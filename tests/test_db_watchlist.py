from chainscope import db


class FakeQuery:
    def __init__(self, calls):
        self.calls = calls

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

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

    def order(self, column):
        self.calls.append(("order", column))
        return self

    def limit(self, value):
        self.calls.append(("limit", value))
        return self

    def execute(self):
        self.calls.append(("execute",))
        return type("Response", (), {"data": [{"coin_id": "bitcoin"}]})()


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


def test_get_user_watchlist_can_load_a_deterministic_user_scoped_subset(monkeypatch):
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    assert db.get_user_watchlist("user-a", limit=5) == ["bitcoin"]
    assert supabase.calls == [
        ("select", "coin_id"),
        ("eq", "user_id", "user-a"),
        ("order", "coin_id"),
        ("limit", 5),
        ("execute",),
    ]
