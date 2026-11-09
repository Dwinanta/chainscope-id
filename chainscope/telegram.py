"""Telegram Bot API helpers with explicit, secret-safe failures."""

import requests

TELEGRAM_API = "https://api.telegram.org"
TIMEOUT = 10


class TelegramAPIError(RuntimeError):
    """Raised when Telegram rejects a request or is unavailable."""


def _request_json(response: requests.Response) -> dict:
    try:
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise TelegramAPIError("Telegram API request failed.") from exc
    except ValueError as exc:
        raise TelegramAPIError("Telegram API returned invalid JSON.") from exc
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise TelegramAPIError("Telegram API did not confirm the request.")
    return payload


def verify_bot(bot_token: str) -> dict:
    if not bot_token or not bot_token.strip():
        raise ValueError("Telegram bot token is required.")
    try:
        response = requests.get(
            f"{TELEGRAM_API}/bot{bot_token.strip()}/getMe",
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise TelegramAPIError("Could not reach Telegram to verify the bot.") from exc
    return _request_json(response)["result"]


def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not bot_token.strip():
        raise ValueError("Telegram bot token is required.")
    if not chat_id or not str(chat_id).strip():
        raise ValueError("Telegram chat ID is required.")
    if not text or not text.strip():
        raise ValueError("Telegram message cannot be empty.")
    try:
        response = requests.post(
            f"{TELEGRAM_API}/bot{bot_token.strip()}/sendMessage",
            json={
                "chat_id": str(chat_id).strip(),
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise TelegramAPIError("Could not reach Telegram to send the message.") from exc
    _request_json(response)
    return True
