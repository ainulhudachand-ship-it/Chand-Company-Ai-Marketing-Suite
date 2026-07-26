"""
pdf_service.py
Stable PDF generator for Chand & Company AI Marketing Suite.
"""

from fpdf import FPDF


class CampaignPDF(FPDF):
    pass


def _safe_text(text):
    """Convert to Latin-1 so built-in Helvetica never crashes."""
    if text is None:
        return ""
    if isinstance(text, list):
        text = ", ".join(str(x) for x in text)
    return str(text).encode("latin-1", errors="ignore").decode("latin-1")


def _write_wrapped(pdf, text, line_height=7):
    """
    Safely writes text without triggering
    'Not enough horizontal space to render a single character'.
    """

    text = _safe_text(text)

    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    if not text.strip():
        pdf.ln(line_height)
        return

    words = text.split()

    line = ""

    for word in words:

        # Break extremely long words/URLs
        if pdf.get_string_width(word) > page_width:

            if line:
                pdf.cell(page_width, line_height, line, ln=True)
                line = ""

            chunk = ""

            for ch in word:

                if pdf.get_string_width(chunk + ch) > page_width:
                    pdf.cell(page_width, line_height, chunk, ln=True)
                    chunk = ch
                else:
                    chunk += ch

            if chunk:
                line = chunk

            continue

        trial = word if not line else line + " " + word

        if pdf.get_string_width(trial) <= page_width:
            line = trial
        else:
            pdf.cell(page_width, line_height, line, ln=True)
            line = word

    if line:
        pdf.cell(page_width, line_height, line, ln=True)


def generate_campaign_pdf(campaign):

    pdf = CampaignPDF()

    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()

    # -----------------------
    # Title
    # -----------------------

    pdf.set_font("Helvetica", "B", 18)

    _write_wrapped(
        pdf,
        campaign.get("product_name", "Campaign"),
        10,
    )

    pdf.ln(2)

    pdf.set_font("Helvetica", "I", 11)

    pdf.set_text_color(100, 100, 100)

    _write_wrapped(
        pdf,
        f"{campaign.get('category','')} | {campaign.get('created_at','')}",
        7,
    )

    pdf.set_text_color(0, 0, 0)

    pdf.ln(4)

    sections = [
        ("Tagline", campaign.get("tagline")),
        ("Description", campaign.get("description")),
        ("Instagram Caption", campaign.get("instagram_caption")),
        ("Facebook Caption", campaign.get("facebook_caption")),
        ("WhatsApp Caption", campaign.get("whatsapp_caption")),
        ("Hashtags", campaign.get("hashtags")),
    ]
    for title, content in sections:

        if not content:
            continue

        pdf.set_font("Helvetica", "B", 12)
        _write_wrapped(pdf, title, 8)

        pdf.set_font("Helvetica", "", 11)
        _write_wrapped(pdf, content, 7)

        pdf.ln(2)

    if campaign.get("image_url"):

        pdf.set_font("Helvetica", "I", 9)

        pdf.set_text_color(120, 120, 120)

        _write_wrapped(
            pdf,
            "Poster image is available inside the Chand & Company AI Marketing Suite.",
            6,
        )

    output = pdf.output()

    if isinstance(output, str):
        return output.encode("latin-1")

    return bytes(output)