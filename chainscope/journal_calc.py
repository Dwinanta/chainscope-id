"""Modul untuk menghitung portofolio otomatis dari histori Trading Journal."""
import pandas as pd

def calculate_portfolio_from_trades(trades: list[dict]) -> pd.DataFrame:
    """Mengubah daftar transaksi (buy/sell) menjadi ringkasan portofolio.
    
    Menggunakan metode Average Cost Basis.
    """
    if not trades:
        return pd.DataFrame()

    # 1. Konversi ke DataFrame
    df = pd.DataFrame(trades)
    
    # 2. Pastikan tipe data benar
    df["amount"] = df["amount"].astype(float)
    df["price_usd"] = df["price_usd"].astype(float)
    
    # 3. Hitung total beli dan total jual per koin
    summary = []
    for symbol, group in df.groupby("symbol"):
        buys = group[group["side"] == "buy"]
        sells = group[group["side"] == "sell"]
        
        total_bought_amount = buys["amount"].sum()
        total_bought_cost = (buys["amount"] * buys["price_usd"]).sum()
        total_sold_amount = sells["amount"].sum()
        
        current_holding = total_bought_amount - total_sold_amount
        
        if current_holding <= 0.00000001: # Abaikan jika sudah habis terjual
            continue
            
        # Harga rata-rata beli (Average Cost)
        avg_buy_price = total_bought_cost / total_bought_amount if total_bought_amount > 0 else 0
        
        summary.append({
            "symbol": symbol,
            "coin_id": group["coin_id"].iloc[0],
            "amount": current_holding,
            "avg_buy_price_usd": avg_buy_price,
            "total_invested_usd": current_holding * avg_buy_price
        })
        
    return pd.DataFrame(summary)