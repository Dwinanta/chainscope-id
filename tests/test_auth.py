from chainscope import auth


def test_request_password_reset_sends_email_and_returns_generic_success(monkeypatch):
    captured = {}

    class FakeAuth:
        def reset_password_for_email(self, email):
            captured["email"] = email

    fake_supabase = type("FakeSupabase", (), {"auth": FakeAuth()})()
    monkeypatch.setattr(auth.db, "get_supabase", lambda: fake_supabase)

    success, message = auth.request_password_reset("person@example.com")

    assert captured["email"] == "person@example.com"
    assert success is True
    assert message == (
        "Jika email terdaftar, link reset password telah dikirim. Cek inbox Anda."
    )


def test_request_password_reset_reports_supabase_errors(monkeypatch):
    class FakeAuth:
        def reset_password_for_email(self, email):
            raise RuntimeError("Supabase unavailable")

    fake_supabase = type("FakeSupabase", (), {"auth": FakeAuth()})()
    monkeypatch.setattr(auth.db, "get_supabase", lambda: fake_supabase)

    success, message = auth.request_password_reset("person@example.com")

    assert success is False
    assert message == "Supabase unavailable"
