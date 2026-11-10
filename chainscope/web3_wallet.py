"""Non-custodial Web3 wallet integration and multi-chain balance intelligence."""

import re
import requests
from chainscope.web3_networks import get_network_by_chain_id


def is_valid_evm_address(address: str) -> bool:
    """Validate 40-hex-character EVM Ethereum address."""
    if not isinstance(address, str):
        return False
    return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", address.strip()))


def is_valid_solana_address(address: str) -> bool:
    """Validate base58 Solana public address."""
    if not isinstance(address, str):
        return False
    # Solana public keys are 32-44 base58 characters
    return bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", address.strip()))


def format_short_address(address: str) -> str:
    """Shorten address for clean UI display (e.g. 0x1234...abcd)."""
    if not address or len(address) < 10:
        return address or ""
    return f"{address[:6]}...{address[-4:]}"


def fetch_native_balance(chain_id: str | int, address: str, timeout: int = 5) -> dict:
    """Fetch native token balance using public JSON-RPC standard endpoints."""
    network = get_network_by_chain_id(chain_id)
    rpc_url = network.get("rpc_url")
    symbol = network.get("symbol", "ETH")
    decimals = network.get("decimals", 18)
    
    if network.get("type") == "solana":
        # Solana JSON-RPC
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address],
        }
        try:
            res = requests.post(rpc_url, json=payload, timeout=timeout)
            if res.status_code == 200:
                lamports = res.json().get("result", {}).get("value", 0)
                balance = float(lamports) / (10 ** decimals)
                return {"balance": balance, "symbol": symbol, "status": "LIVE"}
        except Exception:
            pass
        return {"balance": 0.0, "symbol": symbol, "status": "UNAVAILABLE"}

    # EVM JSON-RPC (eth_getBalance)
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBalance",
        "params": [address, "latest"],
    }
    try:
        res = requests.post(rpc_url, json=payload, timeout=timeout)
        if res.status_code == 200:
            hex_val = res.json().get("result", "0x0")
            wei = int(hex_val, 16)
            balance = float(wei) / (10 ** decimals)
            return {"balance": balance, "symbol": symbol, "status": "LIVE"}
    except Exception:
        pass

    return {"balance": 0.0, "symbol": symbol, "status": "UNAVAILABLE"}


def get_curated_token_balances(chain_id: str | int, address: str) -> list[dict]:
    """Retrieve multi-token asset balances for a connected address across tracked tokens."""
    native = fetch_native_balance(chain_id, address)
    network = get_network_by_chain_id(chain_id)
    
    # Tracked native asset
    tokens = [
        {
            "symbol": native["symbol"],
            "name": f"{network['name']} Native Token",
            "balance": native["balance"],
            "price_usd": 0.0,  # Valued dynamically by market rate
            "is_native": True,
            "network": network["name"],
        }
    ]
    return tokens
