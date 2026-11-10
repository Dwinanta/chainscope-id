from chainscope import token_safety


def test_audit_token_safety_honeypot_detection():
    audit = token_safety.audit_token_safety(
        token_address="0x1234567890abcdef1234567890abcdef12345678",
        is_honeypot=True,
    )
    assert audit["safety_score"] == 0
    assert audit["is_safe_to_trade"] is False
    assert any("honeypot" in flag.lower() for flag in audit["risk_flags"])


def test_audit_token_safety_verified_high_liquidity():
    audit = token_safety.audit_token_safety(
        token_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        liquidity_usd=5000000.0,
        volume_24h_usd=1000000.0,
        buy_tax_pct=0.0,
        sell_tax_pct=0.0,
        is_verified=True,
        has_mint_function=False,
    )
    assert audit["safety_score"] >= 80
    assert audit["risk_level"] == "Rendah (Low Risk)"
    assert audit["is_safe_to_trade"] is True
