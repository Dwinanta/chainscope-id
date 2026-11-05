"""Shared theme tokens and styling for the ChainScope Streamlit UI."""

import streamlit as st


_THEMES = {
    "light": {
        "main_background": "#F8FAFC",
        "content_background": "#FFFFFF",
        "sidebar_background": "#F1F5F9",
        "primary_text": "#0F172A",
        "secondary_text": "#475569",
        "border": "#CBD5E1",
        "accent": "#7C3AED",
        "accent_rgb": "124, 58, 237",
        "accent_fill": "rgba(124,58,237,.12)",
        "area_fill": "rgba(124,58,237,.10)",
        "accent_secondary": "#9D5CF5",
        "accent_tertiary": "#C4A1FA",
        "market_chart": "#7C3AED",
        "market_chart_fill": "rgba(124,58,237,.10)",
        "input_background": "#FFFFFF",
        "card_background": "#FFFFFF",
        "card_surface": "#FFFFFF",
        "card_radius": "10px",
        "card_shadow": "none",
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
        "hover": "#F1F5F9",
        "active": "#EDE9FE",
        "active_text": "#6D28D9",
        "timeframe_background": "#1E222D",
        "timeframe_border": "#31353F",
        "timeframe_text": "#FAFAFA",
        "timeframe_active": "#7C3AED",
        "timeframe_hover": "#F1F5F9",
        "grid": "#CBD5E1",
        "plotly_template": "plotly_white",
    },
    "dark": {
        "main_background": "#080B14",
        "main_background_gradient": (
            "linear-gradient(135deg, #080B14 0%, #0D1220 50%, #111827 100%)"
        ),
        "content_background": "#0D1220",
        "sidebar_background": "#0D1220",
        "sidebar_background_gradient": (
            "linear-gradient(180deg, #0B1020 0%, #111827 55%, #17132B 100%)"
        ),
        "card_border": "#293247",
        "card_surface": (
            "linear-gradient(145deg, #151B2B 0%, #111827 100%)"
        ),
        "card_radius": "12px",
        "card_shadow": "0 8px 24px rgba(2, 6, 23, 0.18)",
        "chart_area_background": "#0D1220",
        "chart_grid": "rgba(148, 163, 184, 0.10)",
        "primary_text": "#F8FAFC",
        "secondary_text": "#94A3B8",
        "border": "#293247",
        "accent": "#7C3AED",
        "accent_rgb": "124, 58, 237",
        "accent_fill": "rgba(124,58,237,.14)",
        "area_fill": "rgba(124,58,237,.12)",
        "accent_secondary": "#8B5CF6",
        "accent_tertiary": "#A78BFA",
        "purple_soft": "#DDD6FE",
        "blue_primary": "#2563EB",
        "blue_secondary": "#3B82F6",
        "cyan_accent": "#38BDF8",
        "blue_soft": "#BFDBFE",
        "market_chart": "#3B82F6",
        "market_chart_fill": "rgba(59,130,246,.14)",
        "input_background": "#111827",
        "card_background": "#151B2B",
        "positive": "#16A34A",
        "positive_text": "#4ADE80",
        "positive_fill": "rgba(22,163,74,.65)",
        "positive_line": "rgba(22,163,74,.45)",
        "negative": "#DC2626",
        "negative_text": "#F87171",
        "negative_fill": "rgba(220,38,38,.65)",
        "negative_line": "rgba(220,38,38,.45)",
        "warning": "#F59E0B",
        "warning_text": "#FBBF24",
        "info": "#3B82F6",
        "info_text": "#BFDBFE",
        "hover": "#141D30",
        "active": "rgba(124,58,237,.18)",
        "active_text": "#DDD6FE",
        "timeframe_background": "#0D1220",
        "timeframe_border": "#293247",
        "timeframe_text": "#F8FAFC",
        "timeframe_active": "#7C3AED",
        "timeframe_hover": "#2D3445",
        "grid": "#293247",
        "plotly_template": "plotly_dark",
    },
}


def get_theme_palette(is_dark_mode: bool = False) -> dict[str, str]:
    """Return a copy of the active semantic color palette."""
    return dict(_THEMES["dark" if is_dark_mode else "light"])


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
    sidebar_surface = (
        palette["sidebar_background_gradient"]
        if is_dark_mode
        else palette["sidebar_background"]
    )
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
            background: var(--cs-sidebar-surface);
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
        [data-testid="stSidebar"] [data-testid="stButton"] > button {{
            justify-content: flex-start;
            min-height: 34px;
            margin-bottom: 4px;
            padding: 6px 12px;
            border: 0;
            border-radius: 6px;
            color: var(--cs-secondary-text);
            background: transparent;
            font-size: 0.9rem;
            font-weight: 500;
            text-align: left;
            box-shadow: none;
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
        }}
        [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
            color: var(--cs-active-text);
            background: var(--cs-active);
            font-weight: 600;
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
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            color: var(--cs-primary-text);
            background: var(--cs-card-background);
            border-color: var(--cs-border);
            border-radius: 12px;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="select"] > div {{
            color: var(--cs-primary-text);
            background: var(--cs-input-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stNumberInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder,
        [data-baseweb="input"] input::placeholder,
        [data-baseweb="textarea"] textarea::placeholder {{
            color: var(--cs-secondary-text);
            opacity: 1;
        }}
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [data-testid="stPopoverBody"],
        [role="listbox"],
        [role="option"] {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}
        [role="option"]:hover {{ background: var(--cs-hover); }}
        [data-baseweb="tag"] {{
            color: var(--cs-active-text);
            background: var(--cs-active);
            border-color: var(--cs-border);
        }}
        input[type="checkbox"], input[type="radio"] {{ accent-color: var(--cs-accent); }}
        [data-testid="stTabs"] [role="tab"] {{
            color: var(--cs-secondary-text);
        }}
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
            color: var(--cs-accent);
            border-bottom-color: var(--cs-accent);
        }}
        [data-testid="stFileUploader"] section {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}

        [data-testid="stButton"] > button,
        [data-testid="stFormSubmitButton"] > button,
        [data-testid="stLinkButton"] a,
        [data-testid="stDownloadButton"] button {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stButton"] > button:hover,
        [data-testid="stLinkButton"] a:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
            border-color: var(--cs-border);
        }}
        [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
            color: #FFFFFF;
            background: var(--cs-accent);
            border-color: var(--cs-accent);
        }}
        [data-testid="stAlert"] {{
            color: var(--cs-primary-text);
            background: var(--cs-content-background);
            border-color: var(--cs-border);
        }}
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span {{ color: var(--cs-primary-text); }}

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
        }}
        {f"""
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] {{
            box-sizing: border-box;
            width: 100%;
            min-width: 0;
            padding: 3px;
            color: #FFFFFF;
            background: var(--cs-timeframe-background);
            border: 1px solid var(--cs-timeframe-border);
            border-radius: 8px;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"] {{
            min-width: 0;
            color: #FFFFFF !important;
            background: transparent !important;
            font-weight: 500;
            white-space: nowrap;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"] * {{
            color: #FFFFFF !important;
            background: transparent !important;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"]:hover {{
            color: #FFFFFF !important;
            background: var(--cs-timeframe-hover) !important;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][aria-checked="true"],
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][data-selected="true"] {{
            color: #FFFFFF !important;
            background: var(--cs-timeframe-active) !important;
            font-weight: 700;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][aria-checked="true"]:hover,
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"][data-selected="true"]:hover {{
            background: var(--cs-timeframe-active) !important;
        }}
        .st-key-overview_timeframe [data-testid="stButtonGroup"] [role="radiogroup"] > button[role="radio"]:focus-visible {{
            outline: 2px solid var(--cs-accent);
            outline-offset: 2px;
            box-shadow: 0 0 0 3px rgba(var(--cs-accent-rgb), 0.3);
            z-index: 1;
        }}
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stPopover"],
        [data-testid="stPopoverBody"],
        [data-testid="stMetric"],
        [data-testid="stAlert"],
        .cs-theme-card,
        .landing-card {{
            background: var(--cs-card-surface);
            border-color: var(--cs-card-border);
            border-radius: var(--cs-card-radius);
            box-shadow: var(--cs-card-shadow);
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            box-shadow: var(--cs-card-shadow);
        }}
        [data-testid="stSidebar"] {{
            background: var(--cs-sidebar-background-gradient);
            border-right-color: var(--cs-card-border);
        }}
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebar"] section {{ background: transparent; }}
        [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {{
            background: rgba(var(--cs-accent-rgb), 0.14);
            border: 1px solid var(--cs-card-border);
        }}
        [data-testid="stSidebar"] .st-key-btn_market-overview [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stSidebar"] .st-key-btn_market-data [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stSidebar"] .st-key-btn_relative-strategy [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stSidebar"] .st-key-btn_technical-analysis [data-testid="stButton"] > button[kind="primary"] {{
            color: var(--cs-blue-soft);
            background: rgba(37, 99, 235, 0.16);
            border: 1px solid rgba(59, 130, 246, 0.32);
        }}
        .logo-container > div:first-child {{
            background: linear-gradient(135deg, #7C3AED, #4F46E5) !important;
        }}
        [data-testid="stButton"] > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
            background: linear-gradient(135deg, #7C3AED, #4F46E5);
            border-color: #7C3AED;
        }}
        [data-testid="stButton"] > button[kind="primary"]:hover,
        [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
            filter: brightness(1.08);
        }}
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {{
            background: linear-gradient(180deg, rgba(8, 11, 20, 0.72), transparent);
        }}
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background: var(--cs-content-background);
            border-color: var(--cs-card-border);
        }}
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-baseweb="select"]:focus-within {{
            border-color: rgba(var(--cs-accent-rgb), 0.55);
            box-shadow: 0 0 0 1px rgba(var(--cs-accent-rgb), 0.18);
        }}
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
            border-bottom-color: var(--cs-accent-tertiary);
        }}
        .st-key-crypto_news [data-testid="stLinkButton"] a {{
            color: #FAFAFA !important;
            background: var(--cs-card-surface);
            border-color: var(--cs-card-border);
            border-radius: var(--cs-card-radius);
            box-shadow: var(--cs-card-shadow);
        }}
        .st-key-crypto_news [data-testid="stLinkButton"] a *,
        .st-key-crypto_news [data-testid="stLinkButton"] a p,
        .st-key-crypto_news [data-testid="stLinkButton"] a span {{
            color: #FAFAFA !important;
            background-color: transparent !important;
        }}
        .st-key-crypto_news [data-testid="stLinkButton"] a:hover {{
            color: var(--cs-primary-text);
            background: var(--cs-hover);
        }}
        .st-key-crypto_news [data-testid="stLinkButton"] a:focus-visible {{
            outline: 2px solid var(--cs-accent);
            outline-offset: 2px;
        }}
        .st-key-crypto_news ::selection {{
            color: var(--cs-primary-text);
            background: rgba(var(--cs-accent-rgb), 0.32);
        }}
        """ if is_dark_mode else ""}
        </style>
        """,
        unsafe_allow_html=True,
    )
