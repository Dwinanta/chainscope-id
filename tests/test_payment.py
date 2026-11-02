from datetime import datetime, timedelta
from hashlib import sha256

import pytest

from chainscope import db, payment


def test_create_snap_transaction_uses_config_and_returns_redirect_url(monkeypatch):
    captured = {}

    class FakeSnap:
        def __init__(self, **kwargs):
            captured["snap_config"] = kwargs

        def create_transaction(self, parameters):
            captured["parameters"] = parameters
            return {"redirect_url": "https://pay.example/checkout"}

    monkeypatch.setattr(
        payment.st,
        "secrets",
        {"MIDTRANS_SERVER_KEY": "sandbox-key", "MIDTRANS_IS_PRODUCTION": False},
    )
    monkeypatch.setattr(payment.midtransclient, "Snap", FakeSnap)

    url = payment.create_snap_transaction("user-123", "user@example.com", 50000)

    assert url == "https://pay.example/checkout"
    assert captured["snap_config"] == {
        "server_key": "sandbox-key",
        "is_production": False,
    }
    transaction = captured["parameters"]
    assert transaction["transaction_details"]["gross_amount"] == 50000
    assert transaction["transaction_details"]["order_id"].startswith(
        f"cs-{sha256(b'user-123').hexdigest()[:8]}-"
    )
    assert transaction["customer_details"] == {"email": "user@example.com"}


def test_create_snap_transaction_requires_explicit_mode(monkeypatch):
    monkeypatch.setattr(payment.st, "secrets", {"MIDTRANS_SERVER_KEY": "sandbox-key"})

    with pytest.raises(ValueError, match="MIDTRANS_IS_PRODUCTION"):
        payment.create_snap_transaction("user-123", "user@example.com", 50000)


def test_create_snap_transaction_rejects_nonpositive_amount(monkeypatch):
    monkeypatch.setattr(
        payment.st,
        "secrets",
        {"MIDTRANS_SERVER_KEY": "sandbox-key", "MIDTRANS_IS_PRODUCTION": False},
    )

    with pytest.raises(ValueError, match="bilangan bulat positif"):
        payment.create_snap_transaction("user-123", "user@example.com", 0)


def test_create_snap_transaction_uses_provided_order_id(monkeypatch):
    captured = {}

    class FakeSnap:
        def __init__(self, **kwargs):
            pass

        def create_transaction(self, parameters):
            captured["order_id"] = parameters["transaction_details"]["order_id"]
            return {"redirect_url": "https://pay.example/checkout"}

    monkeypatch.setattr(
        payment.st,
        "secrets",
        {"MIDTRANS_SERVER_KEY": "sandbox-key", "MIDTRANS_IS_PRODUCTION": False},
    )
    monkeypatch.setattr(payment.midtransclient, "Snap", FakeSnap)

    payment.create_snap_transaction(
        "user-123", "user@example.com", 50000, order_id="PREMIUM-user-123-123"
    )

    assert captured["order_id"] == "PREMIUM-user-123-123"


@pytest.mark.parametrize("transaction_status", ["settlement", "pending", "expire"])
def test_check_transaction_status_returns_midtrans_status(
    monkeypatch, transaction_status
):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"transaction_status": transaction_status}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr(
        payment.st,
        "secrets",
        {"MIDTRANS_SERVER_KEY": "sandbox-key", "MIDTRANS_IS_PRODUCTION": False},
    )
    monkeypatch.setattr(payment.requests, "get", fake_get)

    status = payment.check_transaction_status("PREMIUM-user-123-123")

    assert status == transaction_status
    assert captured["url"] == (
        "https://api.sandbox.midtrans.com/v2/PREMIUM-user-123-123/status"
    )
    assert captured["kwargs"] == {
        "auth": ("sandbox-key", ""),
        "timeout": 10,
    }


def test_upgrade_to_premium_updates_profile_for_30_days(monkeypatch):
    captured = {}

    class FakeQuery:
        def update(self, values):
            captured["values"] = values
            return self

        def eq(self, column, value):
            captured["filter"] = (column, value)
            return self

        def execute(self):
            return "updated"

    class FakeSupabase:
        def table(self, name):
            captured["table"] = name
            return FakeQuery()

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 1, 23, 45)

    monkeypatch.setattr(db, "datetime", FixedDatetime)
    monkeypatch.setattr(db, "get_supabase", lambda: FakeSupabase())

    result = db.upgrade_to_premium("user-123")

    assert result == "updated"
    assert captured["table"] == "profiles"
    assert captured["filter"] == ("id", "user-123")
    assert captured["values"] == {
        "subscription_tier": "premium",
        "subscription_end": "2026-01-31",
    }
