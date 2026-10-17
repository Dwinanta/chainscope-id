"""Modul koneksi database dan query Supabase."""
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
    res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else {}

def add_trade(user_id: str, coin_id: str, symbol: str, side: str, amount: float, price_usd: float, trade_time: str, source: str = "manual"):
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "coin_id": coin_id.lower(),
        "symbol": symbol.upper(),
        "side": side.lower(),
        "amount": amount,
        "price_usd": price_usd,
        "trade_time": trade_time,
        "source": source
    }
    return supabase.table("trades").insert(data).execute()

def get_user_trades(user_id: str):
    supabase = get_supabase()
    res = supabase.table("trades").select("*").eq("user_id", user_id).order("trade_time", desc=True).execute()
    return res.data

def get_all_users_dev():
    """Hanya untuk role 'dev'."""
    supabase = get_supabase()
    res = supabase.table("profiles").select("*").execute()
    return res.data

def delete_trade(trade_id: str):
    supabase = get_supabase()
    return supabase.table("trades").delete().eq("id", trade_id).execute()

def delete_all_user_trades(user_id: str):
    """Menghapus seluruh riwayat transaksi milik user tertentu."""
    supabase = get_supabase()
    return supabase.table("trades").delete().eq("user_id", user_id).execute()

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

def get_user_alerts(user_id: str):
    supabase = get_supabase()
    res = supabase.table("alerts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data

def delete_alert(alert_id: str):
    supabase = get_supabase()
    return supabase.table("alerts").delete().eq("id", alert_id).execute()

def mark_alert_triggered(alert_id: str):
    supabase = get_supabase()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    return supabase.table("alerts").update({"is_active": False, "triggered_at": now}).eq("id", alert_id).execute()

def update_telegram_chat_id(user_id: str, chat_id: str):
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

def get_user_watchlist(user_id: str) -> list[str]:
    supabase = get_supabase()
    res = supabase.table("watchlists").select("coin_id").eq("user_id", user_id).execute()
    return [row["coin_id"] for row in res.data]

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