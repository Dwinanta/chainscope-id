from chainscope import db


TRADE_COLUMNS = "coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag"


class FakeResponse:
    def __init__(self, data=None):
        self.data = data or []


class FakeQuery:
    def __init__(self, calls, table_name):
        self.calls = calls
        self.table_name = table_name
        self.operation = "select"

    def select(self, columns):
        self.calls.append((self.table_name, "select", columns))
        return self

    def insert(self, data):
        self.operation = "insert"
        self.calls.append((self.table_name, "insert", data))
        return self

    def delete(self):
        self.operation = "delete"
        self.calls.append((self.table_name, "delete"))
        return self

    def eq(self, column, value):
        self.calls.append((self.table_name, "eq", column, value))
        return self

    def order(self, column, desc=False):
        self.calls.append((self.table_name, "order", column, desc))
        return self

    def limit(self, value):
        self.calls.append((self.table_name, "limit", value))
        return self

    def execute(self):
        self.calls.append((self.table_name, "execute"))
        return FakeResponse([{"symbol": "BTC"}])


class FakeSupabase:
    def __init__(self):
        self.calls = []

    def table(self, name):
        return FakeQuery(self.calls, name)


def test_get_user_trades_caches_by_user_and_selects_required_columns(monkeypatch):
    db.get_user_trades.clear()
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    assert db.get_user_trades("user-a") == [{"symbol": "BTC"}]
    assert db.get_user_trades("user-a") == [{"symbol": "BTC"}]
    assert db.get_user_trades("user-b") == [{"symbol": "BTC"}]

    selects = [call for call in supabase.calls if call[1] == "select"]
    user_filters = [call for call in supabase.calls if call[1] == "eq"]
    assert selects == [
        ("trades", "select", TRADE_COLUMNS),
        ("trades", "select", TRADE_COLUMNS),
    ]
    assert user_filters == [
        ("trades", "eq", "user_id", "user-a"),
        ("trades", "eq", "user_id", "user-b"),
    ]


def test_successful_trade_insert_invalidates_cached_rows(monkeypatch):
    db.get_user_trades.clear()
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    db.get_user_trades("user-a")
    db.add_trade("user-a", "bitcoin", "btc", "buy", 1, 100, "2026-01-01")
    db.get_user_trades("user-a")

    assert sum(call[1] == "select" for call in supabase.calls) == 2
    assert ("trades", "insert", {
        "user_id": "user-a",
        "coin_id": "bitcoin",
        "symbol": "BTC",
        "side": "buy",
        "amount": 1,
        "price_usd": 100,
        "trade_time": "2026-01-01",
        "source": "manual",
        "strategy_tag": "Swing",
    }) in supabase.calls


def test_successful_trade_deletion_invalidates_cached_rows(monkeypatch):
    db.get_user_trades.clear()
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    db.get_user_trades("user-a")
    db.delete_all_user_trades("user-a")
    db.get_user_trades("user-a")

    assert sum(call[1] == "select" for call in supabase.calls) == 2
    assert ("trades", "eq", "user_id", "user-a") in supabase.calls
