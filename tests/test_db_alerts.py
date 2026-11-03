from chainscope import db


class FakeAlertQuery:
    def __init__(self, data):
        self.data = data
        self.filters = []
        self.selected = None

    def select(self, columns):
        self.selected = columns
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def execute(self):
        return type("Response", (), {"data": self.data})()


class FakeSupabase:
    def __init__(self, data):
        self.query = FakeAlertQuery(data)

    def table(self, name):
        assert name == "alerts"
        return self.query


def test_count_user_alerts_counts_only_active_alerts_for_user(monkeypatch):
    supabase = FakeSupabase([{"id": "alert-1"}, {"id": "alert-2"}])
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    assert db.count_user_alerts("user-123") == 2
    assert supabase.query.selected == "id"
    assert supabase.query.filters == [
        ("user_id", "user-123"),
        ("is_active", True),
    ]


def test_count_user_alerts_returns_zero_when_no_active_alerts(monkeypatch):
    monkeypatch.setattr(db, "get_supabase", lambda: FakeSupabase([]))

    assert db.count_user_alerts("user-123") == 0
