"""Supported blockchain networks, RPC providers, native tokens, and block explorers."""

SUPPORTED_NETWORKS = {
    "1": {
        "name": "Ethereum",
        "chain_id": 1,
        "type": "evm",
        "symbol": "ETH",
        "decimals": 18,
        "rpc_url": "https://eth.llamarpc.com",
        "explorer_url": "https://etherscan.io",
        "gecko_network_id": "eth",
        "is_testnet": False,
    },
    "11155111": {
        "name": "Ethereum Sepolia (Testnet)",
        "chain_id": 11155111,
        "type": "evm",
        "symbol": "SepoliaETH",
        "decimals": 18,
        "rpc_url": "https://rpc.sepolia.org",
        "explorer_url": "https://sepolia.etherscan.io",
        "gecko_network_id": None,
        "is_testnet": True,
    },
    "56": {
        "name": "BNB Smart Chain",
        "chain_id": 56,
        "type": "evm",
        "symbol": "BNB",
        "decimals": 18,
        "rpc_url": "https://binance.llamarpc.com",
        "explorer_url": "https://bscscan.com",
        "gecko_network_id": "bsc",
        "is_testnet": False,
    },
    "137": {
        "name": "Polygon PoS",
        "chain_id": 137,
        "type": "evm",
        "symbol": "POL",
        "decimals": 18,
        "rpc_url": "https://polygon.llamarpc.com",
        "explorer_url": "https://polygonscan.com",
        "gecko_network_id": "polygon_pos",
        "is_testnet": False,
    },
    "42161": {
        "name": "Arbitrum One",
        "chain_id": 42161,
        "type": "evm",
        "symbol": "ETH",
        "decimals": 18,
        "rpc_url": "https://arbitrum.llamarpc.com",
        "explorer_url": "https://arbiscan.io",
        "gecko_network_id": "arbitrum",
        "is_testnet": False,
    },
    "10": {
        "name": "Optimism",
        "chain_id": 10,
        "type": "evm",
        "symbol": "ETH",
        "decimals": 18,
        "rpc_url": "https://optimism.llamarpc.com",
        "explorer_url": "https://optimistic.etherscan.io",
        "gecko_network_id": "optimism",
        "is_testnet": False,
    },
    "8453": {
        "name": "Base",
        "chain_id": 8453,
        "type": "evm",
        "symbol": "ETH",
        "decimals": 18,
        "rpc_url": "https://mainnet.base.org",
        "explorer_url": "https://basescan.org",
        "gecko_network_id": "base",
        "is_testnet": False,
    },
    "43114": {
        "name": "Avalanche C-Chain",
        "chain_id": 43114,
        "type": "evm",
        "symbol": "AVAX",
        "decimals": 18,
        "rpc_url": "https://api.avax.network/ext/bc/C/rpc",
        "explorer_url": "https://snowtrace.io",
        "gecko_network_id": "avax",
        "is_testnet": False,
    },
    "solana": {
        "name": "Solana",
        "chain_id": "solana",
        "type": "solana",
        "symbol": "SOL",
        "decimals": 9,
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "explorer_url": "https://solscan.io",
        "gecko_network_id": "solana",
        "is_testnet": False,
    },
}


def get_network_by_chain_id(chain_id: str | int) -> dict:
    """Retrieve network configuration by Chain ID or network key."""
    key = str(chain_id)
    if key in SUPPORTED_NETWORKS:
        return SUPPORTED_NETWORKS[key]
    # Default to Ethereum
    return SUPPORTED_NETWORKS["1"]


def get_all_networks() -> list[dict]:
    """Return all supported networks."""
    return list(SUPPORTED_NETWORKS.values())


def format_explorer_tx_url(chain_id: str | int, tx_hash: str) -> str:
    """Generate block explorer transaction link."""
    network = get_network_by_chain_id(chain_id)
    base_url = network.get("explorer_url", "https://etherscan.io")
    if network.get("type") == "solana":
        return f"{base_url}/tx/{tx_hash}"
    return f"{base_url}/tx/{tx_hash}"


def format_explorer_address_url(chain_id: str | int, address: str) -> str:
    """Generate block explorer address link."""
    network = get_network_by_chain_id(chain_id)
    base_url = network.get("explorer_url", "https://etherscan.io")
    if network.get("type") == "solana":
        return f"{base_url}/account/{address}"
    return f"{base_url}/address/{address}"
