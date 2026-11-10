from chainscope import reconciliation


def test_reconcile_assets_detects_manual_and_wallet_collision():
    manual = [{"name": "Tether USDT", "symbol": "USDT", "value_usd": 1000.0}]
    portfolio = []
    wallet = [{"symbol": "USDT", "balance": 1000.0, "value_usd": 1000.0, "network": "Polygon"}]
    
    rec = reconciliation.reconcile_assets(manual, portfolio, wallet)
    assert rec["has_duplicates"] is True
    assert rec["total_deducted_overlap_usd"] == 1000.0
    assert len(rec["overlaps"]) == 1


def test_classify_transfer_internal_does_not_affect_income_or_expense():
    res = reconciliation.classify_transfer_transaction(
        tx_type="Transfer",
        from_account="BCA Tabungan",
        to_account="Bibit Reksadana",
        amount=5000000.0,
    )
    assert res["is_internal_transfer"] is True
    assert res["counts_as_income"] is False
    assert res["counts_as_expense"] is False
    assert res["impacts_net_worth"] is False
