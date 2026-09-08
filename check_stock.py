"""Check Amazon.fr product availability and notify via Telegram/email when back in stock."""
import os
import sys

import requests
from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://www.amazon.fr/dp/B0DXQHPY34"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

OUT_OF_STOCK_PATTERNS = [
    "actuellement indisponible",
    "currently unavailable",
    "temporairement en rupture de stock",
    "en rupture de stock",
]

CAPTCHA_MARKERS = [
    "api-services-support@amazon.com",
    "enter the characters you see below",
    "saisissez les caractères que vous voyez dans cette image",
]


def fetch_status(url: str):
    """Loads the product page in a real browser and returns (html, availability_text, has_buy_button).

    A headless browser is required: plain HTTP requests get stuck behind Amazon's bot-check page.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context(locale="fr-FR", user_agent=USER_AGENT)
            page = context.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            html = page.content()
            availability_locator = page.locator("#availability")
            availability_text = (
                availability_locator.inner_text().strip().lower()
                if availability_locator.count()
                else ""
            )
            has_buy_button = page.locator("#buy-now-button, #add-to-cart-button").count() > 0
            return html, availability_text, has_buy_button
        finally:
            browser.close()


def is_in_stock(html: str, availability_text: str, has_buy_button: bool):
    """Returns (in_stock, reason) based on the availability block and buy button presence."""
    if any(marker in html.lower() for marker in CAPTCHA_MARKERS):
        return False, "captcha/blocked"

    if any(pattern in availability_text for pattern in OUT_OF_STOCK_PATTERNS):
        return False, availability_text or "out of stock text found"

    if has_buy_button:
        return True, availability_text or "buy button present"

    return False, availability_text or "no buy button found"


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram not configured, skipping")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=20)


def send_email(subject: str, body: str) -> None:
    import smtplib
    from email.mime.text import MIMEText

    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to_addr = os.environ.get("NOTIFY_EMAIL")
    if not all([host, user, password, to_addr]):
        print("Email not configured, skipping")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    with smtplib.SMTP_SSL(host, 465, timeout=20) as server:
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())


def main() -> None:
    url = os.environ.get("PRODUCT_URL", PRODUCT_URL)
    try:
        html, availability_text, has_buy_button = fetch_status(url)
    except Exception as exc:
        print(f"Fetch failed: {exc}")
        sys.exit(0)  # don't fail the workflow, just skip this run

    in_stock, reason = is_in_stock(html, availability_text, has_buy_button)
    print(f"in_stock={in_stock} reason={reason!r}")

    if in_stock:
        message = f"iPhone 16e jest dostepny! {url}"
        send_telegram(message)
        send_email("iPhone 16e dostepny!", message)


if __name__ == "__main__":
    main()
