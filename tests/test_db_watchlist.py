from chainscope import db


class FakeQuery:
    def __init__(self, calls):
        self.calls = calls

    def delete(self):
        self.calls.append(("delete",))
        return self

    def upsert(self, rows):
        self.calls.append(("upsert", rows))
        return self

    def eq(self, column, value):
        self.calls.append(("eq", column, value))
        return self

    def in_(self, column, values):
        self.calls.append(("in", column, values))
        return self

    def execute(self):
        self.calls.append(("execute",))


class FakeSupabase:
    def __init__(self):
        self.calls = []
        self.query = FakeQuery(self.calls)

    def table(self, name):
        assert name == "watchlists"
        return self.query


def test_sync_user_watchlist_updates_only_changed_ids(monkeypatch):
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    db.sync_user_watchlist(
        "user-a",
        ["bitcoin", "ethereum"],
        ["ethereum", "solana", "dogecoin"],
    )

    assert supabase.calls == [
        ("delete",),
        ("eq", "user_id", "user-a"),
        ("in", "coin_id", ["bitcoin"]),
        ("execute",),
        ("upsert", [
            {"user_id": "user-a", "coin_id": "dogecoin"},
            {"user_id": "user-a", "coin_id": "solana"},
        ]),
        ("execute",),
    ]


def test_sync_user_watchlist_skips_database_writes_when_unchanged(monkeypatch):
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    db.sync_user_watchlist("user-a", ["bitcoin"], ["bitcoin"])

    assert supabase.calls == []
