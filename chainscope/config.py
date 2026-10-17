"""Konstanta konfigurasi untuk ChainScope ID."""

# API
API_BASE = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT = 15           # detik
CACHE_TTL_SECONDS = 90

# Pilihan koin
COIN_COUNT_OPTIONS = [50, 100, 250]
DEFAULT_COIN_COUNT = 20
SUMMARY_CARD_COUNT = 3
MOVERS_PER_SIDE = 5

# Mata uang
CURRENCY_OPTIONS = {
    "IDR": {"label": "IDR (Rupiah)", "prefix": "Rp"},
    "USD": {"label": "USD (Dolar AS)", "prefix": "$"},
}
DEFAULT_CURRENCY = "IDR"

# Kurs tetap hanya untuk Mode Demo (bukan kurs resmi)
DEMO_USD_TO_IDR = 16_000.0