"""Modul koneksi database dan query Supabase."""
from datetime import datetime, timedelta

import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    """Inisialisasi Supabase client (di-cache agar tidak reconnect terus)."""
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL atau SUPABASE_KEY belum di-set di secrets.toml")
    return create_client(url, key)

def get_user_profile(user_id: str) -> dict:
    supabase = get_supabase()
    res = (
        supabase.table("profiles")
        .select("role,subscription_tier,subscription_end,telegram_chat_id")
        .eq("id", user_id)
        .execute()
    )
    return res.data[0] if res.data else {}

def upgrade_to_premium(user_id: str):
    """Upgrade a profile to premium for 30 days."""
    subscription_end = (datetime.now() + timedelta(days=30)).date().isoformat()
    return get_supabase().table("profiles").update({
        "subscription_tier": "premium",
        "subscription_end": subscription_end,
    }).eq("id", user_id).execute()

def delete_user(user_id: str) -> bool:
    """Delete a user's app data and, when configured, their Auth account.

    Returns True when the Auth account was deleted. Without a service role
    key, only app data can be removed; the Auth account remains.
    """
    if not user_id:
        raise ValueError("ID pengguna wajib diisi.")

    service_role_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase_url = st.secrets.get("SUPABASE_URL", "")
    if service_role_key:
        if not supabase_url:
            raise ValueError("SUPABASE_URL belum diatur di secrets.toml.")
        supabase = create_client(supabase_url, service_role_key)
    else:
        supabase = get_supabase()

    for table in ("trades", "alerts", "watchlists"):
        supabase.table(table).delete().eq("user_id", user_id).execute()
        if table == "trades":
            _invalidate_user_trades_cache()
    supabase.table("profiles").delete().eq("id", user_id).execute()

    if not service_role_key:
        return False

    supabase.auth.admin.delete_user(user_id)
    return True

def add_trade(user_id: str, coin_id: str, symbol: str, side: str, amount: float, price_usd: float, trade_time: str, source: str = "manual", strategy_tag: str = "Swing"):
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "coin_id": coin_id.lower(),
        "symbol": symbol.upper(),
        "side": side.lower(),
        "amount": amount,
        "price_usd": price_usd,
        "trade_time": trade_time,
        "source": source,
        "strategy_tag": strategy_tag
    }
    result = supabase.table("trades").insert(data).execute()
    _invalidate_user_trades_cache()
    return result

@st.cache_data(ttl=30, max_entries=128, show_spinner=False)
def get_user_trades(user_id: str, limit: int = 100):
    supabase = get_supabase()
    res = (
        supabase.table("trades")
        .select("coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag")
        .eq("user_id", user_id)
        .order("trade_time", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


@st.cache_data(ttl=30, max_entries=128, show_spinner=False)
def get_user_trades_page(
    user_id: str,
    page_size: int = 100,
    offset: int = 0,
) -> tuple[list[dict], bool]:
    """Fetch one user-scoped trade page and indicate whether more rows exist."""
    if page_size <= 0 or offset < 0:
        raise ValueError("Ukuran halaman dan offset transaksi tidak valid.")

    response = (
        get_supabase()
        .table("trades")
        .select("coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag")
        .eq("user_id", user_id)
        .order("trade_time", desc=True)
        .order("id", desc=True)
        .range(offset, offset + page_size)
        .execute()
    )
    rows = response.data
    return rows[:page_size], len(rows) > page_size


@st.cache_data(ttl=30, max_entries=32, show_spinner=False)
def get_all_user_trades(user_id: str, page_size: int = 500) -> list[dict]:
    """Fetch complete user trade history in bounded pages."""
    if page_size <= 0:
        raise ValueError("Ukuran halaman transaksi harus lebih besar dari nol.")

    supabase = get_supabase()
    trades = []
    start = 0
    while True:
        response = (
            supabase.table("trades")
            .select("id,coin_id,symbol,side,amount,price_usd,trade_time,strategy_tag")
            .eq("user_id", user_id)
            .order("trade_time", desc=True)
            .order("id", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )
        page = response.data
        trades.extend(page)
        if len(page) < page_size:
            return trades
        start += page_size


def add_trades(user_id: str, trades: list[dict]) -> None:
    """Insert a batch of normalized trades with one database request."""
    if not trades:
        return

    rows = [
        {
            "user_id": user_id,
            "coin_id": str(trade["coin_id"]).lower(),
            "symbol": str(trade["symbol"]).upper(),
            "side": str(trade["side"]).lower(),
            "amount": trade["amount"],
            "price_usd": trade["price_usd"],
            "trade_time": trade["trade_time"],
            "source": trade.get("source", "csv"),
            "strategy_tag": trade.get("strategy_tag", "Swing"),
        }
        for trade in trades
    ]
    get_supabase().table("trades").insert(rows).execute()
    _invalidate_user_trades_cache()


def _invalidate_user_trades_cache() -> None:
    get_user_trades.clear()
    get_user_trades_page.clear()
    get_all_user_trades.clear()

def get_all_users_dev():
    """Hanya untuk role 'dev'."""
    supabase = get_supabase()
    res = supabase.table("profiles").select("*").execute()
    return res.data

def delete_trade(trade_id: str):
    supabase = get_supabase()
    result = supabase.table("trades").delete().eq("id", trade_id).execute()
    _invalidate_user_trades_cache()
    return result

def delete_all_user_trades(user_id: str):
    """Menghapus seluruh riwayat transaksi milik user tertentu."""
    supabase = get_supabase()
    result = supabase.table("trades").delete().eq("user_id", user_id).execute()
    _invalidate_user_trades_cache()
    return result

# ==========================================
# FUNGSI UNTUK PRICE ALERTS
# ==========================================

def add_alert(user_id: str, coin_id: str, symbol: str, condition: str, target_price: float, currency: str, note: str = ""):
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "coin_id": coin_id.lower(),
        "symbol": symbol.upper(),
        "condition": condition,
        "target_price": target_price,
        "currency": currency.upper(),
        "note": note
    }
    return supabase.table("alerts").insert(data).execute()

def count_user_alerts(user_id: str) -> int:
    """Return the number of active alerts belonging to a user."""
    response = (
        get_supabase()
        .table("alerts")
        .select("id")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )
    return len(response.data)

def get_user_alerts(user_id: str):
    supabase = get_supabase()
    res = (
        supabase.table("alerts")
        .select("coin_id,symbol,condition,target_price,currency,is_active,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data

def delete_alert(alert_id: str):
    supabase = get_supabase()
    return supabase.table("alerts").delete().eq("id", alert_id).execute()

def mark_alert_triggered(alert_id: str):
    supabase = get_supabase()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    return supabase.table("alerts").update({"is_active": False, "triggered_at": now}).eq("id", alert_id).execute()

def update_telegram_chat_id(user_id: str, chat_id: str | None):
    supabase = get_supabase()
    return supabase.table("profiles").update({"telegram_chat_id": chat_id}).eq("id", user_id).execute()

def get_all_active_alerts():
    """Mengambil SEMUA alert aktif dari semua user (untuk cron job)."""
    supabase = get_supabase()
    res = supabase.table("alerts").select("*").eq("is_active", True).execute()
    return res.data
# ==========================================
# FUNGSI UNTUK WATCHLIST (SUPABASE)
# ==========================================

def get_user_watchlist(user_id: str, limit: int | None = None) -> list[str]:
    if limit is not None and limit <= 0:
        raise ValueError("Batas watchlist harus lebih besar dari nol.")
    query = (
        get_supabase()
        .table("watchlists")
        .select("coin_id")
        .eq("user_id", user_id)
    )
    if limit is not None:
        query = query.order("coin_id").limit(limit)
    res = query.execute()
    return [row["coin_id"] for row in res.data]


def sync_user_watchlist(user_id: str, current_ids: list[str], desired_ids: list[str]) -> None:
    """Apply only the user's watchlist additions and removals."""
    current = set(current_ids)
    desired = set(desired_ids)
    removed = sorted(current - desired)
    added = sorted(desired - current)
    supabase = get_supabase()

    if removed:
        (
            supabase.table("watchlists")
            .delete()
            .eq("user_id", user_id)
            .in_("coin_id", removed)
            .execute()
        )
    if added:
        supabase.table("watchlists").upsert(
            [{"user_id": user_id, "coin_id": coin_id} for coin_id in added]
        ).execute()


def add_to_watchlist(user_id: str, coin_id: str):
    supabase = get_supabase()
    try:
        supabase.table("watchlists").upsert({
            "user_id": user_id, 
            "coin_id": coin_id
        }).execute()
    except Exception as e:
        print(f"Error add watchlist: {e}")

def remove_from_watchlist(user_id: str, coin_id: str):
    supabase = get_supabase()
    return supabase.table("watchlists").delete().eq("user_id", user_id).eq("coin_id", coin_id).execute()

def clear_user_watchlist(user_id: str):
    supabase = get_supabase()
    return supabase.table("watchlists").delete().eq("user_id", user_id).execute()