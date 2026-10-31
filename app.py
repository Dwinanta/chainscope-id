"""
ChainScope ID - Premium Light Mode (Full Features & Indodax Chart)
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

@st.cache_data(ttl=60, show_spinner=False)
def cached_indodax_klines(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    return api.fetch_indodax_klines(symbol, interval, limit)

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

# 4. SIDEBAR & NAVIGASI
if "current_page" not in st.session_state:
    st.session_state.current_page = "market-overview"

with st.sidebar:
    st.markdown("""
        <div class='logo-container'>
            <div style='background: #6C35D9; padding: 6px 10px; border-radius: 8px;'>
                <span style='color:white; font-size:1.2rem;'>⚡</span>
            </div>
            <span style='font-size:1.2rem; font-weight:800; color:#171827;'>ChainScope <span style='color:#6C35D9;'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-color: #E9E6F0;'>", unsafe_allow_html=True)

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

    for url_key, display_name in menu_config.items():
        is_active = (st.session_state.current_page == url_key)
        if st.button(display_name, use_container_width=True, key=f"btn_{url_key}", type="primary" if is_active else "secondary"):
            st.session_state.current_page = url_key
            st.rerun()

    st.markdown("---")
    currency = st.radio("Mata uang:", options=["IDR", "USD"], horizontal=True)
    coin_count = st.selectbox("Tampilkan Koin:", options=[50, 100, 250], index=0)
    demo_mode = st.checkbox("Mode Demo", value=False)

current_page = st.session_state.current_page

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
# ROUTING HALAMAN
# ===========================================================================
if current_page == "market-overview":
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
                hist_df = cached_price_history(chart_coin_id, currency, days_map[tf])
                fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#6C35D9'])
                fig_main.update_traces(fillcolor='rgba(108, 53, 217, 0.08)', line=dict(width=1.5))
                fig_main.update_layout(margin=dict(l=0, r=0, t=5, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, tickfont=dict(size=10)), yaxis=dict(showgrid=True, gridcolor='#E9E6F0', tickfont=dict(size=10)))
                st.plotly_chart(fig_main, use_container_width=True, config={'scrollZoom': True})
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

elif current_page == "market-data":
    st.markdown("<h1>Market Data</h1>", unsafe_allow_html=True)
    
    # --- FITUR BARU: PERBANDINGAN HARGA EXCHANGE LOKAL ---
    with st.container(border=True):
        st.markdown("#### 📊 Perbandingan Harga Exchange Lokal (IDR)")
        exchange_data = api.fetch_exchange_prices()
        
        col_indodax, col_upbit = st.columns(2)
        with col_indodax:
            st.markdown("**Indodax**")
            btc_indodax = exchange_data["Indodax"]["BTC"]
            eth_indodax = exchange_data["Indodax"]["ETH"]
            st.metric("BTC / IDR", f"Rp {btc_indodax:,.0f}" if btc_indodax else "N/A")
            st.metric("ETH / IDR", f"Rp {eth_indodax:,.0f}" if eth_indodax else "N/A")
            
        with col_upbit:
            st.markdown("**Upbit Indonesia**")
            btc_upbit = exchange_data["Upbit Indonesia"]["BTC"]
            eth_upbit = exchange_data["Upbit Indonesia"]["ETH"]
            st.metric("BTC / IDR", f"Rp {btc_upbit:,.0f}" if btc_upbit else "N/A")
            st.metric("ETH / IDR", f"Rp {eth_upbit:,.0f}" if eth_upbit else "N/A")
            
        # Hitung selisih jika keduanya ada
        if btc_indodax and btc_upbit:
            diff_pct = ((btc_upbit - btc_indodax) / btc_indodax) * 100
            st.caption(f"Selisih Harga BTC: {diff_pct:+.2f}% (Upbit vs Indodax)")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- TABEL DATA PASAR (Kode Lama) ---
    st.markdown("<p>Klik pada baris koin untuk melihat analisis teknikalnya.</p>", unsafe_allow_html=True)
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
            st.session_state.selected_technical_coin = selected_coin_id
            st.session_state.current_page = "technical-analysis"
            st.rerun()

elif current_page == "technical-analysis":
    st.markdown("<h1>Technical Analysis</h1>", unsafe_allow_html=True)
    
    default_coin = st.session_state.get("selected_technical_coin", "bitcoin")
    default_idx = int(market_df[market_df["id"] == default_coin].index[0]) if default_coin in market_df["id"].values else 0
    
    tech_label = st.selectbox("Pilih Koin:", market_df["label"].tolist(), index=default_idx)
    
    # Ambil simbol (misal: "BTC")
    symbol_upper = dict(zip(market_df["label"], market_df["symbol_upper"]))[tech_label]
    
    from chainscope.chart_component import render_modern_chart
    render_modern_chart(symbol=symbol_upper, height=680)

elif current_page == "trading-journal":
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

elif current_page == "price-alerts":
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

elif current_page == "portfolio":
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

elif current_page == "converter":
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

elif current_page == "watchlist":
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

elif current_page == "admin-panel" and is_dev:
    st.markdown("<h1>Admin Panel</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        all_users = admin.get_all_users()
        if not all_users:
            st.info("Belum ada user yang terdaftar.")
        else:
            df_users = pd.DataFrame(all_users)
            if "subscription_end" in df_users.columns:
                df_users["subscription_end"] = df_users["subscription_end"].fillna("—").str[:10]
                
            display_cols = ["email", "role", "subscription_tier", "subscription_end"]
            st.dataframe(df_users[display_cols].rename(columns={"email": "Email", "role": "Role", "subscription_tier": "Plan", "subscription_end": "Berakhir Pada"}), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### Kelola User")
            
            user_emails = [u["email"] for u in all_users]
            selected_email = st.selectbox("Pilih user untuk diedit:", options=user_emails)
            
            if selected_email:
                selected_user = next((u for u in all_users if u["email"] == selected_email), None)
                uid = selected_user["id"]
                
                col_r, col_t, col_d = st.columns(3)
                
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
                        
                with col_d:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    new_end = st.date_input("Perpanjang s/d:")
                    if st.button("Set Expired"):
                        admin.update_user_subscription(uid, new_tier, str(new_end))
                        st.success("Masa aktif diperbarui.")
                        st.rerun()