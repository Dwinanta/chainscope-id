"""Decentralized swap quote aggregator, route simulator, and testnet transaction manager."""

from datetime import datetime, timezone
import hashlib


SWAP_ROUTERS = {
    "1": {"dex": "Uniswap V3", "router": "0xE592427A0AEce92De3Edee1F18E0157C05861564", "fee_tier": "0.3%"},
    "11155111": {"dex": "Uniswap V3 (Sepolia)", "router": "0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E", "fee_tier": "0.3%"},
    "56": {"dex": "PancakeSwap V3", "router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4", "fee_tier": "0.25%"},
    "137": {"dex": "QuickSwap / Uniswap V3", "router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", "fee_tier": "0.3%"},
    "42161": {"dex": "Uniswap V3 Arbitrum", "router": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45", "fee_tier": "0.05%"},
    "8453": {"dex": "Aerodrome / Uniswap Base", "router": "0x2626664c2603336E57B271c5C0b26F421741e481", "fee_tier": "0.3%"},
    "solana": {"dex": "Jupiter Aggregator / Raydium", "router": "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4", "fee_tier": "Dynamic"},
}


def get_swap_quote(
    chain_id: str | int,
    input_token: str,
    output_token: str,
    amount_in: float,
    slippage_pct: float = 0.5,
    token_in_price_usd: float = 3000.0,
    token_out_price_usd: float = 1.0,
) -> dict:
    """Calculate decentralized swap quote, price impact, minimum received, and estimated gas fee."""
    if amount_in <= 0:
        raise ValueError("Jumlah token masuk harus lebih besar dari 0.")
    if slippage_pct < 0.01 or slippage_pct > 50.0:
        raise ValueError("Toleransi slippage harus antara 0.01% hingga 50%.")

    net_key = str(chain_id)
    router_info = SWAP_ROUTERS.get(net_key, SWAP_ROUTERS["1"])
    
    # Calculate exchange rate based on relative USD valuation
    total_val_usd = amount_in * token_in_price_usd
    expected_amount_out = (total_val_usd / token_out_price_usd) if token_out_price_usd > 0 else 0.0
    
    # Price impact simulation based on trade size
    price_impact_pct = min(15.0, (total_val_usd / 5000000.0) * 100.0)
    actual_amount_out = expected_amount_out * (1.0 - (price_impact_pct / 100.0))
    
    # Minimum received after slippage
    min_received = actual_amount_out * (1.0 - (slippage_pct / 100.0))
    
    # Gas estimation (EVM ~150k gas, L2 ~40k gas, Solana negligible)
    gas_usd = 0.05 if net_key in {"42161", "8453", "137"} else 0.001 if net_key == "solana" else 4.50
    
    return {
        "chain_id": net_key,
        "dex_name": router_info["dex"],
        "router_contract": router_info["router"],
        "input_token": input_token.upper(),
        "output_token": output_token.upper(),
        "amount_in": amount_in,
        "expected_amount_out": round(actual_amount_out, 6),
        "minimum_received": round(min_received, 6),
        "slippage_pct": slippage_pct,
        "price_impact_pct": round(price_impact_pct, 3),
        "estimated_gas_usd": gas_usd,
        "route": f"{input_token.upper()} → {router_info['dex']} Pool ({router_info['fee_tier']}) → {output_token.upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_testnet_swap_payload(quote: dict, sender_address: str) -> dict:
    """Generate un-signed transaction payload for user wallet approval on testnets/simulators.
    
    Never signs private keys! Signing must occur on the user's browser wallet extension.
    """
    raw_seed = f"{quote['chain_id']}_{sender_address}_{quote['amount_in']}_{datetime.now(timezone.utc).timestamp()}"
    simulated_hash = "0x" + hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()
    
    return {
        "to": quote["router_contract"],
        "from": sender_address,
        "value": hex(int(quote["amount_in"] * 1e18)) if quote["input_token"] in {"ETH", "BNB", "POL"} else "0x0",
        "gasLimit": hex(250000),
        "simulated_tx_hash": simulated_hash,
        "network": quote["chain_id"],
        "disclaimer": "Transaksi non-custodial: verifikasi parameter transaksi di wallet Anda sebelum konfirmasi.",
    }
