"""Streamlit component for the standalone personal finance tracker."""

from pathlib import Path

import streamlit as st

from chainscope import ui


@st.cache_data(ttl=3600, max_entries=1, show_spinner=False)
def _load_personal_wallet_template() -> str:
    html_path = Path(__file__).with_name("personal_wallet.html")
    return html_path.read_text(encoding="utf-8")


def render_personal_wallet(dark_mode: bool = False) -> None:
    """Render the AturUang tracker using the active app theme."""
    html_content = _load_personal_wallet_template()
    theme_name = "dark" if dark_mode else "light"
    html_content = html_content.replace("__INITIAL_THEME__", theme_name)
    dark_theme_style = ""
    if dark_mode:
        palette = ui.get_theme_palette(is_dark_mode=True)
        dark_theme_style = f"""
        html.dark body.bg-slate-50 {{
            background: {palette["main_background_gradient"]};
        }}
        html.dark body.bg-slate-50 header,
        html.dark body.bg-slate-50 main section,
        html.dark body.bg-slate-50 #deleteModal > div {{
            background: {palette["card_surface"]};
            border-color: {palette["card_border"]};
            box-shadow: 0 12px 32px rgba(2, 6, 23, 0.24);
        }}
        html.dark body.bg-slate-50 input,
        html.dark body.bg-slate-50 select,
        html.dark body.bg-slate-50 textarea {{
            color: {palette["primary_text"]};
            background: {palette["input_background"]};
            border-color: {palette["border"]};
        }}
        html.dark body.bg-slate-50 input::placeholder,
        html.dark body.bg-slate-50 textarea::placeholder {{
            color: {palette["secondary_text"]};
        }}
        html.dark body.bg-slate-50 table thead {{
            background: {palette["content_background"]};
        }}
        html.dark body.bg-slate-50 #financeChart {{
            background: {palette["chart_area_background"]};
            border-radius: 0.75rem;
        }}
        """
    html_content = html_content.replace("__DARK_THEME_STYLE__", dark_theme_style)
    st.iframe(
        html_content,
        height=1000,
        alt="AturUang personal finance tracker",
    )
