"""
ai_service.py
Chand & Company AI Marketing Suite

Provider order for every AI call:
    1. Groq (primary — fast, generous free tier)
    2. Gemini (automatic fallback if Groq fails for any reason)
    3. Built-in template content (final fallback — app never crashes)

Function names, parameters, and return values are IDENTICAL to the
original version, so app.py does not need any changes.
"""

import streamlit as st
import requests
import json
import os
import time
import urllib.parse
import random

SHOP_NAME = "Chand & Company"

MAX_RETRIES_PER_MODEL = 3
BACKOFF_BASE_SECONDS = 4

# ---------------------------------------------------------
# Groq (primary provider — OpenAI-compatible endpoint)
# ---------------------------------------------------------
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

# ---------------------------------------------------------
# Gemini (fallback provider)
# ---------------------------------------------------------
GEMINI_MODEL_CANDIDATES = [
    "gemini-flash-latest",
    "gemini-2.0-flash",
]


def _get_secret(key):
    """Read a key from st.secrets first, then environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key].strip()
    except Exception:
        pass
    return os.environ.get(key, "").strip()


def _strip_code_fence(text):
    """Remove markdown code fences if the model returns them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
    return text.strip()


def _call_groq(prompt):
    """Returns (text, True) on success, (None, False) if unavailable."""
    api_key = _get_secret("GROQ_API_KEY")
    if not api_key:
        return None, False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for model in GROQ_MODEL_CANDIDATES:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                print(f">>> Groq ({model}, attempt {attempt + 1})...")
                response = requests.post(GROQ_URL, headers=headers, json=body, timeout=30)
                print("STATUS:", response.status_code)

                if response.status_code == 404:
                    break

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_seconds = float(retry_after) if retry_after else BACKOFF_BASE_SECONDS * (2 ** attempt)
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        print(f">>> Groq 429 — waiting {wait_seconds:.0f}s...")
                        time.sleep(wait_seconds)
                        continue
                    break

                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return text.strip(), True

            except Exception as e:
                print("GROQ EXCEPTION:", e)
                break

    return None, False


def _call_gemini(prompt):
    """Returns (text, True) on success, (None, False) if unavailable."""
    api_key = _get_secret("GEMINI_API_KEY")
    if not api_key:
        return None, False

    body = {"contents": [{"parts": [{"text": prompt}]}]}

    for model in GEMINI_MODEL_CANDIDATES:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )

        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                print(f">>> Gemini ({model}, attempt {attempt + 1})...")
                response = requests.post(url, json=body, timeout=30)
                print("STATUS:", response.status_code)

                if response.status_code == 404:
                    break

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_seconds = float(retry_after) if retry_after else BACKOFF_BASE_SECONDS * (2 ** attempt)
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        print(f">>> Gemini 429 — waiting {wait_seconds:.0f}s...")
                        time.sleep(wait_seconds)
                        continue
                    break

                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip(), True

            except Exception as e:
                print("GEMINI EXCEPTION:", e)
                break

    return None, False


def _call_ai(prompt):
    """
    Try Groq first, then Gemini if Groq fails completely.
    Returns (text, True) if either succeeded, (None, False) if both failed.
    """
    text, success = _call_groq(prompt)
    if success:
        return text, True

    print(">>> Groq unavailable, falling back to Gemini...")
    text, success = _call_gemini(prompt)
    if success:
        return text, True

    return None, False


# ---------------------------------------------------------
# Marketing Kit Generator
# ---------------------------------------------------------

def generate_marketing_kit(product_name, category, features, price, occasion):
    """
    Returns:
        (kit_dict, used_fallback: bool)
    Never crashes. If both Groq and Gemini fail, a built-in fallback kit
    is returned and used_fallback=True.
    """

    prompt = f"""
You are a professional Pakistani marketing copywriter.

Business: {SHOP_NAME}

Product Name: {product_name}
Category: {category}
Features: {features}
Price: {price if price else "Not specified"}
Occasion: {occasion if occasion else "General"}

Generate ONLY valid JSON, no extra text before or after it.

{{
"tagline":"",
"description":"",
"instagram_caption":"",
"facebook_caption":"",
"whatsapp_caption":"",
"hashtags":[]
}}
"""

    text, success = _call_ai(prompt)

    if success:
        try:
            text = _strip_code_fence(text)
            kit = json.loads(text)
            return kit, False
        except Exception:
            pass

    # ---------- FALLBACK ----------
    hashtags = [
        category.replace(" ", ""),
        product_name.replace(" ", ""),
        "ChandCompany",
        "Quality",
        "Fresh",
        "Pakistan",
        "BestPrice",
        "Shopping",
        "Sale",
        "Deal",
    ]

    fallback = {
        "tagline": f"Premium {product_name} at the Best Price!",

        "description":
            f"Discover premium quality {product_name} from Chand & Company. "
            f"Fresh quality, competitive prices, and trusted service for every customer.",

        "instagram_caption":
            f"✨ Fresh {product_name} is now available at Chand & Company!\n"
            f"Order today and enjoy premium quality at affordable prices.",

        "facebook_caption":
            f"Looking for quality {product_name}? "
            f"Visit Chand & Company today for trusted products and excellent customer service.",

        "whatsapp_caption":
            f"{product_name} available now! Contact Chand & Company today for orders.",

        "hashtags": hashtags
    }

    return fallback, True


# ---------------------------------------------------------
# Marketing Tip Generator
# ---------------------------------------------------------

def generate_marketing_tip(category=None):
    """
    Returns:
        (tip, used_fallback: bool)
    """

    topic = category if category else "general retail products"

    prompt = (
        f"Give ONE short practical marketing tip (maximum 2 sentences) "
        f"for a small Pakistani retail shop selling {topic}. "
        f"Plain text only. No numbering. No markdown."
    )

    text, success = _call_ai(prompt)

    if success and text:
        return text.strip().strip('"'), False

    fallback_tips = [
        "Post high-quality product photos consistently on Facebook and Instagram.",
        "Always reply to customer messages quickly to build trust.",
        "Use WhatsApp Status daily to promote new arrivals and discounts.",
        "Offer limited-time discounts to encourage faster buying decisions.",
        "Ask satisfied customers to leave reviews and share their experience.",
        "Create short product videos because they usually get more engagement.",
        "Use local hashtags and location tags to reach nearby customers.",
        "Keep your branding and colours consistent across every platform.",
        "Share customer testimonials regularly to increase credibility.",
        "Highlight seasonal offers and bundle deals for better sales."
    ]

    return random.choice(fallback_tips), True


# ---------------------------------------------------------
# AI Poster Generator (unchanged — Pollinations needs no API key)
# ---------------------------------------------------------

def generate_poster_url(product_name, category):
    """
    Generate a realistic commercial poster using Pollinations.
    """

    prompt = f"""
Ultra realistic 8K commercial advertising poster for a retail brand called {SHOP_NAME}.

Main subject: {product_name} ({category}).
The {product_name} must be the clear, in-focus hero of the frame, centered, filling most of the frame.

Style: luxury supermarket advertisement, professional product photography,
dark elegant background, cinematic studio lighting, soft realistic shadows,
premium packaging aesthetic, food/retail magazine quality, ultra HD, hyper realistic.

Strictly exclude: bottles, oil, cosmetics, medicine, people, logos, text, watermarks.
Only the real {product_name}, nothing else in frame.
"""

    encoded = urllib.parse.quote(prompt)
    seed = abs(hash(product_name + category)) % 100000

    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024&nologo=true&enhance=true&seed={seed}"
    )