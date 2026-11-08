"""Shared theme tokens and styling for the ChainScope Streamlit UI."""

from html import escape
from urllib.parse import urlparse

import streamlit as st


_THEMES = {
    "light": {
        "main_background": "#F8F7FC",
        "content_background": "#FFFFFF",
        "sidebar_background": "#FFFFFF",
        "primary_text": "#181329",
        "secondary_text": "#6B7280",
        "border": "#E5E1EF",
        "card_border": "#E5E1EF",
        "accent": "#7C3AED",
        "accent_rgb": "124, 58, 237",
        "accent_fill": "rgba(124,58,237,.12)",
        "area_fill": "rgba(124,58,237,.10)",
        "accent_secondary": "#9333EA",
        "accent_tertiary": "#C4A1FA",
        "blue_secondary": "#3B82F6",
        "purple_soft": "#6D28D9",
        "blue_primary": "#3B82F6",
        "cyan_accent": "#22D3EE",
        "blue_soft": "#1D4ED8",
        "market_chart": "#7C3AED",
        "market_chart_fill": "rgba(124,58,237,.10)",
        "input_background": "#FFFFFF",
        "card_background": "#FFFFFF",
        "card_surface": "#FFFFFF",
        "card_radius": "10px",
        "card_shadow": "none",
        "chart_area_background": "#FFFFFF",
        "chart_grid": "#E5E1EF",
        "positive": "#16A34A",
        "positive_text": "#15803D",
        "positive_fill": "rgba(22,163,74,.65)",
        "positive_line": "rgba(22,163,74,.45)",
        "negative": "#DC2626",
        "negative_text": "#B91C1C",
        "negative_fill": "rgba(220,38,38,.65)",
        "negative_line": "rgba(220,38,38,.45)",
        "warning": "#F59E0B",
        "warning_text": "#B45309",
        "info": "#3B82F6",
        "info_text": "#1D4ED8",
        "hover": "#F3F0FA",
        "active": "#EDE9FE",
        "active_text": "#6D28D9",
        "timeframe_background": "#FFFFFF",
        "timeframe_border": "#E5E1EF",
        "timeframe_text": "#6B7280",
        "timeframe_active": "#7C3AED",
        "timeframe_hover": "#F3F0FA",
        "grid": "#E5E1EF",
        "plotly_template": "plotly_white",
    },
    "dark": {
        "main_background": "#0B0918",
        "main_background_gradient": (
            "linear-gradient(135deg, #0B0918 0%, #100D22 52%, #15102A 100%)"
        ),
        "content_background": "#0B0918",
        "sidebar_background": "#100D22",
        "sidebar_background_gradient": (
            "linear-gradient(180deg, #0B0918 0%, #121027 58%, #19152F 100%)"
        ),
        "card_border": "rgba(139, 92, 246, 0.25)",
        "card_surface": (
            "linear-gradient(145deg, #19152F 0%, #141127 100%)"
        ),
        "card_radius": "12px",
        "card_shadow": "0 10px 28px rgba(2, 6, 23, 0.24)",
        "chart_area_background": "#121027",
        "chart_grid": "rgba(161, 161, 170, 0.12)",
        "primary_text": "#F8FAFC",
        "secondary_text": "#A1A1AA",
        "border": "rgba(139, 92, 246, 0.25)",
        "accent": "#7C3AED",
        "accent_rgb": "124, 58, 237",
        "accent_fill": "rgba(124,58,237,.14)",
        "area_fill": "rgba(124,58,237,.12)",
        "accent_secondary": "#9333EA",
        "accent_tertiary": "#C084FC",
        "purple_soft": "#DDD6FE",
        "blue_primary": "#3B82F6",
        "blue_secondary": "#3B82F6",
        "cyan_accent": "#22D3EE",
        "blue_soft": "#BFDBFE",
        "market_chart": "#3B82F6",
        "market_chart_fill": "rgba(59,130,246,.14)",
        "input_background": "#211B38",
        "card_background": "#19152F",
        "positive": "#10B981",
        "positive_text": "#34D399",
        "positive_fill": "rgba(16,185,129,.65)",
        "positive_line": "rgba(16,185,129,.45)",
        "negative": "#F43F5E",
        "negative_text": "#FB7185",
        "negative_fill": "rgba(244,63,94,.65)",
        "negative_line": "rgba(244,63,94,.45)",
        "warning": "#F59E0B",
        "warning_text": "#FBBF24",
        "info": "#3B82F6",
        "info_text": "#BFDBFE",
        "hover": "#211B3C",
        "active": "rgba(124,58,237,.18)",
        "active_text": "#DDD6FE",
        "timeframe_background": "#121027",
        "timeframe_border": "rgba(139, 92, 246, 0.25)",
        "timeframe_text": "#F8FAFC",
        "timeframe_active": "#7C3AED",
        "timeframe_hover": "#211B3C",
        "grid": "rgba(139, 92, 246, 0.25)",
        "plotly_template": "plotly_dark",
    },
}


def get_theme_palette(is_dark_mode: bool = False) -> dict[str, str]:
    """Return a copy of the active semantic color palette."""
    return dict(_THEMES["dark" if is_dark_mode else "light"])


def render_coin_logo(
    coin_id: str,
    image_url: str | None,
    size: int = 28,
    symbol: str = "",
) -> str:
    """Return a compact logo element with an asset-specific text fallback."""
    if size <= 0:
        raise ValueError("Ukuran logo koin harus lebih besar dari nol.")

    safe_id = escape(coin_id, quote=True)
    safe_symbol = escape(symbol.strip().upper() or coin_id[:3].upper(), quote=True)
    fallback = (
        f'<span class="cs-coin-logo-fallback" aria-hidden="true">{safe_symbol}</span>'
    )
    safe_image_url = image_url if isinstance(image_url, str) else ""
    parsed_url = urlparse(safe_image_url)
    host = parsed_url.hostname or ""
    if (
        parsed_url.scheme == "https"
        and (host == "coingecko.com" or host.endswith(".coingecko.com"))
    ):
        safe_url = escape(safe_image_url, quote=True)
        image = (
            f'<img src="{safe_url}" alt="{safe_symbol} logo" loading="lazy" '
            'onerror="this.hidden=true;this.nextElementSibling.hidden=false">'
        )
        fallback = fallback.replace(
            'class="cs-coin-logo-fallback" aria-hidden="true"',
            'class="cs-coin-logo-fallback" aria-hidden="true" hidden',
        )
    else:
        image = ""
    return (
        f'<span class="cs-coin-logo" data-coin-id="{safe_id}" '
        f'style="width:{size}px;height:{size}px" role="img" '
        f'aria-label="{safe_symbol} logo">{image}{fallback}</span>'
    )


def apply_plotly_theme(figure, is_dark_mode: bool = False):
    """Apply the active theme to a Plotly figure without hiding its traces."""
    palette = get_theme_palette(is_dark_mode)
    plot_background = (
        palette["chart_area_background"]
        if is_dark_mode
        else "rgba(0,0,0,0)"
    )
    grid_color = palette.get("chart_grid", palette["grid"])
    figure.update_layout(
        template=palette["plotly_template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_background,
        font={"color": palette["primary_text"]},
        legend={"font": {"color": palette["primary_text"]}},
        xaxis={
            "gridcolor": grid_color,
            "linecolor": palette["border"],
            "tickfont": {"color": palette["secondary_text"]},
            "title_font": {"color": palette["secondary_text"]},
        },
        yaxis={
            "gridcolor": grid_color,
            "linecolor": palette["border"],
            "tickfont": {"color": palette["secondary_text"]},
            "title_font": {"color": palette["secondary_text"]},
        },
    )
    return figure


def style_dataframe(dataframe, is_dark_mode: bool = False):
    """Style dataframe cells explicitly so tables follow runtime theme changes."""
    palette = get_theme_palette(is_dark_mode)
    return dataframe.style.set_properties(
        **{
            "background-color": palette["content_background"],
            "color": palette["primary_text"],
            "border-color": palette["border"],
        }
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("background-color", palette["sidebar_background"]),
                    ("color", palette["primary_text"]),
                    ("border-color", palette["border"]),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("background-color", palette["content_background"]),
                    ("color", palette["primary_text"]),
                    ("border-color", palette["border"]),
                ],
            },
        ],
        overwrite=False,
    )


def apply_theme(is_dark_mode: bool = False) -> None:
    """Apply the centralized light or dark theme to the current Streamlit run."""
    palette = get_theme_palette(is_dark_mode)
    app_background = (
        palette["main_background_gradient"]
        if is_dark_mode
        else palette["main_background"]
    )
    sidebar_surface = palette["sidebar_background"]
    css_variables = "\n".join(
        f"        --cs-{name.replace('_', '-')}: {value};"
        for name, value in palette.items()
        if name != "plotly_template"
    )
    css_variables += f"\n        --cs-sidebar-surface: {sidebar_surface};"
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            color-scheme: {"dark" if is_dark_mode else "light"};
{css_variables}
        }}

        .stApp {{
            background: {app_background} !important;
            background-attachment: fixed;
            color-scheme: {"dark" if is_dark_mode else "light"};
        }}
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background: transparent;
            color: var(--cs-primary-text);
            font-family: 'Inter', sans-serif;
        }}
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {{ background: transparent; }}
        .block-container {{
            max-width: 100%;
            padding: 0.5rem 2rem 0;
        }}

        [data-testid="stSidebar"] {{
            background: var(--cs-sidebar-background);
            border-right: 1px solid var(--cs-border);
        }}
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebar"] section {{
            background: transparent;
        }}
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 0;
            margin-top: 0;
        }}
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {{
            color: var(--cs-primary-text);
            background: var(--cs-sidebar-surface);
            border: 1px solid var(--cs-border);
            border-radius: 8px;
        }}
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 0; }}
        [data-testid="stSidebar"] [data-testid="stSelectbox"] {{
            margin-top: -0.5rem;
        }}
        .logo-container {{
            display: flex;
            align-items: center;
            gap: 8px;
            position: relative;
            z-index: 10;
            margin: -3.5rem 0 1.5rem;
            padding-left: 10px;
        }}
        .sidebar-divider {{
            border-color: var(--cs-border);
            margin: 0.75rem 0;
        }}
        .sidebar-profile {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 1.25rem 0.25rem 0.5rem;
            padding: 12px;
            border: 1px solid var(--cs-border);
            border-radius: 12px;
            background: var(--cs-card-surface);
        }}
        .sidebar-profile-avatar {{
            display: grid;
            flex: 0 0 34px;
            width: 34px;
            height: 34px;
            place-items: center;
            border-radius: 50%;
            color: #FFFFFF;
            background: linear-gradient(135deg, var(--cs-accent), var(--cs-blue-secondary, #3B82F6));
            font-size: 0.85rem;
            font-weight: 800;
        }}
        .sidebar-profile-copy {{
            display: flex;
            min-width: 0;
            flex-wrap: wrap;
            align-items: center;
            gap: 5px;
        }}
        .sidebar-profile-copy strong {{
            width: 100%;
            overflow: hidden;
            color: var(--cs-primary-text);
            font-size: 0.76rem;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .profile-badge {{
            padding: 2px 7px;
            border: 1px solid rgba(var(--cs-accent-rgb), 0.25);
            border-radius: 999px;
            color: var(--cs-active-text);
            background: var(--cs-active);
            font-size: 0.6rem;
            font-weight: 800;
            letter-spacing: 0.06em;
        }}
        .admin-badge {{
            border-color: rgba(245, 158, 11, 0.3);
            color: var(--cs-warning-text);
            background: rgba(245, 158, 11, 0.12);
        }}
        .cs-coin-logo {{
            display: inline-flex;
            flex: 0 0 auto;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            border: 1px solid var(--cs-border);
            border-radius: 50%;
            color: var(--cs-accent);
            background: var(--cs-active);
            vertical-align: middle;
        }}
        .cs-coin-logo img {{
            display: block;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .cs-coin-logo-fallback {{
            font-size: 0.55em;
            font-weight: 800;
            line-height: 1;
        }}
        .stApp h1 {{
            font-size: clamp(1.65rem, 2.4vw, 2.15rem);
            font-weight: 750;
            letter-spacing: -0.035em;
        }}
        .stApp h2, .stApp h3, .stApp h4 {{
            letter-spacing: -0.02em;
        }}
        .page-subtitle {{
            margin-top: -0.2rem;
            color: var(--cs-secondary-text);
            font-size: 0.78rem;
            font-weight: 650;
            letter-spacing: 0.07em;
        }}
        .overview-metric {{
            overflow-wrap: anywhere;
            color: var(--cs-primary-text);
            font-size: clamp(1.15rem, 1.6vw, 1.65rem);
            font-weight: 750;
            letter-spacing: -0.035em;
            line-height: 1.25;
        }}
        .mover-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-bottom: 9px;
        }}
        .mover-asset {{
            display: flex;
            min-width: 0;
            align-items: center;
            gap: 7px;
        }}
        .mover-symbol {{ color: var(--cs-primary-text); font-size: 0.75rem; font-weight: 700; }}
        .mover-price {{ color: var(--cs-secondary-text); font-size: 0.68rem; }}
        .selected-assets {{
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 0.25rem 0 0.75rem;
            color: var(--cs-secondary-text);
            font-size: 0.88rem;
        }}
        .selected-assets strong {{ color: var(--cs-primary-text); }}
        .asset-pair-divider, .asset-symbol {{ color: var(--cs-secondary-text); }}
        [data-testid="stSidebar"] [data-testid="stButton"] > button {{
            justify-content: flex-start;
            min-height: 40px;
            margin-bottom: 4px;
            padding: 7px 12px;
            border: 0;
            border-radius: 9px;
            color: var(--cs-secondary-text);
            background: transparent;
            font-size: 0.9rem;
            font-weight: 500;
            text-align: left;
            box-shadow: none;
            transition: color 160ms ease, background 160ms ease, transform 160ms ease;
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
            transform: translateX(2px);
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
            color: #FFFFFF;
            background: linear-gradient(110deg, var(--cs-accent), var(--cs-accent-secondary));
            font-weight: 600;
            box-shadow: 0 5px 16px rgba(var(--cs-accent-rgb), 0.22);
        }}

        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp p, .stApp li, .stApp label,
        [data-testid="stMarkdownContainer"],
        [data-testid="stWidgetLabel"],
        [data-testid="stCaptionContainer"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {{
            color: var(--cs-primary-text);
        }}
        [data-testid="stCaptionContainer"] {{ color: var(--cs-secondary-text); }}
        .stApp a, [data-testid="stLinkButton"] a {{ color: var(--cs-accent); }}
        .text-green {{ color: var(--cs-positive-text); font-weight: 700; }}
        .text-red {{ color: var(--cs-negative-text); font-weight: 700; }}

        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stPopover"],
        [data-testid="stDialog"],
        [data-testid="stPopoverBody"],
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        .cs-theme-card {{
            color: var(--cs-primary-text);
            background: var(--cs-card-surface);
            border-color: var(--cs-card-border);
            border-radius: var(--cs-card-radius);
            box-shadow: var(--cs-card-shadow);
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            transition: border-color 160ms ease, box-shadow 160ms ease;
        }}
        [data-testid="stVerticalBlockBorderWrapper"]:hover {{
            border-color: var(--cs-accent);
            box-shadow: 0 8px 24px rgba(var(--cs-accent-rgb), 0.08);
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
            color: var(--cs-primary-text);
            background: var(--cs-input-background);
            border-color: var(--cs-border);
            color-scheme: {"dark" if is_dark_mode else "light"};
        }}
        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stMultiSelect"] [data-baseweb="select"] {{
            color: var(--cs-primary-text);
        }}
        [data-testid="stNumberInput"] button {{
            color: var(--cs-secondary-text);
            background: var(--cs-input-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stNumberInput"] button:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
        }}
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stNumberInput"] input::placeholder,
        [data-testid="stDateInput"] input::placeholder,
        [data-testid="stTimeInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder,
        [data-baseweb="input"] input::placeholder,
        [data-baseweb="textarea"] textarea::placeholder {{
            color: var(--cs-secondary-text);
            opacity: 1;
        }}
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [data-baseweb="calendar"],
        [data-baseweb="datepicker"],
        [data-testid="stPopoverBody"],
        [data-testid="stDateInput"] [role="dialog"],
        [role="listbox"] {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stDateInput"] [data-baseweb="calendar"] *,
        [data-baseweb="datepicker"] * {{
            color: var(--cs-primary-text);
        }}
        [data-testid="stDateInput"] [data-baseweb="calendar"] button,
        [data-baseweb="datepicker"] button {{
            color: var(--cs-secondary-text);
            background: transparent;
        }}
        [data-testid="stDateInput"] [data-baseweb="calendar"] button:hover,
        [data-baseweb="datepicker"] button:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
        }}
        [role="option"] {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
        }}
        [role="option"]:hover,
        [role="option"][aria-selected="true"] {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
        }}
        [data-baseweb="tag"] {{
            color: var(--cs-active-text);
            background: var(--cs-active);
            border-color: var(--cs-border);
        }}
        input[type="checkbox"], input[type="radio"] {{ accent-color: var(--cs-accent); }}
        input[type="range"] {{ accent-color: var(--cs-accent); }}
        [data-testid="stSlider"] [role="slider"] {{
            border-color: var(--cs-accent);
            background: var(--cs-accent);
        }}
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label,
        [data-testid="stSlider"] label {{
            color: var(--cs-primary-text);
        }}
        [data-testid="stTabs"] [role="tab"] {{
            color: var(--cs-secondary-text);
        }}
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
            color: var(--cs-accent);
            border-bottom-color: var(--cs-accent);
        }}
        [data-testid="stFileUploader"] section {{
            color: var(--cs-primary-text);
            background: var(--cs-input-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
            color: var(--cs-primary-text);
            background: var(--cs-input-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] * {{
            color: var(--cs-primary-text);
        }}
        [data-testid="stFileUploader"] button {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stFileUploader"] button:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
        }}

        [data-testid="stButton"] > button,
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="stLinkButton"] a,
        [data-testid="stDownloadButton"] button {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
            transition: color 160ms ease, background 160ms ease, border-color 160ms ease;
        }}
        [data-testid="stButton"] > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover,
        [data-testid="stLinkButton"] a:hover,
        [data-testid="stDownloadButton"] button:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
            border-color: var(--cs-border);
        }}
        [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
            color: #FFFFFF;
            background: linear-gradient(135deg, var(--cs-accent), var(--cs-blue-secondary));
            border-color: var(--cs-accent);
        }}
        [data-testid="stButton"] > button[kind="primary"]:hover,
        [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
            filter: brightness(1.08);
        }}
        [data-testid="stButton"] > button:disabled,
        [data-testid="stFormSubmitButton"] > button:disabled,
        [data-testid="stDownloadButton"] button:disabled,
        [data-testid="stFileUploader"] button:disabled,
        [data-testid="stNumberInput"] button:disabled {{
            color: var(--cs-secondary-text);
            background: var(--cs-hover);
            border-color: var(--cs-border);
            opacity: 0.55;
            cursor: not-allowed;
        }}
        [data-testid="stButton"] > button:focus-visible,
        [data-testid="stFormSubmitButton"] > button:focus-visible,
        [data-testid="stLinkButton"] a:focus-visible,
        [data-testid="stDownloadButton"] button:focus-visible,
        [data-testid="stFileUploader"] button:focus-visible {{
            outline: 2px solid var(--cs-blue-secondary);
            outline-offset: 2px;
        }}
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stTimeInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
        [data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within {{
            border-color: var(--cs-accent);
            box-shadow: 0 0 0 1px var(--cs-accent);
        }}
        [data-testid="stTextInput"] input:disabled,
        [data-testid="stNumberInput"] input:disabled,
        [data-testid="stDateInput"] input:disabled,
        [data-testid="stTimeInput"] input:disabled,
        [data-testid="stTextArea"] textarea:disabled {{
            color: var(--cs-secondary-text);
            background: var(--cs-hover);
            opacity: 0.65;
            cursor: not-allowed;
        }}
        [data-testid="stMetric"] {{
            color: var(--cs-primary-text);
            background: var(--cs-card-surface);
            border: 1px solid var(--cs-card-border);
            border-radius: var(--cs-card-radius);
            padding: 0.75rem;
        }}
        [data-testid="stProgress"] [role="progressbar"] > div {{
            background: linear-gradient(90deg, var(--cs-accent), var(--cs-blue-secondary));
        }}
        [data-testid="stSpinner"] {{
            color: var(--cs-secondary-text);
        }}
        [data-testid="stAlert"],
        [data-testid="stToast"] {{
            color: var(--cs-primary-text);
            background: var(--cs-card-surface);
            border-color: var(--cs-border);
        }}
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stToast"] p,
        [data-testid="stToast"] span {{ color: var(--cs-primary-text); }}

        .landing-hero {{ text-align: center; padding: 0.45rem 0 0.2rem; }}
        .landing-hero h1 {{
            color: var(--cs-primary-text);
            font-size: 2.25rem;
            line-height: 1.15;
            margin: 0.25rem 0 0.45rem;
        }}
        .landing-hero p, .landing-card p {{ color: var(--cs-secondary-text); }}
        .landing-section-title {{
            color: var(--cs-primary-text);
            font-size: 1.1rem;
            font-weight: 700;
            text-align: center;
            margin: 0.6rem 0 0.4rem;
        }}
        .landing-card {{
            color: var(--cs-primary-text);
            background: var(--cs-card-background);
            border: 1px solid var(--cs-border);
            border-radius: 14px;
            padding: 0.75rem 1rem;
            min-height: 94px;
        }}
        .landing-card h3 {{ color: var(--cs-primary-text); font-size: 1rem; }}
        .landing-card p {{ font-size: 0.88rem; margin: 0; }}
        .landing-price {{ min-height: 118px; text-align: center; }}
        .landing-price .price {{
            color: var(--cs-accent);
            font-size: 1.4rem;
            font-weight: 800;
            margin: 0.25rem 0;
        }}
        .landing-footer {{
            color: var(--cs-secondary-text);
            font-size: 0.75rem;
            text-align: center;
            padding-top: 0.4rem;
        }}
        .st-key-forgot_password button {{
            color: var(--cs-accent);
            background: transparent;
            border: 0;
            text-decoration: underline;
        }}
        .st-key-back_to_landing {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            width: auto;
        }}
        .st-key-back_to_landing button {{
            color: var(--cs-secondary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}

        .stApp ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        .stApp ::-webkit-scrollbar-track {{ background: var(--cs-main-background); }}
        .stApp ::-webkit-scrollbar-thumb {{
            background: var(--cs-border);
            border-radius: 9999px;
        }}

        @media (max-width: 768px) {{
            .block-container {{
                width: 100%;
                max-width: 100vw;
                padding-left: 1rem;
                padding-right: 1rem;
                box-sizing: border-box;
            }}
            [data-testid="stMain"] {{ max-width: 100vw; overflow-x: hidden; }}
            [data-testid="stSidebar"] {{ max-width: 85vw; box-sizing: border-box; }}
            [data-testid="stSidebar"] > div:first-child {{
                padding: 2.5rem 0.75rem 0.75rem;
            }}
            [data-testid="stSidebarCollapseButton"],
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="collapsedControl"] {{
                position: fixed;
                top: 10px;
                left: 10px;
                z-index: 9999;
            }}
            .logo-container {{ margin-top: 0.5rem; }}
            .stApp h1 {{ font-size: 1.65rem; }}
            [data-testid="stDataFrame"] {{ max-width: 100%; overflow-x: auto; }}
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] {{
            box-sizing: border-box;
            width: 100%;
            min-width: 0;
            padding: 3px;
            color: var(--cs-timeframe-text);
            background: var(--cs-timeframe-background);
            border: 1px solid var(--cs-timeframe-border);
            border-radius: 8px;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"] {{
            min-width: 0;
            color: var(--cs-timeframe-text);
            background: transparent;
            font-weight: 500;
            white-space: nowrap;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"] * {{
            color: inherit;
            background: transparent;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"]:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-timeframe-hover);
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][aria-checked="true"],
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][data-selected="true"] {{
            color: #FFFFFF;
            background: var(--cs-timeframe-active);
            font-weight: 700;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][aria-checked="true"]:hover,
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][data-selected="true"]:hover {{
            background: var(--cs-timeframe-active);
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"]:focus-visible {{
            outline: 2px solid var(--cs-accent);
            outline-offset: 2px;
            box-shadow: 0 0 0 3px rgba(var(--cs-accent-rgb), 0.3);
            z-index: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
