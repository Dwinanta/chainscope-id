from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from streamlit.testing.v1 import AppTest

from chainscope import ui


def test_apply_theme_uses_light_palette_without_global_text_overrides(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        ui.st,
        "markdown",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    ui.apply_theme()

    css = rendered["html"]
    assert "--cs-main-background: #F8FAFC;" in css
    assert "--cs-content-background: #FFFFFF;" in css
    assert "--cs-sidebar-background: #F1F5F9;" in css
    assert "--cs-primary-text: #0F172A;" in css
    assert "--cs-accent: #7C3AED;" in css
    assert "--cs-card-surface: #FFFFFF;" in css
    assert "--cs-card-radius: 10px;" in css
    assert "--cs-card-shadow: none;" in css
    assert "linear-gradient(135deg, #080B14 0%, #0D1220 50%, #111827 100%)" not in css
    assert "linear-gradient(180deg, #0B1020 0%, #111827 55%, #17132B 100%)" not in css
    assert "linear-gradient(145deg, #151B2B 0%, #111827 100%)" not in css
    assert ".stApp p, .stApp span, .stApp div" not in css
    assert '[data-testid="stSidebar"] [data-testid="stSelectbox"]' in css
    assert "@media (max-width: 768px)" in css
    assert '[data-testid="stSidebarCollapseButton"]' in css
    assert rendered["options"] == {"unsafe_allow_html": True}


def test_apply_theme_uses_dark_palette(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        ui.st,
        "markdown",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    ui.apply_theme(True)

    css = rendered["html"]
    assert "color-scheme: dark" in css
    assert "--cs-main-background: #0B1120;" in css
    assert "--cs-content-background: #111827;" in css
    assert "--cs-sidebar-background: #0F172A;" in css
    assert "--cs-primary-text: #F8FAFC;" in css
    assert "--cs-secondary-text: #CBD5E1;" in css
    assert "--cs-border: #334155;" in css
    assert "--cs-accent: #A78BFA;" in css
    assert "--cs-input-background: #1E293B;" in css
    assert (
        ".stApp {\n"
        "            background: linear-gradient(135deg, #080B14 0%, "
        "#0D1220 50%, #111827 100%) !important;"
    ) in css
    assert (
        "--cs-sidebar-background-gradient: linear-gradient(180deg, "
        "#0B1020 0%, #111827 55%, #17132B 100%);"
    ) in css
    assert (
        "--cs-card-surface: linear-gradient(145deg, "
        "#151B2B 0%, #111827 100%);"
    ) in css
    assert "--cs-card-border: rgba(167, 139, 250, 0.18);" in css
    assert (
        "--cs-card-surface: linear-gradient(145deg, #151B2B 0%, #111827 100%);"
    ) in css
    assert "--cs-card-radius: 12px;" in css
    assert "--cs-card-shadow: 0 8px 24px rgba(2, 6, 23, 0.18);" in css
    assert "[data-testid=\"stVerticalBlockBorderWrapper\"]" in css
    assert "background: var(--cs-card-surface);" in css
    assert "[data-testid=\"stAlert\"]" in css
    assert ".landing-card" in css
    assert "border-radius: var(--cs-card-radius);" in css
    assert "box-shadow: var(--cs-card-shadow);" in css
    assert "[data-testid=\"stMetric\"]" in css
    assert '[data-testid="stSidebar"] [data-testid="stSelectbox"]' in css
    assert ".landing-card" in css
    assert "border-right: 1px solid var(--cs-border);" in css
    assert "background: var(--cs-sidebar-background-gradient);" in css
    assert rendered["options"] == {"unsafe_allow_html": True}


def test_crypto_news_link_and_selection_styles_are_dark_mode_only(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        ui.st,
        "markdown",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    ui.apply_theme(is_dark_mode=True)
    dark_css = rendered["html"]

    assert ".st-key-crypto_news [data-testid=\"stLinkButton\"] a" in dark_css
    assert "color: var(--cs-primary-text);" in dark_css
    assert "background: var(--cs-card-surface);" in dark_css
    assert "border-radius: var(--cs-card-radius);" in dark_css
    assert "box-shadow: var(--cs-card-shadow);" in dark_css
    assert ".st-key-crypto_news ::selection" in dark_css
    assert "background: rgba(167, 139, 250, 0.32);" in dark_css

    ui.apply_theme(is_dark_mode=False)
    light_css = rendered["html"]

    assert ".st-key-crypto_news [data-testid=\"stLinkButton\"] a" not in light_css
    assert ".st-key-crypto_news ::selection" not in light_css
    assert (
        "--cs-card-surface: linear-gradient(145deg, #151B2B 0%, #111827 100%);"
        not in light_css
    )


def test_plotly_and_dataframe_styles_follow_active_palette():
    figure = ui.apply_plotly_theme(go.Figure(), is_dark_mode=True)
    styled = ui.style_dataframe(pd.DataFrame({"value": [1]}), is_dark_mode=True)

    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.plot_bgcolor == "#111827"
    assert figure.layout.font.color == "#F8FAFC"
    assert figure.layout.yaxis.gridcolor == "rgba(148, 163, 184, 0.12)"
    assert "#111827" in styled.to_html()
    assert "#F8FAFC" in styled.to_html()


def test_plotly_light_background_remains_unchanged():
    figure = ui.apply_plotly_theme(go.Figure())

    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.plot_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.template.layout.plot_bgcolor == "white"


def test_market_indicator_colors_match_theme_tokens():
    light = ui.get_theme_palette()
    dark = ui.get_theme_palette(is_dark_mode=True)

    for palette in (light, dark):
        assert palette["positive"] == "#16A34A"
        assert palette["negative"] == "#DC2626"
        assert palette["warning"] == "#F59E0B"
        assert palette["info"] == "#3B82F6"

    assert light["positive_text"] == "#15803D"
    assert light["warning_text"] == "#B45309"
    assert dark["positive_text"] == "#4ADE80"
    assert dark["warning_text"] == "#FBBF24"


def test_app_theme_toggle_reruns_without_resetting_page_state():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.session_state["show_landing"] is True
    assert any(
        "--cs-main-background: #F8FAFC;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(True).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is True
    assert app.session_state["show_landing"] is True
    assert any(
        "--cs-main-background: #0B1120;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(False).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.session_state["show_landing"] is True
    assert any(
        "--cs-main-background: #F8FAFC;" in element.value
        for element in app.markdown
    )

    app.button(key="landing_get_started").click().run()

    assert not app.exception
    assert app.session_state["show_landing"] is False
    assert any(element.label == "Email" for element in app.text_input)
    assert any(
        "--cs-main-background: #F8FAFC;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(True).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is True
    assert app.session_state["show_landing"] is False
    assert any(
        "--cs-main-background: #0B1120;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(False).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.session_state["show_landing"] is False
    assert any(
        "--cs-main-background: #F8FAFC;" in element.value
        for element in app.markdown
    )
