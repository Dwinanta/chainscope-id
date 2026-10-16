"""Tes untuk fungsi format angka."""

from chainscope import formatting
# (ganti 'chainsope' menjadi 'chainscope' agar sesuai nama package)


def test_format_money_usd_small():
    assert formatting.format_money(1000, "USD") == "$1,000.00"


def test_format_money_usd_billion():
    assert formatting.format_money(1_500_000_000, "USD") == "$1.50 B"


def test_format_money_idr_billion():
    assert formatting.format_money(1_500_000_000, "IDR") == "Rp1,50 M"


def test_format_money_idr_trillion():
    assert formatting.format_money(1_650_000_000_000, "IDR") == "Rp1,65 T"


def test_format_money_none():
    assert formatting.format_money(None, "USD") == "-"


def test_format_percent_positive():
    assert formatting.format_percent(1.5) == "+1.50%"


def test_format_percent_negative():
    assert formatting.format_percent(-2.345) == "-2.35%"


def test_format_percent_none():
    assert formatting.format_percent(None) == "-"