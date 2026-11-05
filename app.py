"""
ChainScope ID - Premium Light Mode (Full Features & Indodax Chart)
"""
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from google.api_core.exceptions import GoogleAPIError

from chainscope import (
    ui, api, auth, compare, config, converter, db, formatting,
    indicators, journal_calc, report, search, telegram, admin, payment,
    ai_assistant,
)

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="ChainScope ID",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
# 2. CEK AUTENTIKASI
auth.check_session()
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "show_landing" not in st.session_state:
    st.session_state.show_landing = True

if "user" not in st.session_state or st.session_state.user is None:
    dark_mode = st.toggle("Dark Mode", key="dark_mode")
    ui.apply_theme(dark_mode)
    if st.session_state.show_landing:
        st.markdown(
            """
            <style>
            .block-container {
                max-width: 1100px !important;
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="landing-hero">
                <div style="font-size:2rem;">⚡</div>
                <h1>ChainScope ID - Platform Analitik Crypto Terlengkap</h1>
                <p>Analisis teknikal dengan RSI dan MA, portofolio otomatis, serta notifikasi Telegram untuk membantu Anda memantau pasar kripto.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _, cta_col, _ = st.columns([1.5, 1, 1.5])
        with cta_col:
            if st.button(
                "Mulai Gratis",
                type="primary",
                width='stretch',
                key="landing_get_started",
            ):
                st.session_state.show_landing = False
                st.rerun()

        st.markdown(
            "<div class='landing-section-title'>Fitur Unggulan</div>",
            unsafe_allow_html=True,
        )
        feature_cols = st.columns(3)
        features = [
            (
                "📉",
                "Analisis Teknikal Interaktif",
                "Analisis pergerakan harga dengan RSI, MA, dan indikator teknikal lainnya.",
            ),
            (
                "💼",
                "Portofolio Otomatis",
                "Catat transaksi dan pantau nilai serta kinerja aset Anda.",
            ),
            (
                "🔔",
                "Notifikasi Telegram",
                "Terima alert harga langsung melalui Telegram.",
            ),
        ]
        for column, (icon, title, description) in zip(feature_cols, features):
            with column:
                st.markdown(
                    f"<div class='landing-card'><h3>{icon} {title}</h3>"
                    f"<p>{description}</p></div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div class='landing-section-title'>Pilih Paket Anda</div>",
            unsafe_allow_html=True,
        )
        pricing_cols = st.columns(2)
        plans = [
            ("Free", "Gratis", "Akses fitur utama untuk mulai memantau pasar."),
            ("Premium", "Rp 50.000/bulan", "Akses penuh ke fitur ChainScope ID, laporan PDF, dan alert tanpa batas."),
        ]
        for column, (plan_name, price, description) in zip(pricing_cols, plans):
            with column:
                st.markdown(
                    f"<div class='landing-card landing-price'><h3>{plan_name}</h3>"
                    f"<div class='price'>{price}</div><p>{description}</p></div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Pilih Paket",
                    type="primary",
                    width='stretch',
                    key=f"landing_plan_{plan_name.lower()}",
                ):
                    st.session_state.show_landing = False
                    st.rerun()

        st.markdown(
            "<div class='landing-footer'>© 2026 ChainScope ID. Dibuat untuk trader Indonesia.</div>",
            unsafe_allow_html=True,
        )
    else:
        if st.button("← Kembali ke halaman depan", key="back_to_landing"):
            st.session_state.show_landing = True
            st.rerun()
        auth.show_auth_page()
    st.stop()

user = st.session_state.user
user_profile = db.get_user_profile(user.id)
is_dev = user_profile.get("role") == "dev"
sub_tier = user_profile.get("subscription_tier", "free").title()
end_date = user_profile.get("subscription_end")
if "language" not in st.session_state:
    st.session_state.language = "EN"

# 3. FUNGSI CACHE API
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_market_data(vs_currency: str) -> pd.DataFrame:
    return api.fetch_market_data(vs_currency, 250)

@st.cache_data(ttl=86400, show_spinner=False)
def cached_all_coins() -> list[dict[str, str]]:
    return api.fetch_all_coins()

@st.cache_data(ttl=300, show_spinner=False)
def cached_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_price_history(coin_id, vs_currency, days)

@st.cache_data(ttl=60, show_spinner=False)
def cached_indodax_klines(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    return api.fetch_indodax_klines(symbol, interval, limit)

@st.cache_data(ttl=300, show_spinner=False)
def cached_fear_greed_index() -> dict[str, str]:
    return api.fetch_fear_greed_index()

@st.cache_data(ttl=300, show_spinner=False)
def cached_crypto_news() -> list[dict[str, str]]:
    return api.fetch_crypto_news(limit=5)

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_usd_currency_rate(currency: str) -> float:
    """Return units of the selected currency per USD using CoinGecko prices."""
    target_currency = currency.lower()
    if target_currency == "usd":
        return 1.0
    df_usd = api.fetch_market_data("usd", 1)
    df_target = api.fetch_market_data(target_currency, 1)
    if df_usd.empty or df_target.empty:
        raise api.ChainScopeAPIError("Kurs mata uang tidak tersedia dari CoinGecko.")

    usd_price = float(df_usd.iloc[0]["current_price"])
    target_price = float(df_target.iloc[0]["current_price"])
    if usd_price <= 0 or target_price <= 0:
        raise api.ChainScopeAPIError("Kurs mata uang dari CoinGecko tidak valid.")
    return target_price / usd_price

# 4. SIDEBAR & NAVIGASI
if "current_page" not in st.session_state:
    st.session_state.current_page = "market-overview"

with st.sidebar:
    st.markdown("""
        <div class='logo-container'>
            <div style='background: var(--cs-accent); padding: 6px 10px; border-radius: 8px;'>
                <span style='color:white; font-size:1.2rem;'>⚡</span>
            </div>
            <span style='font-size:1.2rem; font-weight:800; color:var(--cs-primary-text);'>ChainScope <span style='color:var(--cs-accent);'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-color: var(--cs-border);'>", unsafe_allow_html=True)

    language = st.radio(
        config.translate(st.session_state.language, "Language"),
        ["ID", "EN"],
        horizontal=True,
        key="language",
    )
    dark_mode =     st.toggle(
        config.translate(language, "Dark Mode"),
        key="dark_mode",
    )

    menu_config = {
        "market-overview": "🏠 Market Overview",
        "market-data": "📊 Market Data",
        "relative-strategy": "📊 Strategi Relatif",
        "trading-journal": "📒 Trading Journal",
        "price-alerts": "🔔 Price Alerts",
        "pdf-report": "📄 Laporan PDF",
        "technical-analysis": "📉 Technical Analysis",
        "portfolio": "💼 Portfolio",
        "converter": "💱 Converter",
        "watchlist": "⭐ Watchlist",
        "wallet": "💰 Personal Wallet",
    }
    if is_dev:
        menu_config["admin-panel"] = "👑 Admin Panel"

    for url_key, display_name in menu_config.items():
        is_active = (st.session_state.current_page == url_key)
        if st.button(config.translate(language, display_name), width='stretch', key=f"btn_{url_key}", type="primary" if is_active else "secondary"):
            st.session_state.current_page = url_key
            st.rerun()

    currency = st.selectbox(
        "Mata uang:",
        options=list(config.CURRENCY_OPTIONS),
        format_func=lambda code: config.CURRENCY_OPTIONS[code]["label"],
    )

ui.apply_theme(dark_mode)

current_page = st.session_state.current_page
theme_palette = ui.get_theme_palette(dark_mode)

# 5. AMBIL DATA PASAR HANYA UNTUK HALAMAN YANG MEMAKAINYA
data_source = "LIVE"
market_df = pd.DataFrame()
if current_page != "wallet":
    try:
        market_df = cached_market_data(currency)
    except api.ChainScopeAPIError:
        st.error("Gagal mengambil data dari CoinGecko.")
        st.stop()

    market_df = market_df.copy()
    try:
        all_coins = pd.DataFrame(cached_all_coins())
    except api.ChainScopeAPIError:
        st.error("Gagal mengambil data dari CoinGecko.")
        st.stop()

    if not all_coins.empty:
        market_df = api.merge_market_and_coin_list(market_df, all_coins)

    market_df["symbol_upper"] = market_df["symbol"].astype(str).str.upper()
    market_df["label"] = market_df["name"] + " (" + market_df["symbol_upper"] + ")"

# ===========================================================================
# ROUTING HALAMAN
# ===========================================================================
if current_page == "market-overview":
    col_title, col_search, col_profile = st.columns([2.5, 2, 0.5], vertical_alignment="center")
    with col_title:
        st.markdown(
            f"<h1>{config.translate(language, 'Market Overview')}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown("<p style='font-size:0.9rem; margin-top:5px;'>Real-time crypto market data and insights</p>", unsafe_allow_html=True)
    with col_search:
        search_query = st.text_input("Search", placeholder="🔍 Search coins...", label_visibility="collapsed")
    with col_profile:
        with st.popover("👤"):
            st.markdown(f"### 👤 {user.email}")
            st.markdown(f"**Plan:** {sub_tier}")
            if end_date: st.markdown(f"**Aktif s/d:** {end_date[:10]}")
            if st.button("🚪 Logout", width='stretch', type="primary"): auth.logout_user()

    st.markdown("<br>", unsafe_allow_html=True)

    top4_df = market_df.head(4)
    cols = st.columns(4)
    for col, (_, row) in zip(cols, top4_df.iterrows()):
        with col:
            with st.container(border=True):
                color = (
                    theme_palette["positive_text"]
                    if row["price_change_percentage_24h"] >= 0
                    else theme_palette["negative_text"]
                )
                icon = "▲" if row['price_change_percentage_24h'] >= 0 else "▼"
                c_left, c_right = st.columns([1.2, 1])
                with c_left:
                    st.markdown(f"""
                    <div style='display:flex; gap:8px; align-items:center;'>
                        <img src="{row['image']}" width="24" height="24">
                        <div>
                            <div style='font-weight:700; font-size:0.85rem; color:var(--cs-primary-text);'>{row['name']}</div>
                            <div style='font-size:0.7rem; color:var(--cs-secondary-text);'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                    <div style='margin-top:15px;'>
                        <div style='font-weight:800; font-size:1.1rem; color:var(--cs-primary-text);'>{formatting.format_money(row['current_price'], currency)}</div>
                        <div style='color:{color}; font-size:0.8rem; font-weight:600;'>{icon} {row['price_change_percentage_24h']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_right:
                    sparkline_prices = row.get("sparkline_in_7d", {}).get("price", [])
                    if sparkline_prices:
                        fig = go.Figure(go.Scatter(y=sparkline_prices, mode='lines', line=dict(color=color, width=1.5)))
                        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=60, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
                        ui.apply_plotly_theme(fig, dark_mode)
                        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

    try:
        fear_greed = cached_fear_greed_index()
    except api.ChainScopeAPIError as exc:
        st.warning(f"Fear & Greed Index sementara tidak tersedia: {exc}")
    else:
        classification = fear_greed["classification"]
        normalized_classification = classification.lower()
        sentiment_color = (
            "var(--cs-positive-text)" if "greed" in normalized_classification
            else "var(--cs-negative-text)" if "fear" in normalized_classification
            else "var(--cs-accent)"
        )
        st.markdown(
            "<div style='display:inline-flex; align-items:center; gap:6px; "
            "padding:8px 12px; margin:4px 0 8px; "
            "border:1px solid var(--cs-card-border, var(--cs-border)); "
            "border-radius:var(--cs-card-radius, 10px); "
            "background:var(--cs-card-surface, var(--cs-content-background)); "
            "box-shadow:var(--cs-card-shadow, none); "
            "color:var(--cs-primary-text); font-size:0.9rem;'>"
            "Fear &amp; Greed: "
            f"<strong style='color:{sentiment_color};'>"
            f"{escape(fear_greed['value'])} ({escape(classification)})</strong></div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Berita Crypto Terbaru")
    try:
        crypto_news = cached_crypto_news()
    except api.ChainScopeAPIError as exc:
        st.warning(f"Berita crypto sementara tidak tersedia: {exc}")
    else:
        with st.container(key="crypto_news"):
            if not crypto_news:
                st.info("Belum ada berita crypto terbaru.")
            for article in crypto_news:
                st.link_button(
                    article["title"],
                    article["url"],
                    help=f"Sumber: {article['source']}",
                )
                st.caption(article["source"])

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart, col_movers = st.columns([2.5, 1])
    with col_chart:
        with st.container(border=True):
            c_t1, c_t2, c_t3 = st.columns([2, 1, 1.5])
            c_t1.markdown("<p style='font-weight:700; color:var(--cs-primary-text); font-size:1rem; margin-bottom:0;'>Market Chart</p>", unsafe_allow_html=True)
            overview_coins = search.filter_coins(market_df, search_query)
            if overview_coins.empty:
                st.info("Tidak ada koin yang cocok dengan pencarian.")
            else:
                labels_by_id = dict(zip(overview_coins["id"], overview_coins["label"]))
                chart_coin_id = c_t2.selectbox(
                    "Koin:",
                    options=overview_coins["id"].tolist(),
                    format_func=lambda coin_id: labels_by_id[coin_id],
                    label_visibility="collapsed",
                    key="overview_coin_id",
                )

                with c_t3:
                    tf = st.segmented_control("Timeframe", ["1D", "7D", "1M", "1Y"], default="7D", label_visibility="collapsed")
                    if not tf:
                        tf = "7D"

                days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
                coin_row = market_df.loc[market_df["id"] == chart_coin_id].iloc[0]

                total_mcap = market_df["market_cap"].sum()
                coin_mcap = coin_row["market_cap"]
                dominance = (coin_mcap / total_mcap) * 100 if total_mcap else 0

                st.markdown(f"<p style='font-size:0.75rem; color:var(--cs-secondary-text); margin-top:5px; margin-bottom:0;'>Market Cap {coin_row['symbol_upper']} (Dominance: {dominance:.2f}%)</p>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='margin-top:0;'>{formatting.format_money(coin_mcap, currency)}</h2>", unsafe_allow_html=True)

                try:
                    hist_df = cached_price_history(chart_coin_id, currency, days_map[tf])
                    fig_main = px.area(
                        hist_df,
                        x="waktu",
                        y="price",
                        color_discrete_sequence=[theme_palette["accent"]],
                    )
                    fig_main.update_traces(
                        fillcolor=theme_palette["area_fill"],
                        line=dict(width=1.5),
                    )
                    ui.apply_plotly_theme(fig_main, dark_mode)
                    fig_main.update_layout(
                        margin=dict(l=0, r=0, t=5, b=0),
                        height=300,
                        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                        yaxis=dict(showgrid=True, tickfont=dict(size=10)),
                    )
                    st.plotly_chart(fig_main, width='stretch', config={'displayModeBar': False, 'scrollZoom': True})
                except Exception:
                    st.warning("Riwayat harga koin ini belum tersedia.")

    with col_movers:
        with st.container(border=True):
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(3)
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(3)
            html = "<p style='font-weight:700; font-size:0.95rem; color:var(--cs-primary-text); margin-bottom:10px;'>Top Gainers ⚡</p>"
            for _, r in gainers.iterrows():
                html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'><div style='display:flex; gap:6px;'><img src='{r['image']}' width='16'><div><span style='font-size:0.75rem; font-weight:600;'>{r['symbol_upper']}</span><br><span style='font-size:0.65rem;'>{formatting.format_money(r['current_price'], currency)}</span></div></div><span class='text-green'>+{r['price_change_percentage_24h']:.2f}%</span></div>"
            html += "<hr style='margin:8px 0; border-color:var(--cs-border);'><p style='font-weight:700; font-size:0.95rem; color:var(--cs-primary-text); margin-bottom:10px;'>Top Losers ⚡</p>"
            for _, r in losers.iterrows():
                html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'><div style='display:flex; gap:6px;'><img src='{r['image']}' width='16'><div><span style='font-size:0.75rem; font-weight:600;'>{r['symbol_upper']}</span><br><span style='font-size:0.65rem;'>{formatting.format_money(r['current_price'], currency)}</span></div></div><span class='text-red'>{r['price_change_percentage_24h']:.2f}%</span></div>"
            st.markdown(html, unsafe_allow_html=True)

elif current_page == "market-data":
    st.markdown(
        f"<h1>{config.translate(language, 'Market Data')}</h1>",
        unsafe_allow_html=True,
    )
    is_free_tier = sub_tier == "Free"
    free_market_coins = (
        market_df.sort_values("market_cap", ascending=False, na_position="last").head(10)
        if is_free_tier else market_df
    )
    free_market_symbols = set(free_market_coins["symbol_upper"].dropna())
    
    # Pilihan Sumber Data
    source_choice = st.radio("Pilih Sumber Data:", ["Global (Semua Koin)", "Indodax (Semua Koin IDR)"], horizontal=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    search_query = st.text_input("🔍 Cari koin (contoh: BTC, SOL, DOGE)...", placeholder="Ketik nama atau simbol koin")
    
    if source_choice == "Global (Semua Koin)":
        # --- LOGIKA COINGECKO (Kode Lama) ---
        with st.container(border=True):
            coin_options = search.filter_coins(free_market_coins, search_query)
            has_restricted_matches = False
            if is_free_tier and search_query.strip():
                restricted_matches = search.filter_coins(market_df, search_query)
                restricted_ids = set(restricted_matches["id"])
                allowed_ids = set(free_market_coins["id"])
                has_restricted_matches = bool(restricted_ids - allowed_ids)
                if has_restricted_matches:
                    st.info("Upgrade ke Premium untuk melihat semua koin.")
            if coin_options.empty:
                if not has_restricted_matches:
                    st.info("Tidak ada koin yang cocok dengan pencarian.")
                table_source = free_market_coins.iloc[0:0]
            else:
                labels_by_id = dict(zip(coin_options["id"], coin_options["label"]))
                if (
                    "market_data_coin_id" in st.session_state
                    and st.session_state.market_data_coin_id not in labels_by_id
                ):
                    del st.session_state.market_data_coin_id
                market_coin_id = st.selectbox(
                    "Pilih koin untuk analisis",
                    options=coin_options["id"].tolist(),
                    format_func=lambda coin_id: labels_by_id[coin_id],
                    key="market_data_coin_id",
                )
                if st.button("Buka Technical Analysis", key="market_data_open_analysis"):
                    st.session_state.selected_technical_coin = market_coin_id
                    st.session_state.current_page = "technical-analysis"
                    st.rerun()
                table_source = (
                    coin_options
                    if search_query.strip()
                    else coin_options.head(10 if is_free_tier else 250)
                )
            
            display_df = pd.DataFrame({
                "#": range(1, len(table_source) + 1),
                "Coin": table_source["name"],
                "Ticker": table_source["symbol_upper"],
                "Price": table_source["current_price"].map(
                    lambda value: "—" if pd.isna(value) or value == 0
                    else formatting.format_money(value, currency)
                ),
                "24h %": table_source["price_change_percentage_24h"].map(
                    lambda value: "—" if pd.isna(value) else f"{value:.2f}%"
                ),
                "24h Volume": table_source["total_volume"].map(
                    lambda value: "—" if pd.isna(value)
                    else formatting.format_money(value, currency)
                ),
                "Market Cap": table_source["market_cap"].map(
                    lambda value: "—" if pd.isna(value)
                    else formatting.format_money(value, currency)
                ),
            })
            
            event = st.dataframe(ui.style_dataframe(display_df, dark_mode), width='stretch', hide_index=True, on_select="rerun", selection_mode="single-row", column_config={"Coin": st.column_config.TextColumn("Coin", width="medium"), "24h %": st.column_config.TextColumn("24h %", width="small")})
            
            if len(event.selection.rows) > 0:
                selected_idx = event.selection.rows[0]
                selected_coin_id = table_source.iloc[selected_idx]["id"]
                st.session_state.selected_technical_coin = selected_coin_id
                st.session_state.current_page = "technical-analysis"
                st.rerun()

    else:
        # --- LOGIKA INDODAX (Semua Koin) ---
        try:
            with st.spinner("Mengambil data dari Indodax..."):
                indodax_df = api.fetch_indodax_all_tickers()
        except api.ChainScopeAPIError as exc:
            st.error(f"Gagal mengambil data dari Indodax: {exc}")
        else:
            # Filter berdasarkan pencarian
            if search_query:
                indodax_df = indodax_df[indodax_df["Symbol"].str.contains(search_query.upper(), case=False)]
            if is_free_tier and search_query.strip():
                restricted_indodax = indodax_df.loc[
                    ~indodax_df["Symbol"].astype(str).str.upper().isin(free_market_symbols)
                ]
                if not restricted_indodax.empty:
                    st.info("Upgrade ke Premium untuk melihat semua koin.")
            if is_free_tier:
                indodax_df = indodax_df[
                    indodax_df["Symbol"].astype(str).str.upper().isin(free_market_symbols)
                ]
                
            with st.container(border=True):
                # Format Tabel
                display_df = pd.DataFrame({
                    "Simbol": indodax_df["Symbol"],
                    "Harga (IDR)": indodax_df["Price"].map(lambda v: f"Rp {v:,.0f}"),
                    "Tertinggi 24j": indodax_df["High"].map(lambda v: f"Rp {v:,.0f}"),
                    "Terendah 24j": indodax_df["Low"].map(lambda v: f"Rp {v:,.0f}"),
                    "Volume (IDR)": indodax_df["Volume"].map(lambda v: f"Rp {v:,.0f}"),
                })
                st.dataframe(ui.style_dataframe(display_df, dark_mode), width='stretch', hide_index=True)

elif current_page == "relative-strategy" and sub_tier == "Free":
    st.markdown(
        f"<h1>{config.translate(language, 'Strategi Relatif')}</h1>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown("### Fitur Eksklusif Premium")
        st.write("Bandingkan pergerakan koin dan analisis rasio dengan fitur Premium.")
        if st.button("Upgrade Sekarang", type="primary"):
            st.session_state.current_page = "portfolio"
            st.rerun()

elif current_page == "relative-strategy":
    st.markdown(
        f"<h1>{config.translate(language, 'Strategi Relatif')}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:var(--cs-secondary-text);'>Bandingkan pergerakan dua koin berdasarkan rasio harga 30 hari.</p>",
        unsafe_allow_html=True,
    )

    coin_options = market_df.drop_duplicates("id", keep="first")
    labels_by_id = dict(zip(coin_options["id"], coin_options["label"]))
    coin_ids = coin_options["id"].tolist()
    default_a = "bitcoin" if "bitcoin" in labels_by_id else coin_ids[0]
    default_b = "ethereum" if "ethereum" in labels_by_id else (
        coin_ids[1] if len(coin_ids) > 1 else default_a
    )

    with st.container(border=True):
        coin_a_col, coin_b_col = st.columns(2)
        with coin_a_col:
            coin_a_id = st.selectbox(
                "Koin A",
                options=coin_ids,
                index=coin_ids.index(default_a),
                format_func=lambda coin_id: labels_by_id[coin_id],
                key="relative_coin_a",
            )
        with coin_b_col:
            coin_b_id = st.selectbox(
                "Koin B",
                options=coin_ids,
                index=coin_ids.index(default_b),
                format_func=lambda coin_id: labels_by_id[coin_id],
                key="relative_coin_b",
            )

    if coin_a_id == coin_b_id:
        st.info("Pilih dua koin yang berbeda untuk menghitung rasio.")
    else:
        try:
            history_a = cached_price_history(coin_a_id, currency, days=30)
            history_b = cached_price_history(coin_b_id, currency, days=30)
            ratio_df = compare.build_relative_ratio(history_a, history_b)
        except api.ChainScopeAPIError as exc:
            st.error(f"Gagal mengambil riwayat harga CoinGecko: {exc}")
        else:
            if ratio_df.empty:
                st.warning("Data historis yang beririsan tidak tersedia untuk kedua koin.")
            else:
                coin_a_label = labels_by_id[coin_a_id]
                coin_b_label = labels_by_id[coin_b_id]
                current_ratio = float(ratio_df["ratio"].iloc[-1])
                average_ratio = float(ratio_df["ratio"].mean())

                if current_ratio > average_ratio:
                    relative_status = f"{coin_a_label} Overvalued"
                elif current_ratio < average_ratio:
                    relative_status = f"{coin_b_label} Overvalued"
                else:
                    relative_status = "Relatif seimbang"

                with st.container(border=True):
                    metric_cols = st.columns(3)
                    metric_cols[0].metric("Rasio Saat Ini", f"{current_ratio:.6g}")
                    metric_cols[1].metric("Rata-rata 30 Hari", f"{average_ratio:.6g}")
                    metric_cols[2].metric("Status Relatif", relative_status)
                    st.caption(
                        "Interpretasi relatif terhadap rata-rata rasio 30 hari; "
                        "bukan penilaian nilai intrinsik koin."
                    )

                fig_ratio = go.Figure()
                fig_ratio.add_trace(go.Scatter(
                    x=ratio_df["waktu"],
                    y=ratio_df["ratio"],
                    mode="lines",
                    name=f"{coin_a_label} / {coin_b_label}",
                    line={"color": theme_palette["accent"], "width": 2},
                ))
                fig_ratio.add_trace(go.Scatter(
                    x=ratio_df["waktu"],
                    y=ratio_df["ma20"],
                    mode="lines",
                    name="MA 20",
                    line={"color": theme_palette["accent"], "width": 1.5, "dash": "dash"},
                ))
                fig_ratio.update_layout(
                    height=430,
                    margin={"l": 12, "r": 12, "t": 25, "b": 12},
                    legend={"orientation": "h", "y": 1.08, "x": 0},
                    xaxis={"showgrid": False, "title": None},
                    yaxis={
                        "showgrid": True,
                        "title": f"Rasio {coin_a_label} / {coin_b_label}",
                    },
                )
                ui.apply_plotly_theme(fig_ratio, dark_mode)
                with st.container(border=True):
                    st.plotly_chart(
                        fig_ratio,
                        width='stretch',
                        config={"displayModeBar": False},
                    )

elif current_page == "technical-analysis":
    st.markdown(
        f"<h1>{config.translate(language, 'Technical Analysis')}</h1>",
        unsafe_allow_html=True,
    )
    from chainscope.chart_component import render_modern_chart
    technical_coin_options = market_df.drop_duplicates("id", keep="first")
    technical_coin_ids = technical_coin_options["id"].tolist()
    technical_coin_labels = dict(zip(
        technical_coin_options["id"], technical_coin_options["label"]
    ))
    selected_coin_id = st.session_state.get("selected_technical_coin", "bitcoin")
    if selected_coin_id not in technical_coin_labels:
        selected_coin_id = "bitcoin" if "bitcoin" in technical_coin_labels else technical_coin_ids[0]
        st.session_state.selected_technical_coin = selected_coin_id
    selected_coin_id = st.selectbox(
        "Pilih koin untuk chart dan AI",
        options=technical_coin_ids,
        format_func=lambda coin_id: technical_coin_labels[coin_id],
        key="selected_technical_coin",
    )
    selected_rows = market_df.loc[market_df["id"] == selected_coin_id]
    selected_symbol = (
        selected_rows.iloc[0]["symbol_upper"] if not selected_rows.empty else "BTCUSDT"
    )
    chart_coins = (
        market_df[["id", "symbol_upper", "name", "image"]]
        .fillna("")
        .rename(columns={"symbol_upper": "symbol"})
        .to_dict("records")
    )
    render_modern_chart(
        selected_symbol,
        coins=chart_coins,
        selected_coin_id=selected_coin_id,
        allow_coin_selection=False,
        is_dark_mode=dark_mode,
    )
    with st.expander("🤖 Tanya AI Assistant", expanded=False):
        question = st.text_input(
            "Pertanyaan",
            placeholder="Apakah bagus beli BTC sekarang?",
            key="technical_ai_question",
        )
        if st.button("Tanya AI", key="technical_ai_ask"):
            gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
            if not gemini_api_key:
                st.warning("API Key Gemini belum diatur")
            elif not question.strip():
                st.warning("Masukkan pertanyaan terlebih dahulu.")
            elif selected_rows.empty:
                st.error("Data koin aktif tidak tersedia untuk analisis AI.")
            else:
                try:
                    history = cached_price_history(selected_coin_id, "usd", days=7)
                    snapshot = ai_assistant.build_indicator_snapshot(history)
                    coin_name = selected_rows.iloc[0]["name"]
                    prompt = ai_assistant.build_prompt(
                        snapshot,
                        question.strip(),
                        f"{coin_name} ({selected_symbol})",
                    )
                    answer = ai_assistant.ask_gemini(gemini_api_key, prompt)
                except api.ChainScopeAPIError as exc:
                    st.error(f"Gagal mengambil data indikator: {exc}")
                except ValueError as exc:
                    st.error(f"Gagal menyiapkan analisis AI: {exc}")
                except GoogleAPIError as exc:
                    st.error(f"Gagal meminta jawaban dari Gemini: {exc}")
                else:
                    st.markdown(answer)

elif current_page == "trading-journal":
    st.markdown(
        f"<h1>{config.translate(language, 'Trading Journal')}</h1>",
        unsafe_allow_html=True,
    )
    
    col_manual, col_csv = st.columns(2)
    with col_manual:
        with st.container(border=True):
            st.markdown("#### Input Manual")
            with st.form("manual_trade", clear_on_submit=True):
                t_coin = st.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
                t_side = st.selectbox("Aksi", ["buy", "sell"])
                t_date = st.date_input("Tanggal", datetime.now())
                t_amount = st.number_input("Jumlah Koin", min_value=0.00000001, format="%.8f")
                t_price = st.number_input("Harga (USD)", min_value=0.01)
                t_strategy = st.selectbox("Strategi", ["Swing", "Scalping", "Hedge", "Long-term"])
                if st.form_submit_button("Simpan Transaksi", width='stretch'):
                    sym = market_df[market_df["id"]==t_coin]["symbol_upper"].values[0]
                    db.add_trade(user.id, t_coin, sym, t_side, t_amount, t_price, str(t_date), strategy_tag=t_strategy)
                    st.success("Transaksi tersimpan!")
                    st.rerun()

    with col_csv:
        with st.container(border=True):
            st.markdown("#### Import CSV")
            uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
            if uploaded:
                try:
                    df_csv = pd.read_csv(uploaded)
                    map_coin = st.selectbox("Kolom Koin", df_csv.columns)
                    map_side = st.selectbox("Kolom Aksi", df_csv.columns)
                    map_amount = st.selectbox("Kolom Jumlah", df_csv.columns)
                    map_price = st.selectbox("Kolom Harga", df_csv.columns)
                    map_date = st.selectbox("Kolom Tanggal", df_csv.columns)
                    if st.button("Proses CSV", width='stretch'):
                        success = 0
                        for _, row in df_csv.iterrows():
                            c_id = str(row[map_coin]).lower()
                            valid = market_df[market_df["id"].str.contains(c_id, case=False) | market_df["symbol"].str.contains(c_id, case=False)]
                            if not valid.empty:
                                db.add_trade(user.id, valid.iloc[0]["id"], valid.iloc[0]["symbol_upper"], str(row[map_side]).lower(), float(row[map_amount]), float(row[map_price]), str(row[map_date]), source="csv")
                                success += 1
                        st.success(f"Import {success} transaksi!")
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Riwayat Transaksi")
        trades = db.get_user_trades(user.id)
        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades["trade_time"] = pd.to_datetime(df_trades["trade_time"]).dt.date
            st.dataframe(ui.style_dataframe(df_trades[["trade_time", "symbol", "side", "amount", "price_usd"]], dark_mode), width='stretch', hide_index=True)
            if st.button("🗑️ Hapus Semua Transaksi", type="secondary"):
                db.delete_all_user_trades(user.id)
                st.rerun()
        else:
            st.info("Belum ada transaksi.")

elif current_page == "price-alerts":
    st.markdown(
        f"<h1>{config.translate(language, 'Price Alerts')}</h1>",
        unsafe_allow_html=True,
    )

    active_alert_count = db.count_user_alerts(user.id) if sub_tier == "Free" else 0
    if sub_tier == "Free" and active_alert_count >= 1:
        st.info(
            "Fitur Alert dibatasi 1 untuk user Free. "
            "Upgrade ke Premium untuk alert tanpa batas."
        )
    else:
        with st.container(border=True):
            st.markdown("#### Buat Alert Baru")
            with st.form("new_alert", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                a_coin = c1.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
                a_cond = c2.selectbox("Kondisi", ["above", "below"])
                a_price = c3.number_input("Target Harga", min_value=0.01)
                if st.form_submit_button("Tambah Alert", width='stretch'):
                    if sub_tier == "Free" and db.count_user_alerts(user.id) >= 1:
                        st.info(
                            "Fitur Alert dibatasi 1 untuk user Free. "
                            "Upgrade ke Premium untuk alert tanpa batas."
                        )
                    else:
                        sym = market_df[market_df["id"]==a_coin]["symbol_upper"].values[0]
                        db.add_alert(user.id, a_coin, sym, a_cond, a_price, currency)
                        st.success("Alert dibuat!")
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Daftar Alert")
        alerts = db.get_user_alerts(user.id)
        if alerts:
            alert_df = pd.DataFrame([
                {
                    "Koin": alert["symbol"],
                    "Kondisi": "Di atas" if alert["condition"] == "above" else "Di bawah",
                    "Target": formatting.format_money(alert["target_price"], alert["currency"]),
                    "Status": "Menunggu" if alert.get("is_active", True) else "Terpicu",
                    "Dibuat": alert.get("created_at", "—"),
                }
                for alert in alerts
            ])
            st.dataframe(ui.style_dataframe(alert_df, dark_mode), width='stretch', hide_index=True)
        else:
            st.info("Belum ada alert aktif.")

elif current_page == "pdf-report":
    st.markdown(
        f"<h1>{config.translate(language, 'Laporan PDF')}</h1>",
        unsafe_allow_html=True,
    )
    st.write("Unduh ringkasan pasar berdasarkan data yang sedang ditampilkan.")
    pdf_bytes = report.build_weekly_report(market_df, currency, data_source)
    st.download_button(
        "Unduh Laporan PDF",
        data=pdf_bytes,
        file_name=f"chainscope-weekly-report-{datetime.now():%Y-%m-%d}.pdf",
        mime="application/pdf",
    )

elif current_page == "portfolio":
    st.markdown(
        f"<h1>{config.translate(language, 'Portfolio')}</h1>",
        unsafe_allow_html=True,
    )
    trades = db.get_user_trades(user.id)
    
    if not trades:
        st.info("Belum ada transaksi di Trading Journal.")
    else:
        pf_df = journal_calc.calculate_portfolio_from_trades(trades)
        if pf_df.empty:
            st.warning("Semua aset sudah terjual.")
        else:
            pf_df = pf_df.merge(market_df[["id", "current_price"]], left_on="coin_id", right_on="id", how="left")
            try:
                rate = cached_usd_currency_rate(currency)
            except api.ChainScopeAPIError:
                st.error("Gagal mengambil kurs mata uang dari CoinGecko.")
                st.stop()
            
            pf_df["current_price"] = pf_df["current_price"].fillna(0)
            pf_df["avg_buy_price"] = pf_df["avg_buy_price_usd"] * rate
            pf_df["invested"] = pf_df["total_invested_usd"] * rate
            pf_df["current_value"] = pf_df["amount"] * pf_df["current_price"]
            pf_df["pnl"] = pf_df["current_value"] - pf_df["invested"]
            pf_df["pnl_pct"] = (pf_df["pnl"] / pf_df["invested"] * 100).fillna(0)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Nilai Aset", formatting.format_money(pf_df["current_value"].sum(), currency))
            c2.metric("Total Modal", formatting.format_money(pf_df["invested"].sum(), currency))
            c3.metric("P&L Keseluruhan", formatting.format_money(pf_df["pnl"].sum(), currency), delta=f"{pf_df['pnl_pct'].mean():.2f}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.subheader("Rincian Aset")
                display_df = pd.DataFrame({
                    "Koin": pf_df["symbol"],
                    "Jumlah": pf_df["amount"].map(lambda x: f"{x:.4f}"),
                    "Harga Rata2": pf_df["avg_buy_price"].map(lambda v: formatting.format_money(v, currency)),
                    "Nilai Kini": pf_df["current_value"].map(lambda v: formatting.format_money(v, currency)),
                    "P&L": pf_df["pnl"].map(lambda v: formatting.format_money(v, currency)),
                })
                st.dataframe(ui.style_dataframe(display_df, dark_mode), width='stretch', hide_index=True)

            strategy_df = pf_df.groupby("strategy_tag", as_index=False)["current_value"].sum()
            fig = px.pie(
                strategy_df,
                values="current_value",
                names="strategy_tag",
                color_discrete_sequence=[
                    theme_palette["accent"],
                    theme_palette["accent_secondary"],
                    theme_palette["accent_tertiary"],
                ],
                title="Alokasi Portofolio per Strategi",
            )
            ui.apply_plotly_theme(fig, dark_mode)
            st.plotly_chart(fig, width='stretch')

    if user_profile.get("subscription_tier", "free").lower() != "premium":
        if st.button("🚀 Upgrade ke Premium (Rp 50.000)"):
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            order_id = (
                f"PREMIUM-{sha256(user.id.encode()).hexdigest()[:12]}-{timestamp}"
            )
            st.session_state["premium_payment_order_id"] = order_id
            try:
                st.session_state["premium_payment_url"] = payment.create_snap_transaction(
                    user.id, user.email, 50000, order_id=order_id
                )
            except (ValueError, payment.SnapPaymentError) as error:
                st.session_state.pop("premium_payment_url", None)
                st.error(str(error))

        payment_url = st.session_state.get("premium_payment_url")
        if payment_url:
            st.link_button("Bayar Sekarang", url=payment_url)

        order_id = st.session_state.get("premium_payment_order_id")
        if order_id and st.button("Cek Status Pembayaran"):
            try:
                transaction_status = payment.check_transaction_status(order_id)
            except (ValueError, payment.SnapPaymentError) as error:
                st.error(str(error))
            else:
                if transaction_status in {"settlement", "capture"}:
                    db.upgrade_to_premium(user.id)
                    st.session_state.pop("premium_payment_order_id", None)
                    st.session_state.pop("premium_payment_url", None)
                    st.success("Pembayaran terverifikasi. Akun Premium aktif selama 30 hari.")
                elif transaction_status == "pending":
                    st.info("Pembayaran masih tertunda. Silakan selesaikan pembayaran di Midtrans.")
                elif transaction_status in {"expire", "deny"}:
                    st.error(f"Pembayaran gagal dengan status: {transaction_status}.")
                else:
                    st.warning(f"Status pembayaran saat ini: {transaction_status}.")

elif current_page == "converter":
    st.markdown(
        f"<h1>{config.translate(language, 'Converter')}</h1>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        try:
            rate = cached_usd_currency_rate(currency)
        except api.ChainScopeAPIError:
            st.error("Gagal mengambil kurs mata uang dari CoinGecko.")
            st.stop()
        price_map = converter.build_price_map(market_df, currency, rate)
        col1, col2 = st.columns(2)
        fiat_assets = list(dict.fromkeys(["USD", currency]))
        asset_options = fiat_assets + market_df["id"].tolist()
        selected_currency_index = fiat_assets.index(currency)
        from_asset = col1.selectbox("Dari:", asset_options)
        to_asset = col2.selectbox("Ke:", asset_options, index=selected_currency_index)
        amount = st.number_input("Jumlah:", min_value=0.0, value=1.0)
        res = converter.convert(amount, from_asset, to_asset, price_map)
        if res is not None:
            st.metric("Hasil", formatting.format_money(res, currency))

elif current_page == "watchlist":
    st.markdown(
        f"<h1>{config.translate(language, 'Watchlist')}</h1>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        available_ids = market_df["id"].tolist()
        current_watchlist = db.get_user_watchlist(user.id)
        valid_default = [cid for cid in current_watchlist if cid in available_ids]
        
        selected_ids = st.multiselect("Pilih koin:", options=available_ids, default=valid_default, format_func=lambda cid: dict(zip(market_df["id"], market_df["label"])).get(cid, cid))
        
        if set(selected_ids) != set(current_watchlist):
            db.clear_user_watchlist(user.id)
            for cid in selected_ids: db.add_to_watchlist(user.id, cid)
            st.rerun()
            
        if current_watchlist:
            wl_df = market_df[market_df["id"].isin(current_watchlist)].copy()
            st.dataframe(ui.style_dataframe(wl_df[["name", "symbol_upper", "current_price"]].rename(columns={"name":"Nama", "symbol_upper":"Simbol", "current_price":"Harga"}), dark_mode), width='stretch', hide_index=True)

elif current_page == "wallet":
    from chainscope.wallet_component import render_personal_wallet

    render_personal_wallet(dark_mode=dark_mode)

elif current_page == "admin-panel" and is_dev:
    st.markdown(
        f"<h1>{config.translate(language, 'Admin Panel')}</h1>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        all_users = admin.get_all_users()
        if not all_users:
            st.info("Belum ada user yang terdaftar.")
        else:
            df_users = pd.DataFrame(all_users)
            if "subscription_end" in df_users.columns:
                df_users["subscription_end"] = df_users["subscription_end"].fillna("—").str[:10]
                
            display_cols = ["email", "role", "subscription_tier", "subscription_end"]
            st.dataframe(ui.style_dataframe(df_users[display_cols].rename(columns={"email": "Email", "role": "Role", "subscription_tier": "Plan", "subscription_end": "Berakhir Pada"}), dark_mode), width='stretch', hide_index=True)
            
            st.markdown("---")
            st.markdown("### Kelola User")
            
            user_emails = [u["email"] for u in all_users]
            selected_email = st.selectbox("Pilih user untuk diedit:", options=user_emails)
            
            if selected_email:
                selected_user = next((u for u in all_users if u["email"] == selected_email), None)
                uid = selected_user["id"]
                
                col_r, col_t, col_delete, col_d = st.columns(4)
                
                with col_r:
                    current_role = selected_user.get("role", "user")
                    new_role = st.selectbox("Role:", ["user", "dev"], index=0 if current_role == "user" else 1)
                    if st.button("Update Role"):
                        admin.update_user_role(uid, new_role)
                        st.success("Role diupdate.")
                        st.rerun()
                        
                with col_t:
                    current_tier = selected_user.get("subscription_tier", "free")
                    new_tier = st.selectbox("Langganan:", ["free", "premium"], index=0 if current_tier == "free" else 1)
                    if st.button("Update Tier"):
                        admin.update_user_subscription(uid, new_tier)
                        st.success("Tier diupdate.")
                        st.rerun()

                with col_delete:
                    st.checkbox(
                        "Saya yakin ingin menghapus user ini",
                        key=f"confirm_delete_user_{uid}",
                        disabled=uid == user.id,
                    )
                    if uid == user.id:
                        st.caption("Admin tidak dapat menghapus akunnya sendiri.")
                    if st.button(
                        "🗑️ Hapus User",
                        type="primary",
                        key=f"delete_user_{uid}",
                        disabled=uid == user.id,
                    ):
                        if st.session_state.get(f"confirm_delete_user_{uid}", False):
                            auth_account_deleted = db.delete_user(uid)
                            if auth_account_deleted:
                                st.success("User dan akun autentikasi berhasil dihapus.")
                            else:
                                st.success("Data aplikasi user berhasil dihapus.")
                                st.warning(
                                    "Akun autentikasi masih ada. Tambahkan "
                                    "`SUPABASE_SERVICE_ROLE_KEY` ke "
                                    "`.streamlit/secrets.toml` untuk menghapusnya."
                                )
                            st.rerun()
                        else:
                            st.warning("Centang konfirmasi sebelum menghapus user.")
                        
                with col_d:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    new_end = st.date_input("Perpanjang s/d:")
                    if st.button("Set Expired"):
                        admin.update_user_subscription(uid, new_tier, str(new_end))
                        st.success("Masa aktif diperbarui.")
                        st.rerun()