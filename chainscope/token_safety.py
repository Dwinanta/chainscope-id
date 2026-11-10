"""Automated on-chain token security, honeypot risk analysis, and contract safety audit."""


def audit_token_safety(
    token_address: str,
    network: str = "Ethereum",
    liquidity_usd: float = 100000.0,
    volume_24h_usd: float = 50000.0,
    buy_tax_pct: float = 0.0,
    sell_tax_pct: float = 0.0,
    is_verified: bool = True,
    has_mint_function: bool = False,
    is_honeypot: bool = False,
) -> dict:
    """Analyze contract parameters and heuristic risk factors to produce a security score."""
    risk_flags = []
    safety_score = 100  # Start at 100, deduct for risks

    # 1. Verification Check
    if not is_verified:
        safety_score -= 35
        risk_flags.append("Smart contract belum terverifikasi di block explorer.")

    # 2. Honeypot Check
    if is_honeypot:
        safety_score = 0
        risk_flags.append("BAHAYA: Terdeteksi honeypot! Token tidak dapat dijual.")

    # 3. Liquidity Risk
    if liquidity_usd < 10000.0:
        safety_score -= 30
        risk_flags.append(f"Likuiditas sangat tipis (${liquidity_usd:,.2f}), rentan terhadap slippage ekstrem dan rug pull.")
    elif liquidity_usd < 50000.0:
        safety_score -= 10
        risk_flags.append(f"Likuiditas sedang (${liquidity_usd:,.2f}).")

    # 4. Tax / Fee Analysis
    if sell_tax_pct > 10.0:
        safety_score -= 25
        risk_flags.append(f"Pajak penjualan (sell tax) sangat tinggi ({sell_tax_pct:.1f}%).")
    elif sell_tax_pct > 5.0:
        safety_score -= 10
        risk_flags.append(f"Pajak penjualan moderat ({sell_tax_pct:.1f}%).")

    if buy_tax_pct > 10.0:
        safety_score -= 20
        risk_flags.append(f"Pajak pembelian (buy tax) tinggi ({buy_tax_pct:.1f}%).")

    # 5. Mint Function
    if has_mint_function:
        safety_score -= 15
        risk_flags.append("Fungsi minting terdeteksi aktif: pemilik kontrak dapat mencetak token baru tanpa batas.")

    final_score = max(0, min(100, safety_score))
    
    if final_score >= 80:
        risk_level = "Rendah (Low Risk)"
        badge_color = "#10B981"
    elif final_score >= 50:
        risk_level = "Sedang (Moderate Risk)"
        badge_color = "#F59E0B"
    else:
        risk_level = "Tinggi / Bahaya (High Risk)"
        badge_color = "#F43F5E"

    return {
        "token_address": token_address,
        "network": network,
        "safety_score": final_score,
        "risk_level": risk_level,
        "badge_color": badge_color,
        "risk_flags": risk_flags,
        "is_safe_to_trade": final_score >= 60,
        "disclaimer": (
            "Peringatan: Analisis ini bersifat indikatif berdasarkan parameter on-chain publik. "
            "Skor tinggi tidak menjamin ketiadaan risiko pasar atau kerugian finansial."
        ),
    }
