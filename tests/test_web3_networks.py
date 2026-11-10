from chainscope import web3_networks


def test_get_all_networks_contains_major_chains():
    nets = web3_networks.get_all_networks()
    symbols = [n["symbol"] for n in nets]
    assert "ETH" in symbols
    assert "BNB" in symbols
    assert "POL" in symbols
    assert "SOL" in symbols


def test_get_network_by_chain_id_retrieves_correct_data():
    eth = web3_networks.get_network_by_chain_id(1)
    assert eth["name"] == "Ethereum"
    assert eth["decimals"] == 18

    bsc = web3_networks.get_network_by_chain_id(56)
    assert bsc["name"] == "BNB Smart Chain"
    assert bsc["symbol"] == "BNB"


def test_format_explorer_tx_url():
    url = web3_networks.format_explorer_tx_url(1, "0xabc123")
    assert "https://etherscan.io/tx/0xabc123" == url
