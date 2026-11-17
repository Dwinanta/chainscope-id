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


def test_login_user_does_not_expose_tokens_in_query_params(monkeypatch):
    class FakeSession:
        access_token = "secret-access-token"
        refresh_token = "secret-refresh-token"

    class FakeAuth:
        def sign_in_with_password(self, credentials):
            return type("Res", (), {"user": {"id": "u1"}, "session": FakeSession()})()

    fake_supabase = type("FakeSupabase", (), {"auth": FakeAuth()})()
    monkeypatch.setattr(auth.db, "get_supabase", lambda: fake_supabase)
    auth.st.session_state.clear()
    auth.st.query_params.clear()

    success, msg = auth.login_user("test@example.com", "pass123")

    assert success is True
    assert "access_token" not in auth.st.query_params
    assert "refresh_token" not in auth.st.query_params
    assert auth.st.session_state.user == {"id": "u1"}


def test_check_session_clears_tokens_from_query_params(monkeypatch):
    class FakeSession:
        user = {"id": "u2"}
        session = "active-session"

    class FakeAuth:
        def set_session(self, access, refresh):
            return FakeSession()

    fake_supabase = type("FakeSupabase", (), {"auth": FakeAuth()})()
    monkeypatch.setattr(auth.db, "get_supabase", lambda: fake_supabase)
    auth.st.session_state.clear()
    auth.st.query_params["access_token"] = "raw-access"
    auth.st.query_params["refresh_token"] = "raw-refresh"

    auth.check_session()

    assert auth.st.session_state.user == {"id": "u2"}
    assert "access_token" not in auth.st.query_params
    assert "refresh_token" not in auth.st.query_params


def test_normalize_supabase_url_cleans_quotes_spaces_and_duplicate_scheme():
    from chainscope import db

    assert (
        db.normalize_supabase_url('  "https://tllnodujibcrkffmtseb.supabase.co/" \n')
        == "https://tllnodujibcrkffmtseb.supabase.co"
    )
    assert (
        db.normalize_supabase_url("https://https://tllnodujibcrkffmtseb.supabase.co")
        == "https://tllnodujibcrkffmtseb.supabase.co"
    )
    assert (
        db.normalize_supabase_url("tllnodujibcrkffmtseb.supabase.co")
        == "https://tllnodujibcrkffmtseb.supabase.co"
    )


def test_normalize_supabase_url_rejects_mismatched_jwt_project_ref():
    import base64
    import json
    import pytest
    from chainscope import db

    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(
            json.dumps({"iss": "supabase", "ref": "tllnodujibcrkffmtseb", "role": "anon"}).encode()
        )
        .decode()
        .rstrip("=")
    )
    fake_jwt = f"{header}.{payload}.sig"

    with pytest.raises(db.SupabaseConfigError, match="tidak sesuai dengan project"):
        db.normalize_supabase_url("https://wrongprojectref123.supabase.co", fake_jwt)


def test_register_user_distinguishes_dns_config_and_auth_errors(monkeypatch):
    import socket
    from chainscope import db

    # 1. DNS error ([Errno -2] Name or service not known)
    class DNSFailingAuth:
        def sign_up(self, credentials):
            raise socket.gaierror(-2, "Name or service not known")

    monkeypatch.setattr(
        auth.db, "get_supabase", lambda: type("S", (), {"auth": DNSFailingAuth()})()
    )
    monkeypatch.setattr(
        auth.db, "get_configured_supabase_host", lambda: "typo-host.supabase.co"
    )
    ok_dns, msg_dns = auth.register_user("user@example.com", "password123")
    assert ok_dns is False
    assert "DNS Error" in msg_dns
    assert "typo-host.supabase.co" in msg_dns
    assert "Name or service not known" in msg_dns

    # 2. Config error
    def raise_config_error():
        raise db.SupabaseConfigError("SUPABASE_URL belum diatur")

    monkeypatch.setattr(auth.db, "get_supabase", raise_config_error)
    ok_cfg, msg_cfg = auth.register_user("user@example.com", "password123")
    assert ok_cfg is False
    assert "Konfigurasi Supabase bermasalah" in msg_cfg

    # 3. Normal registration success
    captured = {}

    class ValidAuth:
        def sign_up(self, credentials):
            captured.update(credentials)
            return type("Res", (), {"user": {"id": "u3"}})()

    monkeypatch.setattr(
        auth.db, "get_supabase", lambda: type("S", (), {"auth": ValidAuth()})()
    )
    ok_reg, msg_reg = auth.register_user("  user@example.com  ", "password123")
    assert ok_reg is True
    assert captured["email"] == "user@example.com"
    assert "Registrasi berhasil" in msg_reg


def test_logout_user_clears_session_state_and_query_params(monkeypatch):
    signed_out = []

    class FakeAuth:
        def sign_out(self):
            signed_out.append(True)

    monkeypatch.setattr(
        auth.db, "get_supabase", lambda: type("S", (), {"auth": FakeAuth()})()
    )
    monkeypatch.setattr(auth.st, "rerun", lambda: None)
    auth.st.session_state.user = {"id": "u1"}
    auth.st.session_state.session = "sess-1"
    auth.st.query_params["access_token"] = "tok"

    auth.logout_user()

    assert signed_out == [True]
    assert auth.st.session_state.user is None
    assert auth.st.session_state.session is None
    assert "access_token" not in auth.st.query_params
