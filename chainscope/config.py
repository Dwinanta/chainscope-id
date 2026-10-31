"""Konstanta konfigurasi untuk ChainScope ID."""

# API
API_BASE = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT = 15           # detik
CACHE_TTL_SECONDS = 90

# Pilihan koin
SUMMARY_CARD_COUNT = 3
MOVERS_PER_SIDE = 5

# Mata uang
CURRENCY_OPTIONS = {
    "USD": {"label": "USD (Dolar AS)", "prefix": "$"},
    "IDR": {"label": "IDR (Rupiah)", "prefix": "Rp"},
    "EUR": {"label": "EUR (Euro)", "prefix": "€"},
    "GBP": {"label": "GBP (Pound Sterling)", "prefix": "£"},
    "JPY": {"label": "JPY (Yen Jepang)", "prefix": "¥"},
    "AUD": {"label": "AUD (Dolar Australia)", "prefix": "A$"},
    "CAD": {"label": "CAD (Dolar Kanada)", "prefix": "C$"},
    "CHF": {"label": "CHF (Franc Swiss)", "prefix": "CHF "},
    "CNY": {"label": "CNY (Yuan Tiongkok)", "prefix": "CN¥"},
    "SGD": {"label": "SGD (Dolar Singapura)", "prefix": "S$"},
    "MYR": {"label": "MYR (Ringgit Malaysia)", "prefix": "RM"},
}
DEFAULT_CURRENCY = "IDR"

# Kurs tetap hanya untuk Mode Demo (bukan kurs resmi)
DEMO_USD_TO_IDR = 16_000.0