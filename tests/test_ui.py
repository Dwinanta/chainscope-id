from chainscope import ui


def test_sidebar_navigation_uses_minimal_active_and_inactive_styles(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        ui.st,
        "markdown",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    ui.apply_premium_theme()

    css = rendered["html"]
    assert "color: #77788A !important" in css
    assert "background-color: #f0e9ff !important" in css
    assert "color: #7c3aed !important" in css
    assert "margin-bottom: 4px !important" in css
    assert rendered["options"] == {"unsafe_allow_html": True}
