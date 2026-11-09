from chainscope import db


class FakeQuery:
    def __init__(self):
        self.selected = None
        self.filters = []
        self.update_values = None

    def select(self, columns):
        self.selected = columns
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def update(self, values):
        self.update_values = values
        return self

    def execute(self):
        return type("Response", (), {"data": [{
            "role": "user",
            "subscription_tier": "free",
            "subscription_end": None,
            "telegram_chat_id": None,
        }]})()


class FakeSupabase:
    def __init__(self):
        self.query = FakeQuery()

    def table(self, name):
        assert name == "profiles"
        return self.query


def test_get_user_profile_selects_only_page_required_fields(monkeypatch):
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    profile = db.get_user_profile("user-a")

    assert profile["role"] == "user"
    assert supabase.query.selected == (
        "role,subscription_tier,subscription_end,telegram_chat_id"
    )
    assert supabase.query.filters == [("id", "user-a")]


def test_update_telegram_chat_id_is_scoped_to_the_current_profile(monkeypatch):
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    db.update_telegram_chat_id("user-a", "-10012345")

    assert supabase.query.update_values == {"telegram_chat_id": "-10012345"}
    assert supabase.query.filters == [("id", "user-a")]
