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
    assert "linear-gradient(135deg, #080B14 0%, #0D1220 50%, #111827 100%)" not in rendered["html"]
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
    assert "background: linear-gradient(135deg, #080B14 0%, #0D1220 50%, #111827 100%);" in rendered["html"]
    assert "background: linear-gradient(145deg, #151B2B 0%, #111827 100%);" in rendered["html"]
    assert "box-shadow: 0 8px 24px rgba(2, 6, 23, 0.18);" in rendered["html"]
    assert "borderColor: isDark ? '#151B2B' : '#ffffff'" in rendered["html"]
    assert "__DARK_THEME_STYLE__" not in rendered["html"]
    assert "__DARK_CHART_BORDER__" not in rendered["html"]
