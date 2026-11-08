from chainscope import wallet_component


def test_render_personal_wallet_loads_html_in_light_theme(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        wallet_component.st,
        "iframe",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    wallet_component.render_personal_wallet()

    assert "<title>AturUang - Personal Finance Tracker</title>" in rendered["html"]
    assert '<html lang="id" class="light">' in rendered["html"]
    assert "__INITIAL_THEME__" not in rendered["html"]
    assert "__DARK_THEME_STYLE__" not in rendered["html"]
    assert "linear-gradient(135deg, #0B0918 0%, #100D22 52%, #15102A 100%)" not in rendered["html"]
    assert rendered["options"] == {
        "height": 1000,
        "alt": "AturUang personal finance tracker",
    }


def test_render_personal_wallet_uses_dark_theme(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        wallet_component.st,
        "iframe",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    wallet_component.render_personal_wallet(dark_mode=True)

    assert '<html lang="id" class="dark">' in rendered["html"]
    assert 'const HOST_THEME = "dark";' in rendered["html"]
    assert "localStorage.getItem('aturuang_theme') || 'dark'" in rendered["html"]
    assert "background: linear-gradient(135deg, #0B0918 0%, #100D22 52%, #15102A 100%);" in rendered["html"]
    assert "background: linear-gradient(145deg, #19152F 0%, #141127 100%);" in rendered["html"]
    assert "box-shadow: 0 10px 28px rgba(2, 6, 23, 0.24);" in rendered["html"]
    assert "borderColor: isDark ? '#19152F' : '#ffffff'" in rendered["html"]
    assert "color-scheme: dark;" in rendered["html"]
    assert "background: #211B38;" in rendered["html"]
    assert "select option" in rendered["html"]
    assert "button:disabled" in rendered["html"]
    assert "__DARK_THEME_STYLE__" not in rendered["html"]
    assert "__DARK_CHART_BORDER__" not in rendered["html"]
