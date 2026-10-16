"""Tes untuk modul watchlist."""

from unittest.mock import patch

from chainscope import watchlist


def test_load_watchlist_empty_when_file_missing(tmp_path):
    fake = tmp_path / "watchlist.json"
    with patch.object(watchlist, "WATCHLIST_FILE", fake):
        assert watchlist.load_watchlist() == []


def test_save_and_load_roundtrip(tmp_path):
    fake = tmp_path / "watchlist.json"
    with patch.object(watchlist, "WATCHLIST_FILE", fake):
        watchlist.save_watchlist(["bitcoin", "ethereum", "bitcoin"])
        # Unik & terurut
        assert watchlist.load_watchlist() == ["bitcoin", "ethereum"]


def test_add_coin_idempotent(tmp_path):
    fake = tmp_path / "watchlist.json"
    with patch.object(watchlist, "WATCHLIST_FILE", fake):
        watchlist.add_coin("bitcoin")
        watchlist.add_coin("bitcoin")
        assert watchlist.load_watchlist() == ["bitcoin"]


def test_remove_coin(tmp_path):
    fake = tmp_path / "watchlist.json"
    with patch.object(watchlist, "WATCHLIST_FILE", fake):
        watchlist.save_watchlist(["bitcoin", "ethereum"])
        watchlist.remove_coin("bitcoin")
        assert watchlist.load_watchlist() == ["ethereum"]


def test_is_in_watchlist(tmp_path):
    fake = tmp_path / "watchlist.json"
    with patch.object(watchlist, "WATCHLIST_FILE", fake):
        watchlist.save_watchlist(["bitcoin"])
        assert watchlist.is_in_watchlist("bitcoin") is True
        assert watchlist.is_in_watchlist("ethereum") is False