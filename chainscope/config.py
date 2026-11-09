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
    "USD": {"label": "United States Dollar (USD)", "prefix": "$"},
    "IDR": {"label": "Indonesian Rupiah (IDR)", "prefix": "Rp"},
    "EUR": {"label": "Euro (EUR)", "prefix": "€"},
    "GBP": {"label": "British Pound (GBP)", "prefix": "£"},
    "JPY": {"label": "Japanese Yen (JPY)", "prefix": "¥"},
    "AUD": {"label": "Australian Dollar (AUD)", "prefix": "A$"},
    "CAD": {"label": "Canadian Dollar (CAD)", "prefix": "C$"},
    "CHF": {"label": "Swiss Franc (CHF)", "prefix": "CHF "},
    "CNY": {"label": "Chinese Yuan (CNY)", "prefix": "CN¥"},
    "SGD": {"label": "Singapore Dollar (SGD)", "prefix": "S$"},
    "MYR": {"label": "Malaysian Ringgit (MYR)", "prefix": "RM"},
}
DEFAULT_CURRENCY = "IDR"

_CURRENCY_NAMES_ID = {
    "USD": "Dolar AS",
    "IDR": "Rupiah Indonesia",
    "EUR": "Euro",
    "GBP": "Pound sterling",
    "JPY": "Yen Jepang",
    "AUD": "Dolar Australia",
    "CAD": "Dolar Kanada",
    "CHF": "Franc Swiss",
    "CNY": "Yuan Tiongkok",
    "SGD": "Dolar Singapura",
    "MYR": "Ringgit Malaysia",
}


def currency_display_label(code: str, language: str = "EN") -> str:
    """Return a concise, human-readable currency option label."""
    currency = CURRENCY_OPTIONS.get(code.upper())
    if currency is None:
        return code.upper()
    if language.upper() == "ID":
        name = _CURRENCY_NAMES_ID.get(code.upper(), currency["label"])
    else:
        name = currency["label"].rsplit(" (", 1)[0]
    return f"{code.upper()} · {name}"


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
        "AI Research": "AI Research",
        "Risk Center": "Risk Center",
        "Performance Coach": "Performance Coach",
        "Market": "Market",
        "Insights": "Insights",
        "Tools": "Tools",
        "Preferences": "Preferences",
        "Display currency": "Display currency",
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
        "AI Research": "Riset AI",
        "Risk Center": "Pusat Risiko",
        "Performance Coach": "Performance Coach",
        "Market": "Pasar",
        "Insights": "Analisis",
        "Tools": "Alat",
        "Preferences": "Preferensi",
        "Display currency": "Mata uang tampilan",
    },
}


def translate(language: str, text: str) -> str:
    """Translate a primary navigation label, falling back to its source text."""
    language_translations = UI_TRANSLATIONS.get(language, UI_TRANSLATIONS["EN"])
    return language_translations.get(text, text)


# Kurs tetap hanya untuk Mode Demo (bukan kurs resmi)
DEMO_USD_TO_IDR = 16_000.0