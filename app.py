"""
ChainScope ID - Premium Trading Terminal (Full Features)
"""
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from chainscope import (
    ui, api, auth, compare, config, converter, db, demo, formatting, 
    indicators, journal_calc, portfolio, report, search, telegram, admin
)

# 1. KONFIGURASI HALAMAN & TEMA
st.set_page_config(page_title="ChainScope ID", page_icon="📈", layout="wide")
ui.apply_premium_theme()

# 2. CEK AUTENTIKASI
auth.check_session() # <-- TAMBAHKAN BARIS INI UNTUK MEMBACA URL

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
    st.markdown("""
        <div class="logo-container">
            <div class="logo-icon">⚡</div>
            <div class="logo-text">ChainScope <span>ID</span></div>
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
    
    # Menggunakan ikon SVG inline untuk tampilan menu
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
    except Exception as exc:
        # JIKA API LIMIT, OTOMATIS PINDAH KE DATA DEMO AGAR APLIKASI TIDAK MATI
        market_df = demo.get_demo_market_data(limit=min(coin_count, 50), currency=currency)
        data_source = "DEMO (Fallback)"
        st.warning(f"⚠️ Batas API CoinGecko tercapai (429). Menampilkan data demo sementara.")

if market_df is None or market_df.empty:
    st.error("Gagal memuat data pasar sama sekali.")
    st.stop()

# PASTIKAN 4 BARIS INI ADA
market_df = market_df.copy()
market_df["symbol_upper"] = market_df["symbol"].astype(str).str.upper()
market_df["label"] = market_df["name"] + " (" + market_df["symbol_upper"] + ")"
unit_label = f"Harga ({currency})"
# ===========================================================================
# MENU 1: RINGKASAN (PREMIUM OVERVIEW)
# ===========================================================================
if menu == "🏠 Market Overview":
    # --- HEADER BAR ---
    col_title, col_search = st.columns([3, 1])
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>Market Overview</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#77788A; font-size:0.95rem;'>Real-time crypto market data and insights</p>", unsafe_allow_html=True)
    with col_search:
        search_query = st.text_input("🔍 Search coins...", placeholder="Search coins, pairs, or categories...", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 1: KARTU TOP 4 ---
    top4_df = market_df.head(4)
    cols = st.columns(4)
    for col, (_, row) in zip(cols, top4_df.iterrows()):
        with col:
            with st.container(border=True):
                color = "#16834A" if row['price_change_percentage_24h'] >= 0 else "#D83D50"
                icon = "▲" if row['price_change_percentage_24h'] >= 0 else "▼"
                
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='display:flex; gap:10px; align-items:center;'>
                        <img src="{row['image']}" width="32" height="32" style="border-radius:50%;">
                        <div>
                            <div style='font-weight:600; font-size:1rem; color:#171827;'>{row['name']}</div>
                            <div style='font-size:0.75rem; color:#77788A;'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                </div>
                <h2 style='margin-top:15px; margin-bottom:5px;'>{formatting.format_money(row['current_price'], currency)}</h2>
                <span style='color:{color}; font-size:0.85rem; font-weight:600;'>{icon} {row['price_change_percentage_24h']:.2f}%</span>
                """, unsafe_allow_html=True)
                
                sparkline_prices = row.get("sparkline_in_7d", {}).get("price", [])
                if sparkline_prices:
                    fig = go.Figure(go.Scatter(y=sparkline_prices, mode='lines', line=dict(color=color, width=2)))
                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=60, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 2: GRAFIK BESAR & GAINERS/LOSERS ---
    col_chart, col_movers = st.columns([2.2, 1])
    
    with col_chart:
        with st.container(border=True):
            c_t1, c_t2 = st.columns([3, 2])
            c_t1.markdown("#### Market Overview")
            
            # Menggunakan Market Cap Total sebagai pengganti (karena data global tidak selalu tersedia di API gratis)
            # Kita ambil BTC chart sebagai proxy pergerakan market
            btc_row = market_df[market_df["id"] == "bitcoin"].iloc[0]
            total_mcap = market_df["market_cap"].sum()
            
            c_t1.markdown(f"<h2 style='margin:0;'>{formatting.format_money(total_mcap, currency)}</h2>", unsafe_allow_html=True)
            c_t1.markdown(f"<span class='text-green'>▲ {btc_row['price_change_percentage_24h']:.2f}% (24h)</span>", unsafe_allow_html=True)
            
            timeframe = c_t2.radio("Timeframe", ["1D", "7D", "1M", "1Y"], horizontal=True, label_visibility="collapsed")
            days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
            
            try:
                hist_df = demo.get_demo_price_history(btc_row["current_price"]) if demo_mode else cached_price_history("bitcoin", currency, days_map[timeframe])
                fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#6C35D9'])
                fig_main.update_traces(fillcolor='rgba(108, 53, 217, 0.1)', line=dict(width=3))
                fig_main.update_layout(
                    margin=dict(l=0, r=0, t=20, b=0), height=280,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#77788A'), yaxis=dict(showgrid=True, gridcolor='#E9E6F0', color='#77788A')
                )
                st.plotly_chart(fig_main, use_container_width=True)
            except Exception: st.warning("⚠️ Gagal memuat grafik.")

    with col_movers:
        with st.container(border=True):
            st.markdown("#### Top Gainers ⚡")
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(5)
            for _, row in gainers.iterrows():
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
                    <div style='display:flex; gap:10px; align-items:center;'>
                        <img src="{row['image']}" width="24" height="24">
                        <div>
                            <div style='font-weight:600; font-size:0.85rem; color:#171827;'>{row['name']}</div>
                            <div style='font-size:0.7rem; color:#77788A;'>{row['symbol_upper']}</div>
                        </div>
                    </div>
                    <div style='text-align:right;'>
                        <div class='text-green'>+{row['price_change_percentage_24h']:.2f}%</div>
                        <div style='font-size:0.7rem; color:#77788A;'>{formatting.format_money(row['current_price'], currency)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:15px 0; border-color:#E9E6F0;'>", unsafe_allow_html=True)
            st.markdown("#### Top Losers ⚡")
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(5)
            for _, row in losers.iterrows():
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>
                    <div style='display:flex; gap:10px; align-items:center;'>
                        <img src="{row['image']}" width="24" height="24">
                        <div>
                            <div style='font-weight:600; font-size:0.85rem; color:#171827;'>{row['name']}</div>
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

    # --- ROW 3: TABEL DATA PASAR ---
    with st.container(border=True):
        st.markdown("#### Market Table")
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
# MENU 2: TRADING JOURNAL
# ===========================================================================
elif menu == "📒 Trading Journal":
    st.subheader("📒 Trading Journal")
    col_manual, col_csv = st.columns(2)
    with col_manual:
        st.markdown("**Input Manual**")
        with st.form("manual_trade_form", clear_on_submit=True):
            t_coin = st.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
            t_side = st.selectbox("Aksi", ["buy", "sell"])
            t_date = st.date_input("Tanggal", datetime.now())
            t_amount = st.number_input("Jumlah Koin", min_value=0.00000001, format="%.8f")
            t_price = st.number_input("Harga (USD)", min_value=0.01)
            if st.form_submit_button("Simpan Transaksi"):
                sym = market_df[market_df["id"]==t_coin]["symbol_upper"].values[0]
                db.add_trade(user.id, t_coin, sym, t_side, t_amount, t_price, str(t_date))
                st.success("Transaksi tersimpan!")
                st.rerun()

    with col_csv:
        st.markdown("**Import CSV**")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        if uploaded_file:
            try:
                df_csv = pd.read_csv(uploaded_file)
                map_coin = st.selectbox("Kolom Koin", df_csv.columns)
                map_side = st.selectbox("Kolom Aksi", df_csv.columns)
                map_amount = st.selectbox("Kolom Jumlah", df_csv.columns)
                map_price = st.selectbox("Kolom Harga", df_csv.columns)
                map_date = st.selectbox("Kolom Tanggal", df_csv.columns)
                if st.button("Proses CSV", use_container_width=True):
                    success_count = 0
                    for _, row in df_csv.iterrows():
                        c_id = str(row[map_coin]).lower()
                        valid = market_df[market_df["id"].str.contains(c_id, case=False) | market_df["symbol"].str.contains(c_id, case=False)]
                        if not valid.empty:
                            db.add_trade(user.id, valid.iloc[0]["id"], valid.iloc[0]["symbol_upper"], str(row[map_side]).lower(), float(row[map_amount]), float(row[map_price]), str(row[map_date]), source="csv")
                            success_count += 1
                    st.success(f"Import {success_count} transaksi!")
                    st.rerun()
            except Exception as e: st.error(f"Error CSV: {e}")

    st.markdown("---")
    trades = db.get_user_trades(user.id)
    if trades:
        df_trades = pd.DataFrame(trades)
        df_trades["trade_time"] = pd.to_datetime(df_trades["trade_time"]).dt.date
        st.dataframe(df_trades[["trade_time", "symbol", "side", "amount", "price_usd"]], use_container_width=True, hide_index=True)
        if st.button("🗑️ Hapus Semua", type="secondary"):
            db.delete_all_user_trades(user.id)
            st.rerun()

# ===========================================================================
# MENU 3: ALERTS
# ===========================================================================
elif menu == "🔔 Alerts":
    st.subheader("🔔 Price Alerts")
    with st.expander("⚙️ Hubungkan ke Telegram"):
        tg_chat = st.text_input("Chat ID Telegram Kamu:", value=user_profile.get("telegram_chat_id", ""))
        if st.button("💾 Simpan Chat ID"):
            db.update_telegram_chat_id(user.id, tg_chat)
            st.success("Chat ID tersimpan!")
            st.rerun()
        if st.button("📨 Test Kirim Pesan"):
            global_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
            if telegram.send_message(global_token, tg_chat, "✅ ChainScope ID Berhasil Terhubung!"):
                st.success("Terkirim!")
            else: st.error("Gagal kirim.")
    
    with st.form("alert_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        a_coin = c1.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
        a_cond = c2.selectbox("Kondisi", ["above", "below"])
        a_price = c3.number_input("Target", min_value=0.01)
        if st.form_submit_button("Tambah Alert"):
            sym = market_df[market_df["id"]==a_coin]["symbol_upper"].values[0]
            db.add_alert(user.id, a_coin, sym, a_cond, a_price, currency)
            st.rerun()
            
    alerts = db.get_user_alerts(user.id)
    if alerts:
        for a in alerts:
            st.markdown(f"**{a['symbol']}** {a['condition']} {a['target_price']} {a['currency']} — {'Triggered' if not a['is_active'] else 'Waiting'}")

# ===========================================================================
# MENU 4: TEKNIKAL
# ===========================================================================
elif menu == "📉 Teknikal":
    st.subheader("📉 Analisis Teknikal")
    c1, c2, c3 = st.columns([2, 1, 1])
    tech_label = c1.selectbox("Koin:", market_df["label"].tolist())
    chart_mode = c2.radio("Mode:", ["Line", "Candlestick"], horizontal=True)
    tf = c3.selectbox("Timeframe", ["1D", "7D", "1M", "1Y"], index=1)
    
    days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
    tech_id = dict(zip(market_df["label"], market_df["id"]))[tech_label]
    
    try:
        hist = demo.get_demo_price_history(market_df[market_df["id"]==tech_id].iloc[0]["current_price"]) if demo_mode else cached_price_history(tech_id, currency, days_map[tf])
        ohlc = None
        if chart_mode == "Candlestick" and not demo_mode:
            ohlc = cached_ohlc(tech_id, currency, days_map[tf])
            
        hist["ma20"] = indicators.sma(hist["price"], 20)
        hist["rsi"] = indicators.rsi(hist["price"], 14)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        if ohlc is not None and not ohlc.empty:
            fig.add_trace(go.Candlestick(x=ohlc["waktu"], open=ohlc["open"], high=ohlc["high"], low=ohlc["low"], close=ohlc["close"], name="OHLC"), row=1, col=1)
        else:
            fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["price"], name="Price", line=dict(color="#2962FF")), row=1, col=1)
            
        fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma20"], name="MA20", line=dict(color="#FFB300")), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["rsi"], name="RSI", line=dict(color="#00E676")), row=2, col=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig, use_container_width=True)
    except Exception: st.warning("Gagal memuat data teknikal (API Limit).")

# ===========================================================================
# MENU 5: PERBANDINGAN
# ===========================================================================
elif menu == "📈 Perbandingan":
    st.subheader("📈 Perbandingan Multi-Koin")
    selected_labels = st.multiselect("Pilih 2–5 koin:", options=market_df["label"].tolist(), default=market_df["label"].head(3).tolist(), max_selections=5)
    normalize = st.toggle("Normalisasi ke 100", value=True)
    
    if len(selected_labels) >= 2:
        try:
            history_by_coin = {}
            for lbl in selected_labels:
                cid = dict(zip(market_df["label"], market_df["id"]))[lbl]
                history_by_coin[cid] = demo.get_demo_price_history(market_df[market_df["id"]==cid].iloc[0]["current_price"]) if demo_mode else cached_price_history(cid, currency, 7)
                
            comp_df = compare.build_comparison_df(history_by_coin)
            if normalize: comp_df = compare.normalize_to_100(comp_df)
            fig = px.line(comp_df, x="waktu", y=[c for c in comp_df.columns if c != "waktu"])
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        except Exception: st.warning("Gagal memuat perbandingan (API Limit).")

# ===========================================================================
# MENU 6: PORTOFOLIO
# ===========================================================================
elif menu == "💼 Portofolio":
    st.subheader("💼 Portofolio Otomatis")
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
            c3.metric("P&L", formatting.format_money(pf_df["pnl"].sum(), currency), delta=f"{pf_df['pnl_pct'].mean():.2f}%")
            
            display_df = pd.DataFrame({
                "Koin": pf_df["symbol"],
                "Jumlah": pf_df["amount"].map(lambda x: f"{x:.4f}"),
                "Harga Rata2": pf_df["avg_buy_price"].map(lambda v: formatting.format_money(v, currency)),
                "Nilai Kini": pf_df["current_value"].map(lambda v: formatting.format_money(v, currency)),
                "P&L": pf_df["pnl"].map(lambda v: formatting.format_money(v, currency)),
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)

# ===========================================================================
# MENU 7: KONVERTER
# ===========================================================================
elif menu == "💱 Konverter":
    st.subheader("💱 Konverter Koin")
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
    st.subheader("⭐ Watchlist Saya")
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
# MENU 9: GAINERS & LOSERS
# ===========================================================================
elif menu == "🚀 Gainers & Losers":
    st.subheader("Pergerakan 24 Jam")
    movers_df = market_df.dropna(subset=["price_change_percentage_24h"]).sort_values("price_change_percentage_24h", ascending=False)
    cg, cl = st.columns(2)
    cg.markdown("#### 🟢 Top Gainers")
    cg.dataframe(movers_df.head(5)[["symbol_upper", "price_change_percentage_24h"]], use_container_width=True, hide_index=True)
    cl.markdown("#### 🔴 Top Losers")
    cl.dataframe(movers_df.tail(5)[["symbol_upper", "price_change_percentage_24h"]], use_container_width=True, hide_index=True)

# ===========================================================================
# MENU 10: LAPORAN PDF
# ===========================================================================
elif menu == "📄 Laporan PDF":
    st.subheader("📄 Laporan PDF")
    if st.button("Buat Laporan"):
        try:
            pdf_bytes = report.build_weekly_report(market_df, currency, data_source)
            st.download_button("⬇️ Unduh PDF", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")
        except Exception as e: st.error(f"Gagal membuat PDF: {e}")

# ===========================================================================
# MENU 11: ADMIN PANEL
# ===========================================================================
elif menu == "👑 Admin Panel" and is_dev:
    st.subheader("👑 Admin Panel")
    all_users = admin.get_all_users()
    df_users = pd.DataFrame(all_users)
    st.dataframe(df_users[["email", "role", "subscription_tier", "subscription_end"]], use_container_width=True, hide_index=True)