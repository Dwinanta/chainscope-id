"""Script Cron Job untuk mengecek alert di Supabase dan kirim ke Telegram."""
import os
import requests
from datetime import datetime, timezone

# Ambil kredensial dari Environment Variables GitHub Actions
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
COINGECKO_KEY = os.environ.get("COINGECKO_API_KEY", "")

def get_supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

def main():
    if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_TOKEN]):
        print("Error: Kredensial environment tidak lengkap.")
        return

    headers = get_supabase_headers()

    # 1. Ambil semua alert aktif
    res_alerts = requests.get(f"{SUPABASE_URL}/rest/v1/alerts?is_active=eq.true", headers=headers)
    alerts = res_alerts.json()
    
    if not alerts:
        print("Tidak ada alert aktif.")
        return

    # 2. Kumpulkan koin unik yang perlu dicek harganya
    coins = list(set([a["coin_id"] for a in alerts]))
    coins_str = ",".join(coins)

    # 3. Ambil harga dari CoinGecko (Simple Price API)
    cg_headers = {"x-cg-demo-api-key": COINGECKO_KEY} if COINGECKO_KEY else {}
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coins_str}&vs_currencies=usd,idr"
    
    price_res = requests.get(url, headers=cg_headers)
    prices = price_res.json()

    # 4. Cek setiap alert
    for a in alerts:
        coin_prices = prices.get(a["coin_id"], {})
        current_price = coin_prices.get(a["currency"].lower())
        
        if current_price is None:
            continue

        # Logika pengecekan
        is_hit = (
            (a["condition"] == "above" and current_price >= float(a["target_price"])) or
            (a["condition"] == "below" and current_price <= float(a["target_price"]))
        )

        if is_hit:
            # Dapatkan Chat ID user
            user_res = requests.get(f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{a['user_id']}&select=telegram_chat_id", headers=headers)
            user_data = user_res.json()
            chat_id = user_data[0].get("telegram_chat_id") if user_data else None

            if chat_id:
                # Kirim Telegram
                msg = (
                    f"🚨 <b>ALERT TRIGGERED!</b> 🚨\n\n"
                    f"<b>{a['symbol']}</b> telah menyentuh <b>{current_price:,.2f} {a['currency']}</b>\n"
                    f"Target: {a['condition'].upper()} {float(a['target_price']):,.2f} {a['currency']}\n"
                )
                if a.get("note"):
                    msg += f"📝 Catatan: {a['note']}\n"
                
                tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                requests.post(tg_url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
                print(f"Terkirim alert untuk {a['symbol']} ke chat {chat_id}")

            # Matikan alert agar tidak spam
            now = datetime.now(timezone.utc).isoformat()
            requests.patch(f"{SUPABASE_URL}/rest/v1/alerts?id=eq.{a['id']}", headers=headers, json={"is_active": False, "triggered_at": now})

if __name__ == "__main__":
    main()