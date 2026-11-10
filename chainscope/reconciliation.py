"""Portfolio and asset reconciliation engine for strict duplicate prevention."""

import pandas as pd


def reconcile_assets(
    manual_assets: list[dict],
    portfolio_holdings: list[dict],
    connected_wallet_tokens: list[dict],
) -> dict:
    """Analyze overlap between manual entries, trading portfolio, and connected Web3 wallets.
    
    Returns deduplicated records and the total overlap value to prevent double counting in Net Worth.
    """
    detected_overlaps = []
    total_overlap_value_usd = 0.0

    # Build lookup of connected wallet tokens (by symbol and contract/network)
    wallet_assets = {}
    for w in connected_wallet_tokens:
        sym = str(w.get("symbol", "")).upper()
        if sym:
            wallet_assets[sym] = {
                "balance": float(w.get("balance", 0.0)),
                "value_usd": float(w.get("value_usd", 0.0)),
                "network": w.get("network", "EVM"),
            }

    # Check manual assets against wallet assets
    for asset in manual_assets:
        sym = str(asset.get("symbol", "")).upper()
        name = str(asset.get("name", "")).upper()
        val = float(asset.get("value_usd", 0.0))
        
        # Check collision with connected wallet
        if sym in wallet_assets or any(k in name for k in wallet_assets.keys()):
            matched_sym = sym if sym in wallet_assets else next(k for k in wallet_assets.keys() if k in name)
            w_val = wallet_assets[matched_sym]["value_usd"]
            # Overlap is the minimum of manual value and wallet value
            overlap = min(val, w_val)
            if overlap > 0:
                detected_overlaps.append({
                    "asset_name": asset.get("name", sym),
                    "symbol": matched_sym,
                    "source_a": "Manual Asset Register",
                    "source_b": f"Connected Web3 Wallet ({wallet_assets[matched_sym]['network']})",
                    "manual_value_usd": val,
                    "wallet_value_usd": w_val,
                    "deducted_overlap_usd": overlap,
                    "reason": "Token terdeteksi ganda di aset manual dan wallet Web3.",
                })
                total_overlap_value_usd += overlap

    # Check journal portfolio against connected wallet
    for h in portfolio_holdings:
        sym = str(h.get("symbol", "")).upper()
        val = float(h.get("current_value_usd", 0.0))
        if sym in wallet_assets:
            w_val = wallet_assets[sym]["value_usd"]
            overlap = min(val, w_val)
            if overlap > 0:
                detected_overlaps.append({
                    "asset_name": h.get("coin_id", sym),
                    "symbol": sym,
                    "source_a": "Trading Journal Portfolio",
                    "source_b": f"Connected Web3 Wallet ({wallet_assets[sym]['network']})",
                    "portfolio_value_usd": val,
                    "wallet_value_usd": w_val,
                    "deducted_overlap_usd": overlap,
                    "reason": "Posisi jurnal terdeteksi sama dengan saldo wallet on-chain.",
                })
                total_overlap_value_usd += overlap

    return {
        "has_duplicates": len(detected_overlaps) > 0,
        "duplicate_count": len(detected_overlaps),
        "total_deducted_overlap_usd": round(total_overlap_value_usd, 2),
        "overlaps": detected_overlaps,
    }


def classify_transfer_transaction(
    tx_type: str,
    from_account: str,
    to_account: str,
    amount: float,
) -> dict:
    """Ensure internal transfers between personal accounts/wallets are not counted as income or expenses."""
    is_internal = bool(from_account and to_account and from_account.strip().lower() != to_account.strip().lower())
    
    if is_internal and tx_type.lower() in {"transfer", "internal", "pindah dana"}:
        return {
            "is_internal_transfer": True,
            "counts_as_income": False,
            "counts_as_expense": False,
            "impacts_net_worth": False,
            "note": "Transfer internal antar akun Anda. Tidak mempengaruhi laba rugi atau total kekayaan bersih.",
        }
        
    return {
        "is_internal_transfer": False,
        "counts_as_income": tx_type.lower() == "income" or tx_type.lower() == "pemasukan",
        "counts_as_expense": tx_type.lower() == "expense" or tx_type.lower() == "pengeluaran",
        "impacts_net_worth": True,
        "note": "Transaksi eksternal.",
    }
