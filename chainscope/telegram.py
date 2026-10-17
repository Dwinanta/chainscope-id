"""Klien minimal untuk Telegram Bot API."""
import requests

TELEGRAM_API = "https://api.telegram.org"
TIMEOUT = 10

def verify_bot(bot_token: str) -> dict | None:
    if not bot_token or not bot_token.strip():
        return None
    try:
        r = requests.get(f"{TELEGRAM_API}/bot{bot_token.strip()}/getMe", timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return data.get("result")
        return None
    except Exception:
        return None

def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not chat_id:
        return False
    try:
        r = requests.post(
            f"{TELEGRAM_API}/bot{bot_token.strip()}/sendMessage",
            json={
                "chat_id": str(chat_id).strip(),
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return bool(r.json().get("ok"))
    except Exception:
        return False