"""
ChainScope ID - Premium Trading Terminal
"""
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

@st.cache_data(ttl=300, show_spinner=False)
def cached_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_price_history(coin_id, vs_currency, days)

@st.cache_data(ttl=300, show_spinner=False)
def cached_ohlc(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_ohlc(coin_id, vs_currency, days)

# 4. SIDEBAR (NAVIGASI & PENGATURAN)
with st.sidebar:
    st.markdown(f"### 👤 {user.email}")
    
    # Info Langganan
    end_date = user_profile.get("subscription_end")
    if end_date:
        st.info(f"🌟 **{sub_tier}**\n\nAktif s/d: {end_date[:10]}")
    else:
        st.info(f"🌟 **{sub_tier}**")
        
    if is_dev:
        st.success("👑 Dev Mode Aktif")
    
    if st.button("🚪 Logout", use_container_width=True):
        auth.logout_user()

    st.markdown("---")
    
    # Menu Navigasi
    menu_options = [
        "🏠 Ringkasan", "📒 Trading Journal", "🔔 Alerts", 
        "📉 Teknikal", "📈 Perbandingan", "💼 Portofolio", 
        "💱 Konverter", "⭐ Watchlist", "🚀 Gainers & Losers", 
        "📄 Laporan PDF"
    ]
    if is_dev:
        menu_options.append("👑 Admin Panel")
        
    menu = st.radio("Navigasi", menu_options, label_visibility="collapsed")

    st.markdown("---")
    
    # Pengaturan Global
    currency = st.radio("Mata uang:", options=["IDR", "USD"], horizontal=True)
    coin_count = st.selectbox("Jumlah koin:", options=[10, 20, 50], index=0)
    demo_mode = st.checkbox("Gunakan Mode Demo", value=False)
    
    st.markdown("---")
    st.caption("Sumber data: CoinGecko API")

# 5. AMBIL DATA PASAR
market_df = None
data_source = "LIVE"
error_message = None

if demo_mode:
    market_df = demo.get_demo_market_data(limit=coin_count, currency=currency)
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
# MENU 1: RINGKASAN (PREMIUM DASHBOARD)
# ===========================================================================
if menu == "🏠 Ringkasan":
    col_title, col_date = st.columns([3, 1])
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>Market Overview</h1>", unsafe_allow_html=True)
        st.markdown("<p class='text-muted'>Ringkasan pasar kripto global dan pergerakan harga terbaru.</p>", unsafe_allow_html=True)
    with col_date:
        st.markdown(f"<p class='text-muted' style='text-align:right; margin-top:15px;'>Mode: {data_source}</p>", unsafe_allow_html=True)

    # --- BARIS 1: KARTU TOP 3 + GLOBAL ---
    top3_df = market_df.head(3)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    def create_sparkline(coin_id, current_price, color):
        hist = demo.get_demo_price_history(current_price) if demo_mode else cached_price_history(coin_id, currency, 1)
        fig = go.Figure(go.Scatter(x=hist['waktu'], y=hist['price'], mode='lines', line=dict(color=color, width=2)))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=40, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    for i, (col, (_, row)) in enumerate(zip([col_m1, col_m2, col_m3], top3_df.iterrows())):
        with col:
            with st.container(border=True):
                st.markdown(f"**{row['name']} ({row['symbol_upper']})**")
                st.markdown(f"<h2 style='margin:0;'>{formatting.format_money(row['current_price'], currency)}</h2>", unsafe_allow_html=True)
                color = "#00E676" if row['price_change_percentage_24h'] >= 0 else "#FF5252"
                icon = "▲" if row['price_change_percentage_24h'] >= 0 else "▼"
                st.markdown(f"<span style='color:{color}; font-size:0.9rem;'>{icon} {row['price_change_percentage_24h']:.2f}% (24h)</span>", unsafe_allow_html=True)
                st.plotly_chart(create_sparkline(row['id'], row['current_price'], color), use_container_width=True, config={'displayModeBar': False})

    with col_m4:
        with st.container(border=True):
            st.markdown("**🌐 Pasar Global**")
            st.markdown("<p class='text-muted' style='margin-bottom:0;'>Kapitalisasi Pasar</p><h4>Rp 43,2 T</h4>", unsafe_allow_html=True)
            st.markdown("<p class='text-muted' style='margin-bottom:0;'>Volume 24h</p><h4>Rp 2,1 T</h4>", unsafe_allow_html=True)
            st.markdown("<p class='text-muted' style='margin-bottom:0;'>Dominasi BTC</p><h4>52.3%</h4>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- BARIS 2: GRAFIK & GAINERS/LOSERS ---
    col_chart, col_movers = st.columns([2.5, 1])
    
    with col_chart:
        st.markdown("#### Pergerakan Harga (7 Hari)")
        # Ambil BTC secara default
        btc_row = market_df[market_df["id"] == "bitcoin"].iloc[0]
        hist_df = demo.get_demo_price_history(btc_row["current_price"]) if demo_mode else cached_price_history("bitcoin", currency, 7)
        
        fig_main = px.area(hist_df, x="waktu", y="price", color_discrete_sequence=['#2962FF'])
        fig_main.update_layout(
            margin=dict(l=0, r=0, t=10, b=0), height=300,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, color='#868B96'), yaxis=dict(showgrid=True, gridcolor='#1E222D', color='#868B96')
        )
        st.plotly_chart(fig_main, use_container_width=True)

    with col_movers:
        with st.container(border=True):
            st.markdown("**🚀 Top Gainers**")
            gainers = market_df.sort_values("price_change_percentage_24h", ascending=False).head(4)
            for _, row in gainers.iterrows():
                st.markdown(f"<div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span>{row['symbol_upper']}</span><span class='text-green'>+{row['price_change_percentage_24h']:.2f}%</span></div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("**🔻 Top Losers**")
            losers = market_df.sort_values("price_change_percentage_24h", ascending=True).head(4)
            for _, row in losers.iterrows():
                st.markdown(f"<div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span>{row['symbol_upper']}</span><span class='text-red'>{row['price_change_percentage_24h']:.2f}%</span></div>", unsafe_allow_html=True)

    # --- BARIS 3: TABEL & SENTIMEN ---
    col_table, col_side = st.columns([2.5, 1])
    with col_table:
        st.markdown("#### Tabel Data Pasar")
        search_query = st.text_input("🔍 Cari koin...", label_visibility="collapsed")
        filtered_df = search.filter_coins(market_df, search_query)
        table_source = filtered_df if not filtered_df.empty else market_df
        
        table_view = pd.DataFrame({
            "Nama": table_source["name"],
            "Simbol": table_source["symbol_upper"],
            f"Harga": table_source["current_price"].map(lambda v: formatting.format_money(v, currency)),
            f"Kap. Pasar": table_source["market_cap"].map(lambda v: formatting.format_money(v, currency)),
            "% 24h": table_source["price_change_percentage_24h"].map(formatting.format_percent),
        })
        st.dataframe(table_view, use_container_width=True, hide_index=True)

    with col_side:
        with st.container(border=True):
            st.markdown("**Market Sentiment**")
            st.markdown("""
            <div style='text-align:center; padding:20px;'>
                <div style='width:100px; height:100px; border-radius:50%; border: 6px solid #00E676; display:flex; align-items:center; justify-content:center; margin:auto;'>
                    <h2 style='color:#00E676; margin:0;'>72</h2>
                </div>
                <h4 style='color:#00E676; margin-top:10px;'>Greed</h4>
            </div>
            """, unsafe_allow_html=True)

# ===========================================================================
# MENU 2: TRADING JOURNAL
# ===========================================================================
elif menu == "📒 Trading Journal":
    st.subheader("📒 Trading Journal")
    st.caption("Catat transaksi manual atau import dari CSV exchange.")
    
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
        uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"], label_visibility="collapsed")
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
                    st.success(f"Berhasil import {success_count} transaksi!")
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal membaca CSV: {e}")

    st.markdown("---")
    st.markdown("### Riwayat Transaksi")
    trades = db.get_user_trades(user.id)
    if not trades:
        st.info("Belum ada transaksi.")
    else:
        df_trades = pd.DataFrame(trades)
        df_trades["trade_time"] = pd.to_datetime(df_trades["trade_time"]).dt.date
        st.dataframe(df_trades[["trade_time", "symbol", "side", "amount", "price_usd"]].rename(columns={"trade_time": "Tanggal", "symbol": "Koin", "side": "Aksi", "amount": "Jumlah", "price_usd": "Harga (USD)"}), use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Hapus Semua Transaksi", type="secondary", key="btn_hapus_journal"):
            db.delete_all_user_trades(user.id)
            st.success("Dihapus.")
            st.rerun()

# ===========================================================================
# MENU 3: ALERTS
# ===========================================================================
elif menu == "🔔 Alerts":
    st.subheader("🔔 Price Alerts")
    
    with st.expander("⚙️ Hubungkan ke Telegram"):
        current_chat_id = user_profile.get("telegram_chat_id", "")
        tg_chat = st.text_input("Chat ID Telegram Kamu:", value=current_chat_id)
        if st.button("💾 Simpan Chat ID"):
            db.update_telegram_chat_id(user.id, tg_chat)
            st.success("Chat ID tersimpan!")
            st.rerun()
            
        if st.button("📨 Test Kirim Pesan"):
            global_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
            if telegram.send_message(global_token, tg_chat, "✅ ChainScope ID Berhasil Terhubung!"):
                st.success("Terkirim!")
            else:
                st.error("Gagal kirim. Pastikan bot sudah di-start.")
    
    with st.form("new_alert_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
        alert_coin = c1.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
        alert_cond = c2.selectbox("Kondisi", ["above", "below"])
        alert_price = c3.number_input("Target Harga", min_value=0.01, value=1000.0)
        alert_cur = c4.selectbox("Mata Uang", ["USD", "IDR"])
        
        if st.form_submit_button("➕ Tambah Alert"):
            sym = market_df[market_df["id"]==alert_coin]["symbol_upper"].values[0]
            db.add_alert(user.id, alert_coin, sym, alert_cond, alert_price, alert_cur)
            st.success("Alert dibuat!")
            st.rerun()

    st.markdown("### Daftar Alert")
    user_alerts = db.get_user_alerts(user.id)
    if not user_alerts:
        st.info("Belum ada alert.")
    else:
        for a in user_alerts:
            status = "✅ TRIGGERED" if not a["is_active"] else "⏳ MENUNGGU"
            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(f"**{a['symbol']}** {a['condition']} **{a['target_price']:,.2f} {a['currency']}** — *{status}*")
            with col_del:
                if st.button("🗑️", key=f"del_{a['id']}"):
                    db.delete_alert(a['id'])
                    st.rerun()

# ===========================================================================
# MENU 4: TEKNIKAL
# ===========================================================================
elif menu == "📉 Teknikal":
    st.subheader("📉 Analisis Teknikal")
    
    col_coin, col_tf, col_mode = st.columns([3, 2, 2])
    tech_label = col_coin.selectbox("Koin:", market_df["label"].tolist(), key="tech_coin")
    tech_tf_label = col_tf.selectbox("Timeframe:", ["1 jam", "24 jam", "7 hari", "30 hari", "90 hari", "1 tahun"], index=2)
    chart_mode = col_mode.radio("Mode grafik:", ["Line", "Candlestick"], horizontal=True)
    
    with st.expander("Indikator", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        show_ma20 = c1.checkbox("MA20", value=True)
        show_ma50 = c2.checkbox("MA50", value=False)
        show_bb = c3.checkbox("Bollinger Bands", value=False)
        sub_chart = c4.selectbox("Sub-chart:", ["RSI", "Volume", "Tidak ada"])
        log_scale = c5.checkbox("Skala log", value=False)

    tech_id = dict(zip(market_df["label"], market_df["id"]))[tech_label]
    tech_tf_days = {"1 jam": 1, "24 jam": 1, "7 hari": 7, "30 hari": 30, "90 hari": 90, "1 tahun": 365}[tech_tf_label]

    if demo_mode:
        row = market_df[market_df["id"] == tech_id].iloc[0]
        tech_history = demo.get_demo_price_history(row["current_price"])
        tech_history["volume"] = None
        tech_ohlc = None
    else:
        tech_history = cached_price_history(tech_id, currency, tech_tf_days)
        tech_ohlc = cached_ohlc(tech_id, currency, tech_tf_days) if chart_mode == "Candlestick" else None

    if tech_history is not None and not tech_history.empty:
        history = tech_history.copy()
        history["ma20"] = indicators.sma(history["price"], 20)
        history["ma50"] = indicators.sma(history["price"], 50)
        bb_mid, bb_upper, bb_lower = indicators.bollinger_bands(history["price"], 20, 2)
        history["bb_upper"] = bb_upper
        history["bb_lower"] = bb_lower
        history["rsi"] = indicators.rsi(history["price"], 14)

        if sub_chart == "Tidak ada":
            fig_t = go.Figure()
        else:
            from plotly.subplots import make_subplots
            fig_t = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

        if tech_ohlc is not None and not tech_ohlc.empty:
            fig_t.add_trace(go.Candlestick(x=tech_ohlc["waktu"], open=tech_ohlc["open"], high=tech_ohlc["high"], low=tech_ohlc["low"], close=tech_ohlc["close"], name="OHLC", increasing_line_color="#00E676", decreasing_line_color="#FF5252"), row=1, col=1)
        else:
            fig_t.add_trace(go.Scatter(x=history["waktu"], y=history["price"], mode="lines", name="Harga", line=dict(color="#2962FF", width=2)), row=1, col=1)

        if show_ma20: fig_t.add_trace(go.Scatter(x=history["waktu"], y=history["ma20"], name="MA20", line=dict(color="#FFB300")), row=1, col=1)
        if show_ma50: fig_t.add_trace(go.Scatter(x=history["waktu"], y=history["ma50"], name="MA50", line=dict(color="#9C27B0")), row=1, col=1)
        if show_bb: 
            fig_t.add_trace(go.Scatter(x=history["waktu"], y=history["bb_upper"], name="BB Upper", line=dict(color="#555")), row=1, col=1)
            fig_t.add_trace(go.Scatter(x=history["waktu"], y=history["bb_lower"], name="BB Lower", line=dict(color="#555"), fill="tonexty"), row=1, col=1)

        if sub_chart == "RSI":
            fig_t.add_trace(go.Scatter(x=history["waktu"], y=history["rsi"], name="RSI", line=dict(color="#00E676")), row=2, col=1)
            fig_t.update_yaxes(range=[0, 100], row=2, col=1)
        elif sub_chart == "Volume" and "volume" in history.columns:
            fig_t.add_trace(go.Bar(x=history["waktu"], y=history["volume"], name="Vol", marker_color="#555"), row=2, col=1)

        if log_scale: fig_t.update_yaxes(type="log", row=1, col=1)
        
        fig_t.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600, margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig_t, use_container_width=True)

# ===========================================================================
# MENU 5: PERBANDINGAN
# ===========================================================================
elif menu == "📈 Perbandingan":
    st.subheader("📈 Perbandingan Multi-Koin")
    selected_labels = st.multiselect("Pilih 2–5 koin:", options=market_df["label"].tolist(), default=market_df["label"].head(3).tolist(), max_selections=5)
    normalize = st.toggle("Normalisasi ke 100", value=True)
    
    if len(selected_labels) >= 2:
        history_by_coin = {}
        for lbl in selected_labels:
            cid = dict(zip(market_df["label"], market_df["id"]))[lbl]
            history_by_coin[cid] = demo.get_demo_price_history(market_df[market_df["id"]==cid].iloc[0]["current_price"]) if demo_mode else cached_price_history(cid, currency, 7)
            
        comp_df = compare.build_comparison_df(history_by_coin)
        if normalize: comp_df = compare.normalize_to_100(comp_df)
        fig = px.line(comp_df, x="waktu", y=[c for c in comp_df.columns if c != "waktu"])
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# MENU 6: PORTOFOLIO (OTOMATIS DARI JOURNAL)
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
            
            st.dataframe(pd.DataFrame({
                "Koin": pf_df["symbol"],
                "Jumlah": pf_df["amount"].map(lambda x: f"{x:.4f}"),
                "Harga Rata2": pf_df["avg_buy_price"].map(lambda v: formatting.format_money(v, currency)),
                "Nilai Kini": pf_df["current_value"].map(lambda v: formatting.format_money(v, currency)),
                "P&L": pf_df["pnl"].map(lambda v: formatting.format_money(v, currency)),
            }), use_container_width=True, hide_index=True)

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
# MENU 8: WATCHLIST (SUPABASE)
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
        pdf_bytes = report.build_weekly_report(market_df, currency, data_source)
        st.download_button("⬇️ Unduh PDF", data=pdf_bytes, file_name="report.pdf", mime="application/pdf")

# ===========================================================================
# MENU 11: ADMIN PANEL
# ===========================================================================
elif menu == "👑 Admin Panel" and is_dev:
    st.subheader("👑 Admin Panel")
    all_users = admin.get_all_users()
    df_users = pd.DataFrame(all_users)
    st.dataframe(df_users[["email", "role", "subscription_tier", "subscription_end"]], use_container_width=True, hide_index=True)