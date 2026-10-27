"""
ChainScope ID - Premium Light Mode (Full Features & Navigation)
"""
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from chainscope import (
    ui, api, auth, compare, config, converter, db, demo, formatting, 
    indicators, journal_calc, report, search, telegram, admin
)

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ChainScope ID", page_icon="📈", layout="wide")
ui.apply_premium_theme()

# 2. CEK AUTENTIKASI (Paling Atas)
auth.check_session()
if "user" not in st.session_state or st.session_state.user is None:
    auth.show_auth_page()
    st.stop()

user = st.session_state.user
user_profile = db.get_user_profile(user.id)
is_dev = user_profile.get("role") == "dev"
sub_tier = user_profile.get("subscription_tier", "free").title()
end_date = user_profile.get("subscription_end")

# 3. FUNGSI CACHE API
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_market_data(vs_currency: str, limit: int) -> pd.DataFrame:
    return api.fetch_market_data(vs_currency, limit)

@st.cache_data(ttl=300, show_spinner=False)
def cached_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_price_history(coin_id, vs_currency, days)

@st.cache_data(ttl=300, show_spinner=False)
def cached_ohlc(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_ohlc(coin_id, vs_currency, days)

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_usd_idr_rate() -> float:
    try:
        df_usd = api.fetch_market_data("usd", 1)
        df_idr = api.fetch_market_data("idr", 1)
        if not df_usd.empty and not df_idr.empty:
            return float(df_idr.iloc[0]["current_price"]) / float(df_usd.iloc[0]["current_price"])
    except Exception:
        pass
    return float(config.DEMO_USD_TO_IDR)

# 4. MENU CONFIG (URL TANPA SPASI)
menu_config = {
    "market-overview": "🏠 Market Overview",
    "market-data": "📊 Market Data",
    "trading-journal": "📒 Trading Journal",
    "price-alerts": "🔔 Price Alerts",
    "technical-analysis": "📉 Technical Analysis",
    "portfolio": "💼 Portfolio",
    "converter": "💱 Converter",
    "watchlist": "⭐ Watchlist"
}
if is_dev:
    menu_config["admin-panel"] = "👑 Admin Panel"

query_params = st.query_params
current_url_page = query_params.get("page", "market-overview")
current_page_name = menu_config.get(current_url_page, "🏠 Market Overview")

# 5. SIDEBAR
with st.sidebar:
    st.markdown("""
        <div style='display:flex; align-items:center; gap:8px; margin-bottom: 20px; padding-left: 0px; margin-top: 10px;'>
            <div style='background: #6C35D9; padding: 6px 10px; border-radius: 8px;'>
                <span style='color:white; font-size:1.2rem;'>⚡</span>
            </div>
            <span style='font-size:1.2rem; font-weight:800; color:#171827;'>ChainScope <span style='color:#6C35D9;'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Gunakan Session State untuk Navigasi (Aman, tidak refresh browser)
    if "current_page" not in st.session_state:
        st.session_state.current_page = "market-overview"

    menu_config = {
        "market-overview": "🏠 Market Overview",
        "market-data": "📊 Market Data",
        "trading-journal": "📒 Trading Journal",
        "price-alerts": "🔔 Price Alerts",
        "technical-analysis": "📉 Technical Analysis",
        "portfolio": "💼 Portfolio",
        "converter": "💱 Converter",
        "watchlist": "⭐ Watchlist"
    }
    if is_dev:
        menu_config["admin-panel"] = "👑 Admin Panel"

    # Tampilkan tombol menu (Disembunyikan stylingnya lewat CSS)
    for url_key, display_name in menu_config.items():
        # Cek apakah menu ini sedang aktif
        is_active = (st.session_state.current_page == url_key)
        
        # Jika diklik, ubah halaman di session state dan rerun
        if st.button(display_name, use_container_width=True, key=f"btn_{url_key}", type="primary" if is_active else "secondary"):
            st.session_state.current_page = url_key
            st.rerun()

    st.markdown("---")
    currency = st.radio("Mata uang:", options=["IDR", "USD"], horizontal=True)
    coin_count = st.selectbox("Tampilkan Koin:", options=[50, 100, 250], index=0)
    demo_mode = st.checkbox("Mode Demo", value=False)

# Set variabel halaman aktif
current_url_page = st.session_state.current_page
current_page_name = menu_config.get(current_url_page, "🏠 Market Overview")
# 6. AMBIL DATA PASAR
market_df = None
if demo_mode:
    market_df = demo.get_demo_market_data(limit=min(coin_count, 50), currency=currency)
else:
    try:
        market_df = cached_market_data(currency, coin_count)
    except Exception:
        market_df = demo.get_demo_market_data(limit=min(coin_count, 50), currency=currency)

market_df = market_df.copy()
market_df["symbol_upper"] = market_df["symbol"].astype(str).str.upper()
market_df["label"] = market_df["name"] + " (" + market_df["symbol_upper"] + ")"

# ===========================================================================
# ROUTING HALAMAN
# ===========================================================================
if current_page_name == "🏠 Market Overview":
    col_title, col_search, col_profile = st.columns([2.5, 2, 0.5])
    with col_title:
        st.markdown("<h1>Market Overview</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.9rem; margin-top:5px;'>Real-time crypto market data and insights</p>", unsafe_allow_html=True)
    with col_search:
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input("Search", placeholder="🔍 Search coins...", label_visibility="collapsed")
    with col_profile:
        with st.popover("👤"):
            st.markdown(f"### 👤 {user.email}")
            st.markdown(f"**Plan:** {sub_tier}")
            if end_date: st.markdown(f"**Aktif s/d:** {end_date[:10]}")
            if st.button("🚪 Logout", use_container_width=True, type="primary"): auth.logout_user()

    st.markdown("<br>", unsafe_allow_html=True)

    top4_df = market_df.head(4)
    cols = st.columns(4)
    for col, (_, row) in zip(cols, top4_df.iterrows()):
        with col:
            with st.container(border=True):
                color = "#16834A" if row['price_change_percentage_24h'] >= 0 else "#D83D50"
                icon = "▲" if row['price_change_percentage_24h'] >= 0 else "▼"
                c_left, c_right = st.columns([1.2, 1])
                with c_left:
                    st.markdown(f"""
                    <div style='display:flex; gap:8px; align-items:center;'>
                        <img src="{row['image']}" width="24" height="24">
                        <div>
                            <div style='font-weight:700; font-size:0.85rem; color:#171827;'>{row['name']}</div>
                            <div style='font-size:0.7rem; color:#77788A;'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                    <div style='margin-top:15px;'>
                        <div style='font-weight:800; font-size:1.1rem; color:#171827;'>{formatting.format_money(row['current_price'], currency)}</div>
                        <div style='color:{color}; font-size:0.8rem; font-weight:600;'>{icon} {row['price_change_percentage_24h']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_right:
                    sparkline_prices = row.get("sparkline_in_7d", {}).get("price", [])
                    if sparkline_prices:
                        fig = go.Figure(go.Scatter(y=sparkline_prices, mode='lines', line=dict(color=color, width=1.5)))
                        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=60, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart, col_right = st.columns([2.5, 1])
    with col_chart:
        with st.container(border=True):
            c_t1, c_t2, c_t3 = st.columns([2, 1, 1.5])
            c_t1.markdown("<p style='font-weight:700; color:#171827; font-size:1rem; margin-bottom:0;'>Market Chart</p>", unsafe_allow_html=True)
            
            chart_coin_label = c_t2.selectbox("Koin:", market_df["label"].tolist(), label_visibility="collapsed")
            chart_coin_id = dict(zip(market_df["label"], market_df["id"]))[chart_coin_label]
            
            with c_t3:
                tf = st.segmented_control("Timeframe", ["1D", "7D", "1M", "1Y"], default="7D", label_visibility="collapsed")
                if not tf: tf = "7D"
            
            days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
            coin_row = market_df[market_df["id"] == chart_coin_id].iloc[0]
            
            total_mcap = market_df["market_cap"].sum()
            coin_mcap = coin_row["market_cap"]
            dominance = (coin_mcap / total_mcap) * 100

            st.markdown(f"<p style='font-size:0.75rem; color:#77788A; margin-top:5px; margin-bottom:0;'>Market Cap {coin_row['symbol_upper']} (Dominance: {dominance:.2f}%)</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin-top:0;'>{formatting.format_money(coin_mcap, currency)}</h2>", unsafe_allow_html=True)
            
            try:
                hist_df = demo.get_demo_price_history(coin_row["current_price"]) if demo_mode else cached_price_history(chart_coin_id, currency, days_map[tf])
                fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#6C35D9'])
                fig_main.update_traces(fillcolor='rgba(108, 53, 217, 0.08)', line=dict(width=1.5))
                fig_main.update_layout(margin=dict(l=0, r=0, t=5, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, tickfont=dict(size=10)), yaxis=dict(showgrid=True, gridcolor='#E9E6F0', tickfont=dict(size=10)))
                st.plotly_chart(fig_main, use_container_width=True)
            except Exception: pass

    with col_right:
        with st.container(border=True):
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(4)
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(4)
            html = f"<p style='font-weight:700; font-size:0.95rem; color:#171827; margin-bottom:10px;'>Top Gainers ⚡</p>"
            for _, r in gainers.iterrows():
                html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'><div style='display:flex; gap:6px;'><img src='{r['image']}' width='16'><div><span style='font-size:0.75rem; font-weight:600;'>{r['symbol_upper']}</span><br><span style='font-size:0.65rem;'>{formatting.format_money(r['current_price'], currency)}</span></div></div><span class='text-green'>+{r['price_change_percentage_24h']:.2f}%</span></div>"
            html += f"<hr style='margin:8px 0;'><p style='font-weight:700; font-size:0.95rem; color:#171827; margin-bottom:10px;'>Top Losers ⚡</p>"
            for _, r in losers.iterrows():
                html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'><div style='display:flex; gap:6px;'><img src='{r['image']}' width='16'><div><span style='font-size:0.75rem; font-weight:600;'>{r['symbol_upper']}</span><br><span style='font-size:0.65rem;'>{formatting.format_money(r['current_price'], currency)}</span></div></div><span class='text-red'>{r['price_change_percentage_24h']:.2f}%</span></div>"
            st.markdown(html, unsafe_allow_html=True)

elif current_page_name == "📊 Market Data":
    st.markdown("<h1>Market Data</h1>", unsafe_allow_html=True)
    st.markdown("<p>Klik pada baris koin untuk melihat analisis teknikalnya.</p><br>", unsafe_allow_html=True)
    search_query = st.text_input("🔍 Cari koin...", placeholder="Bitcoin, ETH, Solana")
    
    with st.container(border=True):
        table_source = search.filter_coins(market_df, search_query)
        if table_source.empty: table_source = market_df
        
        display_df = pd.DataFrame({
            "#": range(1, len(table_source) + 1),
            "Coin": table_source["name"],
            "Ticker": table_source["symbol_upper"],
            "Price": table_source["current_price"].map(lambda v: formatting.format_money(v, currency)),
            "24h %": table_source["price_change_percentage_24h"].map(lambda v: f"{v:.2f}%"),
            "24h Volume": table_source["total_volume"].map(lambda v: formatting.format_money(v, currency)),
            "Market Cap": table_source["market_cap"].map(lambda v: formatting.format_money(v, currency)),
        })
        
        event = st.dataframe(display_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", column_config={"Coin": st.column_config.TextColumn("Coin", width="medium"), "24h %": st.column_config.TextColumn("24h %", width="small")})
        
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            selected_coin_id = table_source.iloc[selected_idx]["id"]
            st.query_params["page"] = "technical-analysis"
            st.query_params["coin"] = selected_coin_id
            st.rerun()

elif current_page_name == "📉 Technical Analysis":
    st.markdown("<h1>Technical Analysis</h1>", unsafe_allow_html=True)
    
    default_coin = st.query_params.get("coin", "bitcoin")
    default_idx = int(market_df[market_df["id"] == default_coin].index[0]) if default_coin in market_df["id"].values else 0
    
    with st.container(border=True):
        c1, c2 = st.columns([2, 2])
        tech_label = c1.selectbox("Pilih Koin:", market_df["label"].tolist(), index=default_idx)
        tf = c2.selectbox("Timeframe", ["1D", "7D", "1M", "1Y"], index=1)
        
        with st.expander("⚙️ Pengaturan Indikator", expanded=False):
            col_i1, col_i2, col_i3 = st.columns(3)
            show_ma = col_i1.multiselect("Moving Average", ["MA 9", "MA 20", "MA 50", "MA 200"], default=["MA 20", "MA 50"])
            show_osc = col_i2.selectbox("Oscillator", ["RSI", "Volume", "Tidak ada"])
            show_vp = col_i3.checkbox("Tampilkan Support/Resisten", value=True)
            
        days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
        tech_id = dict(zip(market_df["label"], market_df["id"]))[tech_label]
        
        try:
            hist = demo.get_demo_price_history(market_df[market_df["id"]==tech_id].iloc[0]["current_price"]) if demo_mode else cached_price_history(tech_id, currency, days_map[tf])
            
            if "MA 9" in show_ma: hist["ma9"] = indicators.sma(hist["price"], 9)
            if "MA 20" in show_ma: hist["ma20"] = indicators.sma(hist["price"], 20)
            if "MA 50" in show_ma: hist["ma50"] = indicators.sma(hist["price"], 50)
            if "MA 200" in show_ma: hist["ma200"] = indicators.sma(hist["price"], 200)
            
            if show_osc == "RSI": hist["osc"] = indicators.rsi(hist["price"], 14)
            elif show_osc == "Volume": hist["osc"] = hist["volume"]
            else: hist["osc"] = None

            if show_osc != "Tidak ada":
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            else:
                fig = make_subplots(rows=1, cols=1)
                
            fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["price"], name="Price", line=dict(color="#171827", width=1.5)), row=1, col=1)
            
            if "MA 9" in show_ma: fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma9"], name="MA 9", line=dict(color="#FFB300", width=1)), row=1, col=1)
            if "MA 20" in show_ma: fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma20"], name="MA 20", line=dict(color="#6C35D9", width=1)), row=1, col=1)
            if "MA 50" in show_ma: fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma50"], name="MA 50", line=dict(color="#00E676", width=1)), row=1, col=1)
            if "MA 200" in show_ma: fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma200"], name="MA 200", line=dict(color="#D83D50", width=1)), row=1, col=1)
            
            if show_vp:
                max_p = hist["price"].max()
                min_p = hist["price"].min()
                fig.add_hline(y=max_p, line_dash="dash", line_color="#D83D50", opacity=0.5, annotation_text="Resisten", row=1, col=1)
                fig.add_hline(y=min_p, line_dash="dash", line_color="#16834A", opacity=0.5, annotation_text="Support", row=1, col=1)
            
            if show_osc != "Tidak ada" and hist["osc"] is not None:
                if show_osc == "Volume":
                    fig.add_trace(go.Bar(x=hist["waktu"], y=hist["osc"], name="Volume", marker_color="#E9E6F0"), row=2, col=1)
                else:
                    fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["osc"], name=show_osc, line=dict(color="#171827", width=1.5)), row=2, col=1)
                    if show_osc == "RSI":
                        fig.add_hline(y=70, line_dash="dash", line_color="#D83D50", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="#16834A", row=2, col=1)

            fig.update_layout(template="plotly_white", height=600, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e: st.warning(f"Gagal memuat data teknikal: {e}")

elif current_page_name == "📒 Trading Journal":
    st.markdown("<h1>Trading Journal</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.info("Fitur Trading Journal siap digunakan.")

elif current_page_name == "🔔 Price Alerts":
    st.markdown("<h1>Price Alerts</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.info("Fitur Price Alerts siap digunakan.")

elif current_page_name == "💼 Portfolio":
    st.markdown("<h1>Portfolio</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.info("Fitur Portofolio siap digunakan.")

elif current_page_name == "💱 Converter":
    st.markdown("<h1>Converter</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.info("Fitur Converter siap digunakan.")

elif current_page_name == "⭐ Watchlist":
    st.markdown("<h1>Watchlist</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.info("Fitur Watchlist siap digunakan.")

elif current_page_name == "👑 Admin Panel" and is_dev:
    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.info("Admin Panel siap digunakan.")