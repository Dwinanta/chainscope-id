"""
ChainScope ID - Premium Trading Terminal v2.0
"""
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from chainscope import ui, api, auth, compare, config, converter, db, demo, formatting, indicators, portfolio, report, search, telegram, admin, journal_calc

# 1. KONFIGURASI HALAMAN & TEMA
st.set_page_config(page_title="ChainScope ID", page_icon="📈", layout="wide")
ui.apply_premium_theme()

# 2. CEK AUTENTIKASI
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
    # LOGO HEADER
    st.markdown("""
        <div class="sidebar-logo">
            <h2>⚡ ChainScope <span>ID</span></h2>
        </div>
    """, unsafe_allow_html=True)
    
    # User Profile & Plan
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
    
    # Navigasi
    menu_options = [
        "🏠 Ringkasan", "📒 Trading Journal", "🔔 Alerts", 
        "📉 Teknikal", "📈 Perbandingan", "💼 Portofolio", 
        "💱 Konverter", "⭐ Watchlist", "🚀 Gainers & Losers", 
        "📄 Laporan PDF"
    ]
    if is_dev: menu_options.append("👑 Admin Panel")
    menu = st.radio("Navigasi", menu_options, label_visibility="collapsed")

    st.markdown("---")
    
    # Settings Global
    currency = st.radio("Mata uang:", options=["IDR", "USD"], horizontal=True)
    coin_count = st.selectbox("Tampilkan Koin:", options=config.COIN_COUNT_OPTIONS, index=0, help="Menampilkan Top-N koin dari CoinGecko")
    demo_mode = st.checkbox("Mode Demo", value=False)

# 5. AMBIL DATA PASAR
market_df = None
data_source = "LIVE"
error_message = None

if demo_mode:
    market_df = demo.get_demo_market_data(limit=min(coin_count, 50), currency=currency) # Demo dibatasi 50
    data_source = "DEMO"
else:
    try:
        market_df = cached_market_data(currency, coin_count)
    except Exception as exc:
        error_message = str(exc)

if error_message:
    st.error(error_message)
    st.stop()

market_df = market_df.copy()
market_df["symbol_upper"] = market_df["symbol"].astype(str).str.upper()
market_df["label"] = market_df["name"] + " (" + market_df["symbol_upper"] + ")"
unit_label = f"Harga ({currency})"

# ===========================================================================
# MENU 1: RINGKASAN (PADAT & LENGKAP)
# ===========================================================================
if menu == "🏠 Ringkasan":
    # Header
    col_title, col_search = st.columns([2, 1])
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>Market Overview</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='text-muted'>Data {data_source} • Top {len(market_df)} koin</p>", unsafe_allow_html=True)
    with col_search:
        st.write("") # spacing
        search_query = st.text_input("🔍 Cari koin...", placeholder="Bitcoin, ETH, dll", label_visibility="collapsed")

    # --- ROW 1: KARTU TOP 4 ---
    top4_df = market_df.head(4)
    cols = st.columns(4)
    for col, (_, row) in zip(cols, top4_df.iterrows()):
        with col:
            with st.container(border=True):
                color = "#00E676" if row['price_change_percentage_24h'] >= 0 else "#FF5252"
                icon = "▲" if row['price_change_percentage_24h'] >= 0 else "▼"
                
                # Header Card (Logo + Nama)
                st.markdown(f"""
                <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
                    <img src="{row['image']}" width="24" height="24" style="border-radius:50%;">
                    <b>{row['name']}</b>
                </div>
                <h2 style='margin:0;'>{formatting.format_money(row['current_price'], currency)}</h2>
                <span style='color:{color}; font-size:0.9rem;'>{icon} {row['price_change_percentage_24h']:.2f}% (24h)</span>
                """, unsafe_allow_html=True)
                
                                # Sparkline (Langsung ambil dari data market_df, tidak perlu request API baru)
                sparkline_prices = row.get("sparkline_in_7d", {}).get("price", [])
                if sparkline_prices:
                    fig = go.Figure(go.Scatter(y=sparkline_prices, mode='lines', line=dict(color=color, width=1.5)))
                    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=50, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ROW 2: GRAFIK BESAR & GAINERS/LOSERS ---
    col_chart, col_movers = st.columns([2.5, 1])
    
    with col_chart:
        with st.container(border=True):
            # Header Chart & Timeframe Selector
            c_t1, c_t2, c_t3 = st.columns([2, 2, 2])
            c_t1.markdown("#### Pergerakan Harga")
            chart_coin = c_t2.selectbox("Pilih Koin", market_df["label"].tolist(), label_visibility="collapsed")
            timeframe = c_t3.selectbox("Timeframe", ["1D", "7D", "1M", "1Y"], index=1, label_visibility="collapsed")
            
            days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
            days = days_map[timeframe]
            
            cid = dict(zip(market_df["label"], market_df["id"]))[chart_coin]
            
            try:
                hist_df = demo.get_demo_price_history(market_df[market_df["id"]==cid].iloc[0]["current_price"]) if demo_mode else cached_price_history(cid, currency, days)
                
                fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#2962FF'])
                fig_main.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0), height=350,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, color='#868B96'), yaxis=dict(showgrid=True, gridcolor='#1E222D', color='#868B96')
                )
                st.plotly_chart(fig_main, use_container_width=True)
            except Exception as e:
                st.warning("⚠️ Grafik sedang tidak dapat dimuat karena batas API CoinGecko. Silakan coba beberapa saat lagi atau gunakan Mode Demo.")

    with col_movers:
        with st.container(border=True):
            st.markdown("#### 🚀 Top Gainers")
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(5)
            for _, row in gainers.iterrows():
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <div style='display:flex; gap:8px; align-items:center;'>
                        <img src="{row['image']}" width="20" height="20">
                        <b>{row['symbol_upper']}</b>
                    </div>
                    <span class='text-green'>+{row['price_change_percentage_24h']:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
            st.markdown("#### 🔻 Top Losers")
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(5)
            for _, row in losers.iterrows():
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <div style='display:flex; gap:8px; align-items:center;'>
                        <img src="{row['image']}" width="20" height="20">
                        <b>{row['symbol_upper']}</b>
                    </div>
                    <span class='text-red'>{row['price_change_percentage_24h']:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

    # --- ROW 3: TABEL DATA LENGKAP (DENGAN LOGO) ---
    st.markdown("### Tabel Data Pasar")
    filtered_df = search.filter_coins(market_df, search_query)
    table_source = filtered_df if not filtered_df.empty else market_df
    
    # Buat DataFrame untuk tabel
    display_df = pd.DataFrame({
        "#": range(1, len(table_source) + 1),
        "Logo": table_source["image"], # URL gambar
        "Nama": table_source["name"],
        "Simbol": table_source["symbol_upper"],
        "Harga": table_source["current_price"],
        "24h (%)": table_source["price_change_percentage_24h"],
        "Volume 24h": table_source["total_volume"],
        "Kap. Pasar": table_source["market_cap"]
    })

    # Tampilkan Tabel dengan Config
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"),
            "Harga": st.column_config.NumberColumn(format=f"{currency} %,.2f"),
            "24h (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Volume 24h": st.column_config.NumberColumn(format="%,.0f"),
            "Kap. Pasar": st.column_config.NumberColumn(format="%,.0f")
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
                col_options = df_csv.columns.tolist()
                map_coin = st.selectbox("Kolom Koin", col_options)
                map_side = st.selectbox("Kolom Aksi", col_options)
                map_amount = st.selectbox("Kolom Jumlah", col_options)
                map_price = st.selectbox("Kolom Harga", col_options)
                map_date = st.selectbox("Kolom Tanggal", col_options)
                
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
            except Exception as e:
                st.error(f"Error CSV: {e}")

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
# MENU 3: ALERTS (Singkat)
# ===========================================================================
elif menu == "🔔 Alerts":
    st.subheader("🔔 Price Alerts")
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
# MENU 4: TEKNIKAL (Singkat)
# ===========================================================================
elif menu == "📉 Teknikal":
    st.subheader("📉 Analisis Teknikal")
    c1, c2 = st.columns(2)
    tech_label = c1.selectbox("Koin:", market_df["label"].tolist())
    tech_id = dict(zip(market_df["label"], market_df["id"]))[tech_label]
    
    hist = cached_price_history(tech_id, currency, 7)
    hist["ma20"] = indicators.sma(hist["price"], 20)
    hist["rsi"] = indicators.rsi(hist["price"], 14)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
    fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["price"], name="Price", line=dict(color="#2962FF")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["ma20"], name="MA20", line=dict(color="#FFB300")), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist["waktu"], y=hist["rsi"], name="RSI", line=dict(color="#00E676")), row=2, col=1)
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600)
    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# MENU 5-11 (Placeholder Rapi)
# ===========================================================================
elif menu == "📈 Perbandingan":
    st.info("Fitur Perbandingan siap.")
elif menu == "💼 Portofolio":
    st.info("Fitur Portofolio siap.")
elif menu == "💱 Konverter":
    st.info("Fitur Konverter siap.")
elif menu == "⭐ Watchlist":
    st.info("Fitur Watchlist siap.")
elif menu == "🚀 Gainers & Losers":
    st.info("Fitur Movers siap.")
elif menu == "📄 Laporan PDF":
    st.info("Fitur PDF siap.")
elif menu == "👑 Admin Panel" and is_dev:
    st.info("Admin Panel siap.")