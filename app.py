"""
app.py — Chand & Company AI Marketing Suite
Main Streamlit entry point: sidebar navigation + all pages.

Run locally:   streamlit run app.py
Requires:      GEMINI_API_KEY in .streamlit/secrets.toml (see secrets.toml.example)
"""

import streamlit as st
import pandas as pd

import db
import ai_service
import pdf_service

st.set_page_config(page_title="Chand & Co. AI Marketing Suite", page_icon="🛍️", layout="centered")

# ============================================================
# STYLE
# ============================================================

def inject_style():
    st.markdown(
        """
        <style>
        .stApp { background-color: #FBF7EF; }
        h1, h2, h3 { color: #0F5C56 !important; }

        .stButton>button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button {
            background-color: #E8A83C; color: #1a1a1a; border: none;
            border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem;
        }
        .stButton>button:hover, [data-testid="stFormSubmitButton"] button:hover,
        [data-testid="stDownloadButton"] button:hover { background-color: #d4952f; color: #1a1a1a; }

        [data-testid="stForm"] {
            background-color: #FFFFFF; border: 1px solid #E7DFD0;
            border-radius: 14px; padding: 1.2rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important; border-color: #E7DFD0 !important;
        }
        .stTextInput input, .stTextArea textarea {
            border-radius: 8px !important; border: 1.5px solid #E7DFD0 !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus { border-color: #E8A83C !important; }

        section[data-testid="stSidebar"] { background-color: #0F5C56; }
        section[data-testid="stSidebar"] * { color: #FFFFFF !important; }

        .hero-banner {
            background: linear-gradient(135deg, #0F5C56 0%, #0A423D 100%);
            border-radius: 16px; padding: 26px 22px; color: #fff; margin-bottom: 20px;
        }
        .hero-banner h1 { font-size: 24px; color: #fff !important; margin: 0 0 6px 0; }
        .hero-banner p { margin: 0; font-size: 14px; color: rgba(255,255,255,0.85); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle):
    st.markdown(
        f"""<div class="hero-banner"><h1>{title}</h1><p>{subtitle}</p></div>""",
        unsafe_allow_html=True,
    )


db.init_db()
inject_style()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.markdown("## 🛍️ Chand & Co.")
st.sidebar.caption("AI Marketing Suite")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Dashboard", "📦 Products", "✨ Generate Kit", "📜 Campaign History"],
    label_visibility="collapsed",
)

sidebar_stats = db.get_stats()
st.sidebar.divider()
st.sidebar.caption("Quick Snapshot")
sc1, sc2 = st.sidebar.columns(2)
sc1.metric("📦", sidebar_stats["total_products"])
sc2.metric("✨", sidebar_stats["total_campaigns"])

st.sidebar.divider()
st.sidebar.caption("Developed by")
st.sidebar.caption("Masooma Fatima ❤️")

# ============================================================
# PAGE: DASHBOARD
# ============================================================

if page == "🏠 Dashboard":
    hero("🏠 Dashboard", "Chand & Company ka marketing activity, ek nazar mein.")

    stats = sidebar_stats
    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Products", stats["total_products"])
    col2.metric("✨ Campaigns", stats["total_campaigns"])
    col3.metric("🗂️ Categories", len(stats["by_category"]))

    if stats["by_category"]:
        st.subheader("Campaigns by Category")
        chart_df = pd.DataFrame(
            list(stats["by_category"].items()), columns=["Category", "Count"]
        ).set_index("Category")
        st.bar_chart(chart_df)

    with st.container(border=True):
        st.subheader("💡 AI Marketing Tip")
        categories = list(stats["by_category"].keys())
        tip_category = categories[0] if categories else None

        if st.button("💡 Naya Tip Lein", use_container_width=True):
            with st.spinner("🤖 AI aapke liye ek marketing tip soch rahi hai..."):
                tip, error = ai_service.generate_marketing_tip(tip_category)

            if tip:
                st.session_state["current_tip"] = tip
            elif error:
                st.warning(error)

        if "current_tip" in st.session_state:
            st.info(st.session_state["current_tip"], icon="💡")
        else:
            st.caption("Upar button dabayein — AI ek marketing tip degi.")

# ============================================================
# PAGE: PRODUCTS
# ============================================================

elif page == "📦 Products":
    hero("📦 Product Management", "Products save karein — Generate Kit page par dropdown se select ho sakenge.")

    if "editing_product_id" not in st.session_state:
        st.session_state["editing_product_id"] = None

    editing = db.get_product(st.session_state["editing_product_id"]) if st.session_state["editing_product_id"] else None

    with st.form("product_form", clear_on_submit=True):
        st.write("**Edit Product**" if editing else "**Naya Product Add Karein**")
        name = st.text_input("Product name*", value=editing["name"] if editing else "")
        category = st.text_input("Category*", value=editing["category"] if editing else "")
        features = st.text_area("Key features*", value=editing["features"] if editing else "")
        col1, col2 = st.columns(2)
        with col1:
            price = st.text_input("Price (optional)", value=editing["price"] if editing else "")
        with col2:
            occasion = st.text_input("Occasion/audience (optional)", value=editing["occasion"] if editing else "")
        submitted = st.form_submit_button("Update Product" if editing else "Add Product")

        if submitted:
            if not name or not category or not features:
                st.warning("Name, category, aur features zaroor bharein.")
            elif editing:
                db.update_product(editing["id"], name, category, features, price, occasion)
                st.session_state["editing_product_id"] = None
                st.success("Product update ho gaya.")
                st.rerun()
            else:
                db.add_product(name, category, features, price, occasion)
                st.success("Product add ho gaya.")
                st.rerun()

    if editing and st.button("Cancel Edit"):
        st.session_state["editing_product_id"] = None
        st.rerun()

    st.divider()
    st.subheader("Saved Products")
    products = db.get_products()
    if not products:
        st.caption("Abhi tak koi product save nahi hua.")
    else:
        for p in products:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{p['name']}**  \n`{p['category']}` · {p['price'] or 'price N/A'}")
                if c2.button("✏️ Edit", key=f"edit_{p['id']}"):
                    st.session_state["editing_product_id"] = p["id"]
                    st.rerun()
                if c3.button("🗑️ Delete", key=f"del_{p['id']}"):
                    st.session_state[f"confirm_delete_{p['id']}"] = True

                if st.session_state.get(f"confirm_delete_{p['id']}"):
                    st.warning(f"Pakka delete karna hai '{p['name']}'?")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("Haan, Delete Karein", key=f"confirm_{p['id']}"):
                        db.delete_product(p["id"])
                        del st.session_state[f"confirm_delete_{p['id']}"]
                        st.rerun()
                    if cc2.button("Cancel", key=f"cancel_{p['id']}"):
                        del st.session_state[f"confirm_delete_{p['id']}"]
                        st.rerun()

# ============================================================
# PAGE: GENERATE KIT
# ============================================================

elif page == "✨ Generate Kit":
    hero("✨ Generate Marketing Kit", "Tagline, captions, hashtags, aur poster — sab ek click mein.")

    products = db.get_products()
    product_names = ["✍️ Manual entry"] + [p["name"] for p in products]
    choice = st.selectbox("Product source", product_names)
    selected = next((p for p in products if p["name"] == choice), None) if choice != "✍️ Manual entry" else None

    with st.form("kit_form"):
        product_name = st.text_input("Product name*", value=selected["name"] if selected else "")
        category = st.text_input("Category*", value=selected["category"] if selected else "")
        features = st.text_area("Key features*", value=selected["features"] if selected else "")
        col1, col2 = st.columns(2)
        with col1:
            price = st.text_input("Price (optional)", value=selected["price"] if selected else "")
        with col2:
            occasion = st.text_input("Occasion/audience (optional)", value=selected["occasion"] if selected else "")
        submitted = st.form_submit_button("Generate Marketing Kit")

    if submitted:
        if not product_name or not category or not features:
            st.warning("Product name, category, aur features zaroor bharein.")
        else:
            with st.spinner("🤖 AI aapki professional marketing kit taiyaar kar rahi hai — tagline, captions, hashtags..."):
                kit, error = ai_service.generate_marketing_kit(
                    product_name,
                    category,
                    features,
                    price,
                    occasion,
                )

            with st.spinner("🎨 Poster design ho raha hai..."):
                image_url = ai_service.generate_poster_url(product_name, category)

            if kit:
                hashtags_str = " ".join(f"#{h}" for h in kit.get("hashtags", []))
                db.save_campaign(
                    product_name, category, kit.get("tagline", ""), kit.get("description", ""),
                    kit.get("instagram_caption", ""), kit.get("facebook_caption", ""),
                    kit.get("whatsapp_caption", ""), hashtags_str, image_url,
                )
                st.session_state["last_kit"] = {"kit": kit, "hashtags_str": hashtags_str, "image_url": image_url}
            elif error:
                st.warning(error)

    if "last_kit" in st.session_state:
        lk = st.session_state["last_kit"]
        kit = lk["kit"]
        with st.container(border=True):
            st.success("🎉 Marketing Kit Generated Successfully!")
            st.subheader("✨ Tagline")
            st.write(kit.get("tagline", ""))
            st.subheader("📝 Description")
            st.write(kit.get("description", ""))
            st.subheader("📷 Instagram Caption")
            st.text_area("ig", kit.get("instagram_caption", ""), label_visibility="collapsed", disabled=True, key="ig_out")
            st.subheader("👍 Facebook Caption")
            st.text_area("fb", kit.get("facebook_caption", ""), label_visibility="collapsed", disabled=True, key="fb_out")
            st.subheader("💬 WhatsApp Caption")
            st.text_area("wa", kit.get("whatsapp_caption", ""), label_visibility="collapsed", disabled=True, key="wa_out")
            st.subheader("#️⃣ Hashtags")
            st.write(lk["hashtags_str"])
            st.subheader("🖼️ Poster")
            try:
                st.image(lk["image_url"], use_container_width=True)
            except Exception:
                st.info("Poster image abhi load nahi ho saka — baaki kit save ho gayi hai.")

# ============================================================
# PAGE: CAMPAIGN HISTORY
# ============================================================

elif page == "📜 Campaign History":
    hero("📜 Campaign History", "Purani marketing kits dekhein, search karein, ya PDF download karein.")

    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("🔍 Product name se search karein")
    with col2:
        categories = ["Sab (All)"] + db.get_campaign_categories()
        category_filter = st.selectbox("Category", categories)

    campaigns = db.get_campaigns(search_term=search_term, category_filter=category_filter)

    if not campaigns:
        st.caption("Koi campaign nahi mili.")
    else:
        st.caption(f"{len(campaigns)} campaign(s) mili.")
        for c in campaigns:
            with st.container(border=True):
                st.markdown(f"**{c['product_name']}** ({c['category']}) — _{c['created_at']}_")
                st.write(f"Tagline: {c['tagline']}")
                if c.get("whatsapp_caption"):
                    st.write(f"WhatsApp: {c['whatsapp_caption']}")
                if c.get("hashtags"):
                    st.write(c["hashtags"])

                pdf_bytes = pdf_service.generate_campaign_pdf(c)
                st.download_button(
                    "⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name=f"{c['product_name'].replace(' ', '_')}_campaign.pdf",
                    mime="application/pdf",
                    key=f"pdf_{c['id']}",
                )