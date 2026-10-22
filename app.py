"""
ChainScope ID - Premium Light Mode
"""
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chainscope import (
    ui, api, auth, compare, config, converter, db, demo, formatting, 
    indicators, journal_calc, report, search, telegram, admin
)

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="ChainScope ID", page_icon="📈", layout="wide")
ui.apply_premium_theme()

# 2. CEK AUTENTIKASI
auth.check_session()
if "user" not in st.session_state or st.session_state.user is None:
    auth.show_auth_page()
    st.stop()

user = st.session_state.user
user_profile = db.get_user_profile(user.id)
is_dev = user_profile.get("role") == "dev"
sub_tier = user_profile.get("subscription_tier", "free").title()

# 3. FUNGSI CACHE API
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_market_data(vs_currency: str, limit: int) -> pd.DataFrame:
    return api.fetch_market_data(vs_currency, limit)

@st.cache_data(ttl=300, show_spinner=False)
def cached_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_price_history(coin_id, vs_currency, days)

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

# 4. SIDEBAR
with st.sidebar:
    # Logo
    st.markdown("""
        <div style='display:flex; align-items:center; gap:10px; margin-bottom: 30px; padding-left: 10px;'>
            <div style='background: #6C35D9; padding: 8px 12px; border-radius: 10px;'>
                <span style='color:white; font-size:1.5rem;'>⚡</span>
            </div>
            <span style='font-size:1.4rem; font-weight:800; color:#171827;'>ChainScope <span style='color:#6C35D9;'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"👤 **{user.email}**")
    end_date = user_profile.get("subscription_end")
    if end_date:
        st.info(f"🌟 Plan: **{sub_tier}**\n\nAktif s/d: {end_date[:10]}")
    else:
        st.info(f"🌟 Plan: **{sub_tier}**")
        
    if is_dev:
        st.success("👑 Dev Mode Aktif")
    
    if st.button("🚪 Logout", use_container_width=True):
        auth.logout_user()

    st.markdown("---")
    
    menu_options = [
        "🏠 Market Overview", "📒 Trading Journal", "🔔 Price Alerts", 
        "📉 Technical Analysis", "📈 Compare", "💼 Portfolio", 
        "💱 Converter", "⭐ Watchlist", "🚀 Gainers & Losers", 
        "📄 Laporan PDF"
    ]
    if is_dev: menu_options.append("👑 Admin Panel")
    
    menu = st.radio("Navigasi", menu_options, label_visibility="collapsed")

    st.markdown("---")
    currency = st.radio("Mata uang:", options=["IDR", "USD"], horizontal=True)
    coin_count = st.selectbox("Tampilkan Koin:", options=[50, 100, 250], index=0)
    demo_mode = st.checkbox("Mode Demo", value=False)

# 5. AMBIL DATA PASAR
market_df = None
data_source = "LIVE"

if demo_mode:
    market_df = demo.get_demo_market_data(limit=min(coin_count, 50), currency=currency)
    data_source = "DEMO"
else:
    try:
        market_df = cached_market_data(currency, coin_count)
    except Exception:
        market_df = demo.get_demo_market_data(limit=min(coin_count, 50), currency=currency)
        data_source = "DEMO (Fallback)"

market_df = market_df.copy()
market_df["symbol_upper"] = market_df["symbol"].astype(str).str.upper()
market_df["label"] = market_df["name"] + " (" + market_df["symbol_upper"] + ")"

# ===========================================================================
# MENU 1: MARKET OVERVIEW
# ===========================================================================
if menu == "🏠 Market Overview":
    # --- 1. HEADER BAR ---
    col_title, col_search = st.columns([2.5, 1.5])
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>Market Overview</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:1rem; margin-top:5px;'>Real-time crypto market data and insights</p>", unsafe_allow_html=True)
    with col_search:
        st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input("Search", placeholder="🔍 Search coins, pairs, or categories...", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. KARTU TOP 4 ---
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
                    <div style='display:flex; gap:10px; align-items:center;'>
                        <img src="{row['image']}" width="28" height="28">
                        <div>
                            <div style='font-weight:700; font-size:1rem; color:#171827;'>{row['name']}</div>
                            <div style='font-size:0.75rem; color:#77788A;'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                    <div style='margin-top:20px;'>
                        <div style='font-weight:800; font-size:1.3rem; color:#171827;'>{formatting.format_money(row['current_price'], currency)}</div>
                        <div style='color:{color}; font-size:0.85rem; font-weight:600; margin-top:5px;'>{icon} {row['price_change_percentage_24h']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c_right:
                    sparkline_prices = row.get("sparkline_in_7d", {}).get("price", [])
                    if sparkline_prices:
                        fig = go.Figure(go.Scatter(y=sparkline_prices, mode='lines', line=dict(color=color, width=2)))
                        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=80, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. GRAFIK BESAR & GAINERS/LOSERS ---
    col_chart, col_right_side = st.columns([2.3, 1]) # Lebar grafik ditambah, kanan dipersempit
    
    with col_chart:
        with st.container(border=True):
            c_t1, c_t2 = st.columns([2, 1.5])
            c_t1.markdown("<p style='font-weight:700; color:#171827; font-size:1.1rem; margin-bottom:0;'>Market Overview <span style='color:#aaa;'>ⓘ</span></p>", unsafe_allow_html=True)
            
            with c_t2:
                timeframe = st.segmented_control("Timeframe", ["1D", "7D", "1M", "1Y"], default="1D", label_visibility="collapsed")
                if not timeframe: timeframe = "1D"
            
            days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
            btc_row = market_df[market_df["id"] == "bitcoin"].iloc[0]
            total_mcap = market_df["market_cap"].sum()
            
            mcap_str = f"Rp{total_mcap / 1_000_000_000_000_000:.2f} Kuadriliun" if currency == "IDR" else f"${total_mcap / 1_000_000_000_000:.2f} T"

            st.markdown(f"<p style='font-size:0.85rem; color:#77788A; margin-top:15px; margin-bottom:0;'>Total Market Cap</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin:0;'>{mcap_str}</h2>", unsafe_allow_html=True)
            st.markdown(f"<span class='text-green'>▲ {btc_row['price_change_percentage_24h']:.2f}% (24h)</span>", unsafe_allow_html=True)
            
            try:
                hist_df = demo.get_demo_price_history(btc_row["current_price"]) if demo_mode else cached_price_history("bitcoin", currency, days_map[timeframe])
                fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#6C35D9'])
                fig_main.update_traces(fillcolor='rgba(108, 53, 217, 0.08)', line=dict(width=2))
                fig_main.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0), height=280,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#77788A', tickformat="%H:%M"), 
                    yaxis=dict(showgrid=True, gridcolor='#E9E6F0', color='#77788A')
                )
                st.plotly_chart(fig_main, use_container_width=True)
            except Exception: st.warning("⚠️ Gagal memuat grafik.")

    with col_right_side:
        # --- KOTAK GAINERS ---
        with st.container(border=True):
            st.markdown("<p style='font-weight:700; font-size:1.1rem; color:#171827; margin-bottom:15px;'>Top Gainers ⚡</p>", unsafe_allow_html=True)
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(5)
            for _, row in gainers.iterrows():
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
                    <div style='display:flex; gap:10px; align-items:center;'>
                        <img src="{row['image']}" width="24" height="24">
                        <div>
                            <div style='font-weight:700; font-size:0.85rem; color:#171827;'>{row['name']}</div>
                            <div style='font-size:0.7rem; color:#77788A;'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                    <div style='text-align:right;'>
                        <div class='text-green'>+{row['price_change_percentage_24h']:.2f}%</div>
                        <div style='font-size:0.7rem; color:#77788A;'>{formatting.format_money(row['current_price'], currency)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- KOTAK LOSERS ---
        with st.container(border=True):
            st.markdown("<p style='font-weight:700; font-size:1.1rem; color:#171827; margin-bottom:15px;'>Top Losers ⚡</p>", unsafe_allow_html=True)
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(5)
            for _, row in losers.iterrows():
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
                    <div style='display:flex; gap:10px; align-items:center;'>
                        <img src="{row['image']}" width="24" height="24">
                        <div>
                            <div style='font-weight:700; font-size:0.85rem; color:#171827;'>{row['name']}</div>
                            <div style='font-size:0.7rem; color:#77788A;'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                    <div style='text-align:right;'>
                        <div class='text-red'>{row['price_change_percentage_24h']:.2f}%</div>
                        <div style='font-size:0.7rem; color:#77788A;'>{formatting.format_money(row['current_price'], currency)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 4. MARKET TABLE ---
    with st.container(border=True):
        st.markdown("<p style='font-weight:700; font-size:1.2rem; color:#171827; margin-bottom:10px;'>Market Table</p>", unsafe_allow_html=True)
        
        filtered_df = search.filter_coins(market_df, search_query)
        table_source = filtered_df if not filtered_df.empty else market_df
        
        display_df = pd.DataFrame({
            "#": range(1, len(table_source) + 1),
            "Coin": table_source["name"],
            "Ticker": table_source["symbol_upper"],
            "Price": table_source["current_price"].map(lambda v: formatting.format_money(v, currency)),
            "24h %": table_source["price_change_percentage_24h"].map(lambda v: f"{v:.2f}%"),
            "24h Volume": table_source["total_volume"].map(lambda v: formatting.format_money(v, currency)),
            "Market Cap": table_source["market_cap"].map(lambda v: formatting.format_money(v, currency)),
        })

        st.dataframe(
            display_df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Coin": st.column_config.TextColumn("Coin", width="medium"),
                "24h %": st.column_config.TextColumn("24h %", width="small"),
            }
        )

# ===========================================================================
# MENU LAINNYA (Bisa diisi kembali kodemu yang lama)
# ===========================================================================
elif menu == "📒 Trading Journal":
    st.info("Fitur Trading Journal siap digunakan.")
elif menu == "🔔 Price Alerts":
    st.info("Fitur Price Alerts siap digunakan.")
elif menu == "📉 Technical Analysis":
    st.info("Fitur Teknikal siap digunakan.")
elif menu == "📈 Compare":
    st.info("Fitur Perbandingan siap digunakan.")
elif menu == "💼 Portfolio":
    st.info("Fitur Portofolio siap digunakan.")
elif menu == "💱 Converter":
    st.info("Fitur Konverter siap digunakan.")
elif menu == "⭐ Watchlist":
    st.info("Fitur Watchlist siap digunakan.")
elif menu == "🚀 Gainers & Losers":
    st.info("Fitur Movers siap digunakan.")
elif menu == "📄 Laporan PDF":
    st.info("Fitur PDF siap digunakan.")
elif menu == "👑 Admin Panel" and is_dev:
    st.info("Admin Panel siap digunakan.")