"""
ChainScope ID - Premium Light Mode (Full Features)
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

# 2. CEK AUTENTIKASI
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

# 4. SIDEBAR
with st.sidebar:
    # Logo (Rapat ke atas)
    st.markdown("""
        <div style='display:flex; align-items:center; gap:8px; margin-bottom: 20px; padding-left: 0px; margin-top: 10px;'>
            <div style='background: #6C35D9; padding: 6px 10px; border-radius: 8px;'>
                <span style='color:white; font-size:1.2rem;'>⚡</span>
            </div>
            <span style='font-size:1.2rem; font-weight:800; color:#171827;'>ChainScope <span style='color:#6C35D9;'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu_options = [
        "🏠 Market Overview", "📊 Market Data", "📒 Trading Journal", 
        "🔔 Price Alerts", "📉 Technical Analysis", "💼 Portfolio", 
        "💱 Converter", "⭐ Watchlist"
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
# MENU 1: MARKET OVERVIEW (Dashboard Utama)
# ===========================================================================
if menu == "🏠 Market Overview":
    col_title, col_search, col_profile = st.columns([2.5, 2, 0.5])
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>Market Overview</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.9rem; margin-top:5px;'>Real-time crypto market data and insights</p>", unsafe_allow_html=True)
    with col_search:
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input("Search", placeholder="🔍 Search coins...", label_visibility="collapsed")
    with col_profile:
        with st.popover("👤"):
            st.markdown(f"### 👤 {user.email}")
            st.markdown(f"**Plan:** {sub_tier}")
            if end_date: st.markdown(f"**Aktif s/d:** {end_date[:10]}")
            if is_dev: st.success("👑 Dev Mode")
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True, type="primary"):
                auth.logout_user()

    st.markdown("<br>", unsafe_allow_html=True)

    # Kartu Top 4
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

    # Grafik & Movers
    col_chart, col_right = st.columns([2.5, 1])
    with col_chart:
        with st.container(border=True):
            c_t1, c_t2 = st.columns([2, 1.5])
            c_t1.markdown("<p style='font-weight:700; color:#171827; font-size:1rem; margin-bottom:0;'>Market Chart (BTC)</p>", unsafe_allow_html=True)
            with c_t2:
                tf = st.segmented_control("Timeframe", ["1D", "7D", "1M", "1Y"], default="1D", label_visibility="collapsed")
                if not tf: tf = "1D"
            
            days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
            btc_row = market_df[market_df["id"] == "bitcoin"].iloc[0]
            total_mcap = market_df["market_cap"].sum()
            mcap_str = f"Rp{total_mcap / 1_000_000_000_000_000:.2f} Kuadriliun" if currency == "IDR" else f"${total_mcap / 1_000_000_000_000:.2f} T"

            st.markdown(f"<p style='font-size:0.75rem; color:#77788A; margin-top:5px; margin-bottom:0;'>Total Market Cap</p>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin-top:0;'>{mcap_str}</h2>", unsafe_allow_html=True)
            
            try:
                hist_df = demo.get_demo_price_history(btc_row["current_price"]) if demo_mode else cached_price_history("bitcoin", currency, days_map[tf])
                fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#6C35D9'])
                fig_main.update_traces(fillcolor='rgba(108, 53, 217, 0.08)', line=dict(width=1.5))
                fig_main.update_layout(margin=dict(l=0, r=0, t=5, b=0), height=180, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, tickfont=dict(size=10)), yaxis=dict(showgrid=True, gridcolor='#E9E6F0', tickfont=dict(size=10)))
                st.plotly_chart(fig_main, use_container_width=True)
            except Exception: pass

    with col_right:
        with st.container(border=True):
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(4)
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(4)
            html = f"<p style='font-weight:700; font-size:0.95rem; color:#171827; margin-bottom:10px;'>Top Gainers ⚡</p>"
            for _, r in gainers.iterrows():
                html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'><div style='display:flex; gap:6px;'><img src='{r['image']}' width='16'><span style='font-size:0.75rem; font-weight:600;'>{r['symbol_upper']}</span></div><span class='text-green'>+{r['price_change_percentage_24h']:.2f}%</span></div>"
            html += f"<hr style='margin:8px 0;'><p style='font-weight:700; font-size:0.95rem; color:#171827; margin-bottom:10px;'>Top Losers ⚡</p>"
            for _, r in losers.iterrows():
                html += f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'><div style='display:flex; gap:6px;'><img src='{r['image']}' width='16'><span style='font-size:0.75rem; font-weight:600;'>{r['symbol_upper']}</span></div><span class='text-red'>{r['price_change_percentage_24h']:.2f}%</span></div>"
            st.markdown(html, unsafe_allow_html=True)

# ===========================================================================
# MENU 2: MARKET DATA (Tabel Lengkap)
# ===========================================================================
elif menu == "📊 Market Data":
    st.markdown("<h1>Market Data</h1>", unsafe_allow_html=True)
    st.markdown("<p>Semua koin beserta filter dan data lengkap.</p><br>", unsafe_allow_html=True)
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
        st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={"Coin": st.column_config.TextColumn("Coin", width="medium"), "24h %": st.column_config.TextColumn("24h %", width="small")})

# ===========================================================================
# MENU 3: TRADING JOURNAL
# ===========================================================================
elif menu == "📒 Trading Journal":
    st.markdown("<h1>Trading Journal</h1>", unsafe_allow_html=True)
    
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
                if st.form_submit_button("Simpan Transaksi", use_container_width=True):
                    sym = market_df[market_df["id"]==t_coin]["symbol_upper"].values[0]
                    db.add_trade(user.id, t_coin, sym, t_side, t_amount, t_price, str(t_date))
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
                    if st.button("Proses CSV", use_container_width=True):
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
            st.dataframe(df_trades[["trade_time", "symbol", "side", "amount", "price_usd"]], use_container_width=True, hide_index=True)
            if st.button("🗑️ Hapus Semua Transaksi", type="secondary"):
                db.delete_all_user_trades(user.id)
                st.rerun()
        else:
            st.info("Belum ada transaksi.")

# ===========================================================================
# MENU 4: PRICE ALERTS
# ===========================================================================
elif menu == "🔔 Price Alerts":
    st.markdown("<h1>Price Alerts</h1>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### Buat Alert Baru")
        with st.form("new_alert", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            a_coin = c1.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
            a_cond = c2.selectbox("Kondisi", ["above", "below"])
            a_price = c3.number_input("Target Harga", min_value=0.01)
            if st.form_submit_button("Tambah Alert", use_container_width=True):
                sym = market_df[market_df["id"]==a_coin]["symbol_upper"].values[0]
                db.add_alert(user.id, a_coin, sym, a_cond, a_price, currency)
                st.success("Alert dibuat!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Daftar Alert")
        alerts = db.get_user_alerts(user.id)
        if alerts:
            for a in alerts:
                st.markdown(f"**{a['symbol']}** {a['condition']} {a['target_price']} {a['currency']} — {'Triggered' if not a['is_active'] else 'Waiting'}")
        else:
            st.info("Belum ada alert aktif.")

# ===========================================================================
# MENU 5: TECHNICAL ANALYSIS
# ===========================================================================
elif menu == "📉 Technical Analysis":
    st.markdown("<h1>Technical Analysis</h1>", unsafe_allow_html=True)
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        tech_label = c1.selectbox("Koin:", market_df["label"].tolist(), label_visibility="collapsed")
        chart_mode = c2.radio("Mode:", ["Line", "Candlestick"], horizontal=True)
        tf = c3.selectbox("Timeframe", ["1D", "7D", "1M", "1Y"], index=1, label_visibility="collapsed")
        
        days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
        tech_id = dict(zip(market_df["label"], market_df["id"]))[tech_label]
        
        try:
            hist = demo.get_demo_price_history(market_df[market_df["id"]==tech_id].iloc[0]["current_price"]) if demo_mode else cached_price_history(tech_id, currency, days_map[tf])
            ohlc = cached_ohlc(tech_id, currency, days_map[tf]) if chart_mode == "Candlestick" and not demo_mode else None
            hist["ma20"] = indicators.sma(hist["price"], 20)
            
            fig = go.Figure()
            if ohlc is not None and not ohlc.empty:
                fig.add_trace(go.Candlestick(x=ohlc["waktu"], open=ohlc["open"], high=ohlc["high"], low=ohlc["low"], close=ohlc["close"], name="OHLC"))
            else:
                fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["price"], name="Price", line=dict(color="#6C35D9")))
                
            fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma20"], name="MA20", line=dict(color="#FFB300")))
            fig.update_layout(template="plotly_white", height=500, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        except Exception: st.warning("Gagal memuat data teknikal.")

# ===========================================================================
# MENU 6: PORTFOLIO
# ===========================================================================
elif menu == "💼 Portfolio":
    st.markdown("<h1>Portfolio</h1>", unsafe_allow_html=True)
    trades = db.get_user_trades(user.id)
    
    if not trades:
        st.info("Belum ada transaksi di Trading Journal.")
    else:
        pf_df = journal_calc.calculate_portfolio_from_trades(trades)
        if pf_df.empty:
            st.warning("Semua aset sudah terjual.")
        else:
            pf_df = pf_df.merge(market_df[["id", "current_price"]], left_on="coin_id", right_on="id", how="left")
            rate = cached_usd_idr_rate() if currency == "IDR" else 1.0
            if demo_mode: rate = config.DEMO_USD_TO_IDR if currency == "IDR" else 1.0
            
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
                display_df = pd.DataFrame({
                    "Koin": pf_df["symbol"],
                    "Jumlah": pf_df["amount"].map(lambda x: f"{x:.4f}"),
                    "Harga Rata2": pf_df["avg_buy_price"].map(lambda v: formatting.format_money(v, currency)),
                    "Nilai Kini": pf_df["current_value"].map(lambda v: formatting.format_money(v, currency)),
                    "P&L": pf_df["pnl"].map(lambda v: formatting.format_money(v, currency)),
                })
                st.dataframe(display_df, use_container_width=True, hide_index=True)

# ===========================================================================
# MENU 7: CONVERTER
# ===========================================================================
elif menu == "💱 Converter":
    st.markdown("<h1>Converter</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        rate = cached_usd_idr_rate() if currency == "IDR" else 1.0
        price_map = converter.build_price_map(market_df, currency, rate)
        col1, col2 = st.columns(2)
        from_asset = col1.selectbox("Dari:", ["USD", "IDR"] + market_df["id"].tolist())
        to_asset = col2.selectbox("Ke:", ["USD", "IDR"] + market_df["id"].tolist(), index=1)
        amount = st.number_input("Jumlah:", min_value=0.0, value=1.0)
        res = converter.convert(amount, from_asset, to_asset, price_map)
        if res: st.metric("Hasil", formatting.format_money(res, currency))

# ===========================================================================
# MENU 8: WATCHLIST
# ===========================================================================
elif menu == "⭐ Watchlist":
    st.markdown("<h1>Watchlist</h1>", unsafe_allow_html=True)
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
            st.dataframe(wl_df[["name", "symbol_upper", "current_price"]].rename(columns={"name":"Nama", "symbol_upper":"Simbol", "current_price":"Harga"}), use_container_width=True, hide_index=True)

# ===========================================================================
# MENU 9: ADMIN PANEL
# ===========================================================================
elif menu == "👑 Admin Panel" and is_dev:
    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        all_users = admin.get_all_users()
        df_users = pd.DataFrame(all_users)
        st.dataframe(df_users[["email", "role", "subscription_tier", "subscription_end"]], use_container_width=True, hide_index=True)