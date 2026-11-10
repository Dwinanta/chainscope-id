import pytest
from chainscope import dex_swap


def test_get_swap_quote_calculation():
    quote = dex_swap.get_swap_quote(
        chain_id=1,
        input_token="ETH",
        output_token="USDC",
        amount_in=1.0,
        slippage_pct=0.5,
        token_in_price_usd=3000.0,
        token_out_price_usd=1.0,
    )
    assert quote["dex_name"] == "Uniswap V3"
    assert quote["amount_in"] == 1.0
    assert quote["expected_amount_out"] > 2900.0
    assert quote["minimum_received"] < quote["expected_amount_out"]
    assert quote["slippage_pct"] == 0.5


def test_get_swap_quote_rejects_negative_or_zero_amount():
    with pytest.raises(ValueError, match="harus lebih besar dari 0"):
        dex_swap.get_swap_quote(1, "ETH", "USDC", 0.0)


def test_generate_testnet_swap_payload_structure():
    quote = dex_swap.get_swap_quote(1, "ETH", "USDC", 1.0)
    payload = dex_swap.generate_testnet_swap_payload(quote, "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert "to" in payload
    assert "from" in payload
    assert payload["from"] == "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert "simulated_tx_hash" in payload
