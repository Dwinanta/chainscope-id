from chainscope import web3_wallet


def test_is_valid_evm_address():
    assert web3_wallet.is_valid_evm_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045") is True
    assert web3_wallet.is_valid_evm_address("0x123") is False
    assert web3_wallet.is_valid_evm_address("not_an_address") is False


def test_is_valid_solana_address():
    assert web3_wallet.is_valid_solana_address("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU") is True
    assert web3_wallet.is_valid_solana_address("short") is False


def test_format_short_address():
    short = web3_wallet.format_short_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
    assert short == "0xd8dA...6045"
