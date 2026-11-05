"""Modul untuk menghitung portofolio otomatis dari histori Trading Journal."""
import pandas as pd

def calculate_portfolio_from_trades(trades: list[dict]) -> pd.DataFrame:
    """Mengubah daftar transaksi (buy/sell) menjadi ringkasan portofolio.
    
    Menggunakan metode Average Cost Basis dengan operasi vektor pandas yang efisien.
    """
    if not trades:
        return pd.DataFrame()

    # 1. Konversi ke DataFrame
    df = pd.DataFrame(trades)
    
    # 2. Pastikan tipe data benar
    df["amount"] = df["amount"].astype(float)
    df["price_usd"] = df["price_usd"].astype(float)
    if "strategy_tag" not in df.columns:
        df["strategy_tag"] = "Swing"
    else:
        df["strategy_tag"] = df["strategy_tag"].fillna("Swing")
        
    df["cost_usd"] = df["amount"] * df["price_usd"]
    
    # 3. Operasi vektor per koin (tanpa for-loop python)
    buys = df[df["side"] == "buy"]
    sells = df[df["side"] == "sell"]
    
    if buys.empty:
        return pd.DataFrame()

    buy_agg = buys.groupby("symbol").agg(
        coin_id=("coin_id", "first"),
        total_bought_amount=("amount", "sum"),
        total_bought_cost=("cost_usd", "sum"),
        strategy_tag=("strategy_tag", "last"),
    )
    
    sell_agg = sells.groupby("symbol")["amount"].sum().rename("total_sold_amount")
    
    merged = buy_agg.join(sell_agg, how="left")
    merged["total_sold_amount"] = merged["total_sold_amount"].fillna(0.0)
    merged["amount"] = merged["total_bought_amount"] - merged["total_sold_amount"]
    
    # Filter koin yang masih dimiliki (holding > 0)
    active = merged[merged["amount"] > 1e-8].copy()
    if active.empty:
        return pd.DataFrame()
        
    active["avg_buy_price_usd"] = active["total_bought_cost"] / active["total_bought_amount"]
    active["total_invested_usd"] = active["amount"] * active["avg_buy_price_usd"]
    
    result = active.reset_index()[["symbol", "coin_id", "amount", "avg_buy_price_usd", "total_invested_usd", "strategy_tag"]]
    return result
