from chainscope import config


def test_translate_primary_navigation_labels():
    assert config.translate("ID", "Market Overview") == "Ringkasan Pasar"
    assert config.translate("EN", "Market Overview") == "Market Overview"
    assert config.translate("ID", "🏠 Market Overview") == "🏠 Ringkasan Pasar"


def test_translate_falls_back_for_unknown_labels_and_languages():
    assert config.translate("ID", "Untranslated label") == "Untranslated label"
    assert config.translate("FR", "Market Overview") == "Market Overview"


def test_new_research_and_risk_navigation_labels_are_localized():
    assert config.translate("EN", "AI Research") == "AI Research"
    assert config.translate("ID", "AI Research") == "Riset AI"
    assert config.translate("EN", "Risk Center") == "Risk Center"
    assert config.translate("ID", "Risk Center") == "Pusat Risiko"


def test_sidebar_group_and_preference_labels_are_localized():
    assert config.translate("EN", "Insights") == "Insights"
    assert config.translate("ID", "Insights") == "Analisis"
    assert config.translate("ID", "Display currency") == "Mata uang tampilan"


def test_currency_labels_use_distinct_fiat_names_and_codes():
    assert config.CURRENCY_OPTIONS["IDR"]["label"] == "Indonesian Rupiah (IDR)"
    assert config.CURRENCY_OPTIONS["USD"]["label"] == "United States Dollar (USD)"
    assert config.CURRENCY_OPTIONS["EUR"]["label"] == "Euro (EUR)"
    assert config.CURRENCY_OPTIONS["JPY"]["label"] == "Japanese Yen (JPY)"
    assert config.CURRENCY_OPTIONS["GBP"]["label"] == "British Pound (GBP)"
    assert config.DEFAULT_CURRENCY in config.CURRENCY_OPTIONS


def test_currency_display_labels_are_concise_and_localized():
    assert config.currency_display_label("IDR", "EN") == "IDR · Indonesian Rupiah"
    assert config.currency_display_label("IDR", "ID") == "IDR · Rupiah Indonesia"
    assert config.currency_display_label("unknown", "ID") == "UNKNOWN"
