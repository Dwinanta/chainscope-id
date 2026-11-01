from datetime import date, timedelta
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

    monkeypatch.setattr(db, "get_supabase", lambda: FakeSupabase())

    result = db.upgrade_to_premium("user-123")

    assert result == "updated"
    assert captured["table"] == "profiles"
    assert captured["filter"] == ("id", "user-123")
    assert captured["values"] == {
        "subscription_tier": "premium",
        "subscription_end": (date.today() + timedelta(days=30)).isoformat(),
    }
