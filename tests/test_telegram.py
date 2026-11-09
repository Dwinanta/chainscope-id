import pytest
import requests

from chainscope import telegram


class FakeResponse:
    def __init__(self, payload, error=None):
        self.payload = payload
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


def test_send_message_uses_plain_text_and_requires_api_confirmation(monkeypatch):
    sent = {}

    def fake_post(url, **kwargs):
        sent.update(url=url, **kwargs)
        return FakeResponse({"ok": True})

    monkeypatch.setattr(telegram.requests, "post", fake_post)

    assert telegram.send_message("token", "chat", "<plain text>")
    assert sent["json"]["text"] == "<plain text>"
    assert "parse_mode" not in sent["json"]


def test_send_message_surfaces_transport_and_telegram_failures(monkeypatch):
    monkeypatch.setattr(
        telegram.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(requests.Timeout()),
    )
    with pytest.raises(telegram.TelegramAPIError, match="Could not reach"):
        telegram.send_message("token", "chat", "message")

    monkeypatch.setattr(
        telegram.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"ok": False}),
    )
    with pytest.raises(telegram.TelegramAPIError, match="did not confirm"):
        telegram.send_message("token", "chat", "message")


def test_send_message_validates_required_arguments():
    with pytest.raises(ValueError, match="token"):
        telegram.send_message("", "chat", "message")
    with pytest.raises(ValueError, match="chat ID"):
        telegram.send_message("token", "", "message")
    with pytest.raises(ValueError, match="cannot be empty"):
        telegram.send_message("token", "chat", "")
