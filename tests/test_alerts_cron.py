from scripts import check_alerts_cron


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class FakeNoContentResponse(FakeResponse):
    def json(self):
        raise ValueError("204 response has no body")


class FakeSession:
    def __init__(self, telegram_ok=True):
        self.telegram_ok = telegram_ok
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        if url.endswith("/rest/v1/alerts"):
            return FakeResponse([{
                "id": "alert-1",
                "user_id": "user-1",
                "coin_id": "bitcoin",
                "symbol": "BTC",
                "condition": "above",
                "target_price": 100,
                "currency": "USD",
                "note": "<unsafe>",
            }])
        if url.endswith("/simple/price"):
            return FakeResponse({"bitcoin": {"usd": 101}})
        if url.endswith("/rest/v1/profiles"):
            return FakeResponse([{"telegram_chat_id": "chat-1"}])
        raise AssertionError(f"Unexpected GET {url}")

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs))
        return FakeResponse({"ok": self.telegram_ok})

    def patch(self, url, **kwargs):
        self.calls.append(("patch", url, kwargs))
        return FakeNoContentResponse(None)


def _environment():
    return {
        "SUPABASE_URL": "https://supabase.example.test/",
        "SUPABASE_KEY": "service-key",
        "TELEGRAM_BOT_TOKEN": "bot-token",
    }


def test_alert_sweep_uses_bearer_auth_plain_text_and_deactivates_on_delivery():
    session = FakeSession()

    assert check_alerts_cron.run_alert_checks(_environment(), session)

    alerts_request = next(
        call for call in session.calls
        if call[0] == "get" and call[1].endswith("/rest/v1/alerts")
    )
    assert alerts_request[2]["headers"]["Authorization"] == "Bearer service-key"
    telegram_request = next(call for call in session.calls if call[0] == "post")
    assert "parse_mode" not in telegram_request[2]["json"]
    assert "<unsafe>" in telegram_request[2]["json"]["text"]
    patch_request = next(call for call in session.calls if call[0] == "patch")
    assert patch_request[2]["params"]["is_active"] == "eq.true"


def test_alert_remains_active_when_telegram_does_not_confirm_delivery():
    session = FakeSession(telegram_ok=False)

    assert not check_alerts_cron.run_alert_checks(_environment(), session)
    assert not any(call[0] == "patch" for call in session.calls)


def test_cron_authorization_uses_supplied_key_as_bearer_token():
    headers = check_alerts_cron.get_supabase_headers("secret")

    assert headers["apikey"] == "secret"
    assert headers["Authorization"] == "Bearer secret"
