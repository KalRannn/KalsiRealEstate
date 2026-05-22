"""
Backend API Server for Property Assessment Website
===================================================
Wraps scraper.py, serves the frontend, and emails every new lead
to kalsirealestateservices@gmail.com in real time.

Setup:
    pip install flask flask-cors playwright --break-system-packages
    playwright install chromium
    python server.py
"""

import sys
import json
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ── EMAIL CONFIG ─────────────────────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
FROM_EMAIL    = "raloplaysgames@gmail.com"
FROM_PASSWORD = "kgcg wsdy jkff vohl"
TO_EMAIL      = "kalsirealestateservices@gmail.com"
# ─────────────────────────────────────────────────────────────────────────────


def send_lead_email(lead: dict, assessment: dict):
    """Send a lead notification email in a background thread."""
    def _send():
        try:
            name    = lead.get("name", "N/A")
            email   = lead.get("email", "N/A")
            phone   = lead.get("phone", "N/A")
            address = lead.get("address", "N/A")
            time    = datetime.now().strftime("%B %d, %Y at %I:%M %p")

            current_val  = assessment.get("current",  {}).get("value", "N/A") if assessment.get("current")  else "N/A"
            proposed_val = assessment.get("proposed", {}).get("value", "N/A") if assessment.get("proposed") else "N/A"
            prop_address = assessment.get("property_address") or address

            subject = f"🏠 New Lead — {name} | {address}"

            # ── Plain text fallback
            text_body = f"""
New Property Value Lead
========================
Time     : {time}
Name     : {name}
Email    : {email}
Phone    : {phone}
Address  : {address}

Assessment Results
------------------
Property : {prop_address}
2026 Value : {current_val}
2027 Value : {proposed_val}
========================
Sent from your property value tool.
"""

            # ── HTML email
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background: #F0EDE6; margin: 0; padding: 0; }}
  .wrap {{ max-width: 560px; margin: 32px auto; background: #fff; border: 2px solid #111; }}
  .header {{ background: #111; padding: 28px 32px; }}
  .header-logo {{ font-family: monospace; font-size: 14px; font-weight: 700; color: #fff; letter-spacing: 0.02em; }}
  .header-logo em {{ font-style: normal; color: #E63946; }}
  .header-tag {{ font-family: monospace; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-top: 4px; }}
  .red-bar {{ height: 3px; background: #E63946; }}
  .body {{ padding: 32px; }}
  .section-title {{ font-family: monospace; font-size: 9px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #E63946; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
  .row {{ display: flex; border-bottom: 1px solid #E8E4DC; padding: 11px 0; }}
  .row-label {{ font-family: monospace; font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #888; width: 90px; flex-shrink: 0; padding-top: 1px; }}
  .row-value {{ font-size: 14px; color: #111; font-weight: 500; }}
  .assessment {{ background: #111; margin-top: 24px; padding: 24px; position: relative; }}
  .assessment::before {{ content: ''; display: block; height: 2px; background: #E63946; position: absolute; top: 0; left: 0; right: 0; }}
  .assess-label {{ font-family: monospace; font-size: 9px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: rgba(255,255,255,0.25); margin-bottom: 16px; }}
  .assess-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .assess-box {{ background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); padding: 14px; }}
  .assess-year {{ font-family: monospace; font-size: 8px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #E63946; margin-bottom: 6px; }}
  .assess-value {{ font-family: monospace; font-size: 22px; font-weight: 700; color: #fff; letter-spacing: -0.02em; }}
  .assess-addr {{ font-family: monospace; font-size: 11px; color: rgba(255,255,255,0.35); margin-top: 14px; letter-spacing: 0.04em; }}
  .cta {{ margin-top: 28px; background: #E63946; padding: 14px 20px; text-align: center; }}
  .cta a {{ font-family: monospace; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #fff; text-decoration: none; }}
  .footer {{ padding: 16px 32px; background: #F0EDE6; border-top: 1px solid #D4D0C8; }}
  .footer-text {{ font-family: monospace; font-size: 9px; color: #888; letter-spacing: 0.06em; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="header-logo">SHARIYA <em>KALSI</em> — REALTOR®</div>
    <div class="header-tag">New lead from your property value tool</div>
  </div>
  <div class="red-bar"></div>
  <div class="body">
    <div class="section-title">— Contact Details</div>
    <div class="row"><div class="row-label">Name</div><div class="row-value">{name}</div></div>
    <div class="row"><div class="row-label">Email</div><div class="row-value"><a href="mailto:{email}" style="color:#E63946;">{email}</a></div></div>
    <div class="row"><div class="row-label">Phone</div><div class="row-value"><a href="tel:{phone}" style="color:#E63946;">{phone}</a></div></div>
    <div class="row"><div class="row-label">Address</div><div class="row-value">{address}</div></div>
    <div class="row" style="border:none;"><div class="row-label">Time</div><div class="row-value" style="color:#888;font-size:12px;">{time}</div></div>

    <div class="assessment">
      <div class="assess-label">Assessment Results — {prop_address}</div>
      <div class="assess-grid">
        <div class="assess-box">
          <div class="assess-year">2026 Current</div>
          <div class="assess-value">{current_val}</div>
        </div>
        <div class="assess-box">
          <div class="assess-year">2027 Proposed</div>
          <div class="assess-value">{proposed_val}</div>
        </div>
      </div>
      <div class="assess-addr">{prop_address}</div>
    </div>

    <div class="cta">
      <a href="mailto:{email}">Reply to {name} →</a>
    </div>
  </div>
  <div class="footer">
    <div class="footer-text">Sent automatically from your property value tool · Chapter Real Estate · Winnipeg, MB</div>
  </div>
</div>
</body>
</html>
"""

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"Shariya Kalsi Website <{FROM_EMAIL}>"
            msg["To"]      = TO_EMAIL
            msg["Reply-To"] = email  # reply goes straight to the lead

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(FROM_EMAIL, FROM_PASSWORD)
                server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

            print(f"[Email] Lead emailed: {name} — {address}")

        except Exception as e:
            print(f"[Email] Failed to send: {e}")

    threading.Thread(target=_send, daemon=True).start()

# ---------------------------------------------------------------------------
# Inline scraper logic (same as scraper.py, returns dict instead of printing)
# ---------------------------------------------------------------------------
BASE_URL = "https://assessment.winnipeg.ca/AsmtTax/English/Propertydetails/default.stm"


def scrape_assessed_value(address: str) -> dict:
    """Return a dict with keys: property_address, current, proposed, error"""
    from playwright.sync_api import sync_playwright

    parts = address.strip().split(None, 1)
    if len(parts) < 2:
        return {"error": "Provide both a street number and name, e.g. '630 Main'"}

    street_num = parts[0]
    street_name = parts[1].split()[0]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(BASE_URL, wait_until="domcontentloaded")
            page.locator("input[name='StreetNumber']").fill(street_num)
            page.locator("input[name='StreetName']").fill(street_name)

            with page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
                page.locator("input#SubmitAddress").click()

            current_value = None
            proposed_value = None
            property_address = None

            for row in page.locator("tr").all():
                cells = row.locator("td").all()
                if len(cells) == 3:
                    col0 = cells[0].inner_text().strip()
                    col1 = cells[1].inner_text().strip()
                    col2 = cells[2].inner_text().strip()
                    if "$" in col2:
                        parent_text = row.locator("xpath=../..").inner_text()
                        if "2027" in parent_text and proposed_value is None:
                            proposed_value = {"class": col0, "status": col1, "value": col2}
                        elif current_value is None:
                            current_value = {"class": col0, "status": col1, "value": col2}

            addr_row = page.locator("tr").filter(has_text="Roll Number").first
            if addr_row.count():
                property_address = addr_row.inner_text().strip().split("\n")[0]

            browser.close()

            if not current_value and not proposed_value:
                return {"error": "No assessed value found for that address. Please verify the address and try again."}

            return {
                "property_address": property_address,
                "current": current_value,
                "proposed": proposed_value,
                "error": None
            }

    except Exception as e:
        return {"error": f"Scraper error: {str(e)}"}


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder=".")
CORS(app)

# Simple in-memory lead store (replace with a DB in production)
leads = []
leads_lock = threading.Lock()


@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/value")
@app.route("/value.html")
def value_tool():
    return send_from_directory(".", "value.html")


@app.route("/api/assess", methods=["POST"])
def assess():
    data = request.get_json(force=True)
    address = (data.get("address") or "").strip()
    name    = (data.get("name") or "").strip()
    email   = (data.get("email") or "").strip()
    phone   = (data.get("phone") or "").strip()

    if not address:
        return jsonify({"error": "Address is required"}), 400
    if not name or not email or not phone:
        return jsonify({"error": "Name, email, and phone are required"}), 400

    # Save lead locally
    with leads_lock:
        leads.append({"name": name, "email": email, "phone": phone, "address": address})
        try:
            Path("leads.json").write_text(json.dumps(leads, indent=2))
        except Exception:
            pass

    result = scrape_assessed_value(address)

    # Email the lead to Shariya (non-blocking background thread)
    send_lead_email(
        {"name": name, "email": email, "phone": phone, "address": address},
        result
    )

    return jsonify(result)


@app.route("/api/leads", methods=["GET"])
def get_leads():
    """Simple admin endpoint — protect this in production!"""
    with leads_lock:
        return jsonify(leads)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon-32.png')
def favicon32():
    return send_from_directory('.', 'favicon-32.png', mimetype='image/png')

@app.route('/apple-touch-icon.png')
def apple_icon():
    return send_from_directory('.', 'apple-touch-icon.png', mimetype='image/png')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)