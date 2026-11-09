from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from streamlit.testing.v1 import AppTest

from chainscope import formatting, ui


def test_clean_html_text_removes_highlight_markup_and_decodes_entities():
    title = '<span style="background-color:#fff"><b>Bitcoin</b></span> &amp; Ethereum'

    assert formatting.clean_html_text(title) == "Bitcoin & Ethereum"


def test_apply_theme_uses_light_palette_without_global_text_overrides(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        ui.st,
        "markdown",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    ui.apply_theme()

    css = rendered["html"]
    assert "--cs-main-background: #F8F7FC;" in css
    assert "--cs-content-background: #FFFFFF;" in css
    assert "--cs-sidebar-background: #FFFFFF;" in css
    assert "--cs-primary-text: #181329;" in css
    assert "--cs-secondary-text: #6B7280;" in css
    assert "--cs-border: #E5E1EF;" in css
    assert "--cs-input-background: #FFFFFF;" in css
    assert "--cs-accent: #7C3AED;" in css
    assert "--cs-accent-secondary: #9333EA;" in css
    assert "--cs-timeframe-background: #FFFFFF;" in css
    assert "--cs-timeframe-border: #E5E1EF;" in css
    assert "--cs-timeframe-text: #6B7280;" in css
    assert "--cs-timeframe-active: #7C3AED;" in css
    assert "--cs-card-surface: #FFFFFF;" in css
    assert "--cs-card-radius: 10px;" in css
    assert "--cs-card-shadow: none;" in css
    assert "linear-gradient(135deg, #0B0918 0%, #100D22 52%, #15102A 100%)" not in css
    assert "--cs-sidebar-background-gradient" not in css
    assert ".stApp p, .stApp span, .stApp div" not in css
    assert '[data-testid="stSidebar"] [data-testid="stSelectbox"]' in css
    assert '[data-testid="stDateInput"] [data-baseweb="calendar"]' in css
    assert '[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]' in css
    assert '[data-testid="stNumberInput"] button' in css
    assert '[data-testid="stProgress"] [role="progressbar"]' in css
    assert "@media (max-width: 768px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "@keyframes cs-enter" in css
    assert ".landing-hero-panel" in css
    assert ".auth-promo" in css
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
    assert "--cs-main-background: #0B0918;" in css
    assert "--cs-content-background: #0B0918;" in css
    assert "--cs-sidebar-background: #100D22;" in css
    assert "--cs-primary-text: #F8FAFC;" in css
    assert "--cs-secondary-text: #A1A1AA;" in css
    assert "--cs-border: rgba(139, 92, 246, 0.25);" in css
    assert "--cs-accent: #7C3AED;" in css
    assert "--cs-accent-secondary: #9333EA;" in css
    assert "--cs-purple-soft: #DDD6FE;" in css
    assert "--cs-blue-primary: #3B82F6;" in css
    assert "--cs-blue-secondary: #3B82F6;" in css
    assert "--cs-cyan-accent: #22D3EE;" in css
    assert "--cs-blue-soft: #BFDBFE;" in css
    assert "--cs-market-chart: #3B82F6;" in css
    assert "--cs-timeframe-background: #121027;" in css
    assert "--cs-timeframe-border: rgba(139, 92, 246, 0.25);" in css
    assert "--cs-timeframe-active: #7C3AED;" in css
    assert "--cs-timeframe-hover: #211B3C;" in css
    assert (
        '.st-key-overview_timeframe [data-testid="stButtonGroup"] '
        '[role="radiogroup"]'
    ) in css
    assert '> button[role="radio"][aria-checked="true"]' in css
    assert '[data-selected="true"]' in css
    assert ':hover' in css
    assert ':focus-visible' in css
    assert "background: var(--cs-timeframe-hover);" in css
    assert "background: var(--cs-timeframe-active);" in css
    assert "--cs-input-background: #211B38;" in css
    assert (
        ".stApp {\n"
        "            background: linear-gradient(135deg, #0B0918 0%, "
        "#100D22 52%, #15102A 100%) !important;"
    ) in css
    assert (
        "--cs-sidebar-surface: #100D22;"
    ) in css
    assert (
        "--cs-card-surface: linear-gradient(145deg, "
        "#19152F 0%, #141127 100%);"
    ) in css
    assert "--cs-card-border: rgba(139, 92, 246, 0.25);" in css
    assert (
        "--cs-card-surface: linear-gradient(145deg, #19152F 0%, #141127 100%);"
    ) in css
    assert "--cs-card-radius: 12px;" in css
    assert "--cs-card-shadow: 0 10px 28px rgba(2, 6, 23, 0.24);" in css
    assert "[data-testid=\"stVerticalBlockBorderWrapper\"]" in css
    assert "background: var(--cs-card-surface);" in css
    assert "[data-testid=\"stAlert\"]" in css
    assert ".landing-card" in css
    assert "border-radius: var(--cs-card-radius);" in css
    assert "box-shadow: var(--cs-card-shadow);" in css
    assert "[data-testid=\"stMetric\"]" in css
    assert ".landing-card" in css
    assert "border-right: 1px solid var(--cs-border);" in css
    assert "background: var(--cs-sidebar-background);" in css
    assert "background: linear-gradient(110deg, var(--cs-accent), var(--cs-accent-secondary));" in css
    assert "linear-gradient(135deg, var(--cs-accent), var(--cs-blue-secondary))" in css
    assert '[data-testid="stDateInput"] [data-baseweb="calendar"]' in css
    assert '[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"]' in css
    assert '[data-testid="stNumberInput"] button' in css
    assert '[data-testid="stDialog"]' in css
    assert '[data-testid="stSpinner"]' in css
    assert rendered["options"] == {"unsafe_allow_html": True}


def test_form_component_styles_are_shared_by_both_themes(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        ui.st,
        "markdown",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    ui.apply_theme(is_dark_mode=True)
    dark_css = rendered["html"]
    assert "color-scheme: dark" in dark_css
    assert '[data-testid="stDownloadButton"] button' in dark_css
    assert '[data-baseweb="popover"]' in dark_css
    assert '[role="option"][aria-selected="true"]' in dark_css
    assert '[data-testid="stFileUploader"] button' in dark_css
    assert '[data-testid="stNumberInput"] button:hover' in dark_css
    assert '[data-testid="stDateInput"] [data-baseweb="calendar"] button' in dark_css
    assert '[data-testid="stTextArea"] textarea:disabled' in dark_css
    assert '[data-testid="stButton"] > button:focus-visible' in dark_css

    ui.apply_theme(is_dark_mode=False)
    light_css = rendered["html"]
    assert "color-scheme: light" in light_css
    assert '[data-testid="stDownloadButton"] button' in light_css
    assert '[data-baseweb="popover"]' in light_css
    assert '[role="option"][aria-selected="true"]' in light_css
    assert '[data-testid="stFileUploader"] button' in light_css
    assert '[data-testid="stNumberInput"] button:hover' in light_css
    assert '[data-testid="stDateInput"] [data-baseweb="calendar"] button' in light_css
    assert '[data-testid="stTextArea"] textarea:disabled' in light_css
    assert '[data-testid="stButton"] > button:focus-visible' in light_css
    assert "!important" not in light_css.replace(
        "background: #F8F7FC !important;", ""
    )


def test_plotly_and_dataframe_styles_follow_active_palette():
    figure = ui.apply_plotly_theme(go.Figure(), is_dark_mode=True)
    styled = ui.style_dataframe(pd.DataFrame({"value": [1]}), is_dark_mode=True)

    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.plot_bgcolor == "#121027"
    assert figure.layout.font.color == "#F8FAFC"
    assert figure.layout.yaxis.gridcolor == "rgba(161, 161, 170, 0.12)"
    assert "#0B0918" in styled.to_html()
    assert "#F8FAFC" in styled.to_html()


def test_plotly_light_background_remains_unchanged():
    figure = ui.apply_plotly_theme(go.Figure())

    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.plot_bgcolor == "rgba(0,0,0,0)"
    assert figure.layout.template.layout.plot_bgcolor == "white"


def test_market_indicator_colors_match_theme_tokens():
    light = ui.get_theme_palette()
    dark = ui.get_theme_palette(is_dark_mode=True)

    for palette in (light,):
        assert palette["positive"] == "#16A34A"
        assert palette["negative"] == "#DC2626"
        assert palette["warning"] == "#F59E0B"
        assert palette["info"] == "#3B82F6"

    assert dark["positive"] == "#10B981"
    assert dark["negative"] == "#F43F5E"
    assert dark["warning"] == "#F59E0B"
    assert dark["info"] == "#3B82F6"
    assert light["positive_text"] == "#15803D"
    assert light["warning_text"] == "#B45309"
    assert dark["positive_text"] == "#34D399"
    assert dark["warning_text"] == "#FBBF24"
    assert light["market_chart"] == "#7C3AED"
    assert dark["market_chart"] == "#3B82F6"


def test_user_widget_keys_do_not_share_state_across_accounts():
    assert ui.user_state_key("watchlist", "user-a") == "watchlist_user-a"
    assert ui.user_state_key("watchlist", "user-a") != ui.user_state_key(
        "watchlist", "user-b"
    )


def test_render_coin_logo_uses_https_asset_and_asset_specific_fallback():
    markup = ui.render_coin_logo(
        "bitcoin", "https://assets.coingecko.com/coins/images/1/large/bitcoin.png", 24, "BTC"
    )

    assert 'data-coin-id="bitcoin"' in markup
    assert 'src="https://assets.coingecko.com/coins/images/1/large/bitcoin.png"' in markup
    assert 'alt="BTC logo"' in markup
    assert 'class="cs-coin-logo-fallback" aria-hidden="true" hidden' in markup
    assert "onerror=" in markup


def test_render_coin_logo_rejects_non_https_image_and_escapes_text():
    markup = ui.render_coin_logo('coin" onclick="bad', "javascript:alert(1)", 20, "<X>")

    assert "javascript:" not in markup
    assert 'data-coin-id="coin&quot; onclick=&quot;bad"' in markup
    assert "&lt;X&gt;" in markup
    assert "<img" not in markup


def test_app_theme_toggle_reruns_without_resetting_page_state():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.session_state["show_landing"] is True
    assert any(
        "--cs-main-background: #F8F7FC;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(True).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is True
    assert app.session_state["show_landing"] is True
    assert any(
        "--cs-main-background: #0B0918;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(False).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.session_state["show_landing"] is True
    assert any(
        "--cs-main-background: #F8F7FC;" in element.value
        for element in app.markdown
    )

    app.button(key="landing_get_started").click().run()

    assert not app.exception
    assert app.session_state["show_landing"] is False
    assert any(element.label == "Email" for element in app.text_input)
    assert any("Selamat datang" in element.value for element in app.markdown)
    assert any("auth-promo" in element.value for element in app.markdown)
    assert any(
        "--cs-main-background: #F8F7FC;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(True).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is True
    assert app.session_state["show_landing"] is False
    assert any(
        "--cs-main-background: #0B0918;" in element.value
        for element in app.markdown
    )

    app.toggle[0].set_value(False).run()

    assert not app.exception
    assert app.session_state["dark_mode"] is False
    assert app.session_state["show_landing"] is False
    assert any(
        "--cs-main-background: #F8F7FC;" in element.value
        for element in app.markdown
    )
