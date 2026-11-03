from chainscope import config


def test_translate_primary_navigation_labels():
    assert config.translate("ID", "Market Overview") == "Ringkasan Pasar"
    assert config.translate("EN", "Market Overview") == "Market Overview"
    assert config.translate("ID", "🏠 Market Overview") == "🏠 Ringkasan Pasar"


def test_translate_falls_back_for_unknown_labels_and_languages():
    assert config.translate("ID", "Untranslated label") == "Untranslated label"
    assert config.translate("FR", "Market Overview") == "Market Overview"
