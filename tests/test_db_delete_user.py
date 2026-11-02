from chainscope import db


class FakeQuery:
    def __init__(self, calls, table):
        self.calls = calls
        self.table_name = table

    def delete(self):
        self.calls.append((self.table_name, "delete"))
        return self

    def eq(self, column, value):
        self.calls.append((self.table_name, column, value))
        return self

    def execute(self):
        self.calls.append((self.table_name, "execute"))


class FakeSupabase:
    def __init__(self):
        self.calls = []
        self.auth = type("Auth", (), {})()
        self.auth.admin = type("Admin", (), {})()
        self.auth.admin.delete_user = lambda user_id: self.calls.append(
            ("auth.delete_user", user_id)
        )

    def table(self, name):
        return FakeQuery(self.calls, name)


def test_delete_user_uses_service_role_and_deletes_auth_user(monkeypatch):
    fake_supabase = FakeSupabase()
    captured = {}
    monkeypatch.setattr(
        db.st,
        "secrets",
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        },
    )
    monkeypatch.setattr(
        db,
        "create_client",
        lambda url, key: captured.update(url=url, key=key) or fake_supabase,
    )

    result = db.delete_user("user-123")

    assert result is True
    assert captured == {
        "url": "https://example.supabase.co",
        "key": "service-role-key",
    }
    assert fake_supabase.calls[-1] == ("auth.delete_user", "user-123")
    assert ("profiles", "id", "user-123") in fake_supabase.calls


def test_delete_user_falls_back_to_app_data_without_service_role(monkeypatch):
    fake_supabase = FakeSupabase()
    monkeypatch.setattr(
        db.st,
        "secrets",
        {"SUPABASE_URL": "https://example.supabase.co"},
    )
    monkeypatch.setattr(db, "get_supabase", lambda: fake_supabase)

    result = db.delete_user("user-123")

    assert result is False
    assert ("trades", "user_id", "user-123") in fake_supabase.calls
    assert ("alerts", "user_id", "user-123") in fake_supabase.calls
    assert ("watchlists", "user_id", "user-123") in fake_supabase.calls
    assert ("profiles", "id", "user-123") in fake_supabase.calls
    assert not any(call[0] == "auth.delete_user" for call in fake_supabase.calls)
