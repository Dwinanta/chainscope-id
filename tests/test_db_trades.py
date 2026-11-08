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

    def range(self, start, end):
        self.calls.append((self.table_name, "range", start, end))
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


def test_get_all_user_trades_pages_and_caches_by_user(monkeypatch):
    db.get_all_user_trades.clear()
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    assert db.get_all_user_trades("user-a", page_size=5) == [{"symbol": "BTC"}]
    assert db.get_all_user_trades("user-a", page_size=5) == [{"symbol": "BTC"}]
    assert db.get_all_user_trades("user-b", page_size=5) == [{"symbol": "BTC"}]

    ranges = [call for call in supabase.calls if call[1] == "range"]
    user_filters = [call for call in supabase.calls if call[1] == "eq"]
    assert ranges == [
        ("trades", "range", 0, 4),
        ("trades", "range", 0, 4),
    ]
    assert user_filters == [
        ("trades", "eq", "user_id", "user-a"),
        ("trades", "eq", "user_id", "user-b"),
    ]


def test_get_all_user_trades_reads_every_page(monkeypatch):
    class PaginatedQuery(FakeQuery):
        def __init__(self, calls, table_name):
            super().__init__(calls, table_name)
            self.start = 0

        def range(self, start, end):
            self.start = start
            self.calls.append((self.table_name, "range", start, end))
            return self

        def execute(self):
            self.calls.append((self.table_name, "execute"))
            rows = [
                {"symbol": "BTC"},
                {"symbol": "ETH"},
            ] if self.start == 0 else [{"symbol": "SOL"}]
            return FakeResponse(rows)

    class PaginatedSupabase(FakeSupabase):
        def table(self, name):
            return PaginatedQuery(self.calls, name)

    db.get_all_user_trades.clear()
    supabase = PaginatedSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    trades = db.get_all_user_trades("user-a", page_size=2)

    assert trades == [
        {"symbol": "BTC"},
        {"symbol": "ETH"},
        {"symbol": "SOL"},
    ]
    assert [call for call in supabase.calls if call[1] == "range"] == [
        ("trades", "range", 0, 1),
        ("trades", "range", 2, 3),
    ]


def test_get_user_trades_page_returns_has_more_and_uses_bounded_range(monkeypatch):
    class PaginatedQuery(FakeQuery):
        def __init__(self, calls, table_name):
            super().__init__(calls, table_name)
            self.page_range = None

        def range(self, start, end):
            self.page_range = (start, end)
            self.calls.append((self.table_name, "range", start, end))
            return self

        def execute(self):
            self.calls.append((self.table_name, "execute"))
            return FakeResponse([
                {"symbol": "BTC"},
                {"symbol": "ETH"},
                {"symbol": "SOL"},
            ])

    class PaginatedSupabase(FakeSupabase):
        def table(self, name):
            return PaginatedQuery(self.calls, name)

    db.get_user_trades_page.clear()
    supabase = PaginatedSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    rows, has_more = db.get_user_trades_page(
        "user-a",
        page_size=2,
        offset=4,
    )

    assert rows == [{"symbol": "BTC"}, {"symbol": "ETH"}]
    assert has_more is True
    assert ("trades", "range", 4, 6) in supabase.calls
    assert ("trades", "eq", "user_id", "user-a") in supabase.calls


def test_add_trades_inserts_batch_and_invalidates_trade_cache(monkeypatch):
    db.get_user_trades.clear()
    db.get_all_user_trades.clear()
    supabase = FakeSupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supabase)

    db.get_user_trades("user-a")
    db.add_trades("user-a", [
        {
            "coin_id": "bitcoin",
            "symbol": "btc",
            "side": "BUY",
            "amount": 1,
            "price_usd": 100,
            "trade_time": "2026-01-01",
        },
        {
            "coin_id": "ethereum",
            "symbol": "eth",
            "side": "sell",
            "amount": 2,
            "price_usd": 50,
            "trade_time": "2026-01-02",
        },
    ])
    db.get_user_trades("user-a")

    inserts = [call for call in supabase.calls if call[1] == "insert"]
    assert len(inserts) == 1
    assert inserts[0][2] == [
        {
            "user_id": "user-a",
            "coin_id": "bitcoin",
            "symbol": "BTC",
            "side": "buy",
            "amount": 1,
            "price_usd": 100,
            "trade_time": "2026-01-01",
            "source": "csv",
            "strategy_tag": "Swing",
        },
        {
            "user_id": "user-a",
            "coin_id": "ethereum",
            "symbol": "ETH",
            "side": "sell",
            "amount": 2,
            "price_usd": 50,
            "trade_time": "2026-01-02",
            "source": "csv",
            "strategy_tag": "Swing",
        },
    ]
    assert sum(call[1] == "select" for call in supabase.calls) == 2
