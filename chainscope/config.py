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

# Main navigation and page titles
UI_TRANSLATIONS = {
    "EN": {
        "Language": "Language",
        "Dark Mode": "Dark Mode",
        "🏠 Market Overview": "🏠 Market Overview",
        "📊 Market Data": "📊 Market Data",
        "📊 Strategi Relatif": "📊 Relative Strategy",
        "📒 Trading Journal": "📒 Trading Journal",
        "🔔 Price Alerts": "🔔 Price Alerts",
        "📄 Laporan PDF": "📄 PDF Report",
        "📉 Technical Analysis": "📉 Technical Analysis",
        "💼 Portfolio": "💼 Portfolio",
        "💱 Converter": "💱 Converter",
        "⭐ Watchlist": "⭐ Watchlist",
        "👑 Admin Panel": "👑 Admin Panel",
        "Market Overview": "Market Overview",
        "Market Data": "Market Data",
        "Strategi Relatif": "Relative Strategy",
        "Technical Analysis": "Technical Analysis",
        "Trading Journal": "Trading Journal",
        "Price Alerts": "Price Alerts",
        "Laporan PDF": "PDF Report",
        "Portfolio": "Portfolio",
        "Converter": "Converter",
        "Watchlist": "Watchlist",
        "Admin Panel": "Admin Panel",
    },
    "ID": {
        "Language": "Bahasa",
        "Dark Mode": "Mode Gelap",
        "🏠 Market Overview": "🏠 Ringkasan Pasar",
        "📊 Market Data": "📊 Data Pasar",
        "📊 Strategi Relatif": "📊 Strategi Relatif",
        "📒 Trading Journal": "📒 Jurnal Trading",
        "🔔 Price Alerts": "🔔 Peringatan Harga",
        "📄 Laporan PDF": "📄 Laporan PDF",
        "📉 Technical Analysis": "📉 Analisis Teknikal",
        "💼 Portfolio": "💼 Portofolio",
        "💱 Converter": "💱 Konverter",
        "⭐ Watchlist": "⭐ Daftar Pantauan",
        "👑 Admin Panel": "👑 Panel Admin",
        "Market Overview": "Ringkasan Pasar",
        "Market Data": "Data Pasar",
        "Strategi Relatif": "Strategi Relatif",
        "Technical Analysis": "Analisis Teknikal",
        "Trading Journal": "Jurnal Trading",
        "Price Alerts": "Peringatan Harga",
        "Laporan PDF": "Laporan PDF",
        "Portfolio": "Portofolio",
        "Converter": "Konverter",
        "Watchlist": "Daftar Pantauan",
        "Admin Panel": "Panel Admin",
    },
}


def translate(language: str, text: str) -> str:
    """Translate a primary navigation label, falling back to its source text."""
    language_translations = UI_TRANSLATIONS.get(language, UI_TRANSLATIONS["EN"])
    return language_translations.get(text, text)


# Kurs tetap hanya untuk Mode Demo (bukan kurs resmi)
DEMO_USD_TO_IDR = 16_000.0