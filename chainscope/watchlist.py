"""Watchlist pengguna — disimpan ke file JSON lokal.

Watchlist bersifat per-instalasi (bukan per-pengguna), karena
belum ada sistem login di versi ini. Cocok untuk single-user lokal
atau sebagai fondasi fitur berbayar di kemudian hari.
"""

import json
from pathlib import Path

# Disimpan di root proyek: <root>/watchlist.json
WATCHLIST_FILE = Path(__file__).resolve().parent.parent / "watchlist.json"


def load_watchlist() -> list[str]:
    """Baca watchlist dari disk. Kembalikan list ID koin (mis. 'bitcoin')."""
    if not WATCHLIST_FILE.exists():
        return []
    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [str(x) for x in data]


def save_watchlist(coin_ids: list[str]) -> None:
    """Simpan watchlist ke disk (urut & unik)."""
    cleaned = sorted({str(c) for c in coin_ids if c})
    WATCHLIST_FILE.write_text(
        json.dumps(cleaned, indent=2),
        encoding="utf-8",
    )


def add_coin(coin_id: str) -> list[str]:
    """Tambah satu koin ke watchlist (idempotent)."""
    current = load_watchlist()
    if coin_id not in current:
        current.append(coin_id)
        save_watchlist(current)
    return load_watchlist()


def remove_coin(coin_id: str) -> list[str]:
    """Hapus satu koin dari watchlist."""
    current = [c for c in load_watchlist() if c != coin_id]
    save_watchlist(current)
    return current


def is_in_watchlist(coin_id: str) -> bool:
    """Cek apakah koin sudah ada di watchlist."""
    return coin_id in load_watchlist()