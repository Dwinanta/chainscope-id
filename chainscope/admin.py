"""Modul untuk manajemen admin (Dev only)."""
from chainscope import db

def get_all_users():
    """Mengambil semua profil user dari database."""
    supabase = db.get_supabase()
    res = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
    return res.data

def update_user_role(user_id: str, new_role: str):
    """Mengubah role user (user / dev)."""
    supabase = db.get_supabase()
    return supabase.table("profiles").update({"role": new_role}).eq("id", user_id).execute()

def update_user_subscription(user_id: str, tier: str, end_date: str = None):
    """Mengubah tier langganan dan tanggal berakhirnya."""
    supabase = db.get_supabase()
    data = {"subscription_tier": tier}
    if end_date:
        data["subscription_end"] = end_date
    return supabase.table("profiles").update(data).eq("id", user_id).execute()