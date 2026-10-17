"""
ChainScope ID - Dashboard pasar kripto sederhana (UI Streamlit).

Logika non-UI ada di package `chainscope/`.
Data live: CoinGecko API publik (tanpa API key).

Disclaimer: aplikasi ini hanya menampilkan data pasar publik.
Bukan saran investasi.
"""

from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from chainscope import ui

from chainscope import (
    api, auth, compare, config, converter, db, demo, formatting, 
    indicators, portfolio, report, search, watchlist,
)

# ---------------------------------------------------------------------------
# Konfigurasi halaman
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ChainScope ID",
    page_icon="📈",
    layout="wide",
)
st.set_page_config(page_title="ChainScope ID", page_icon="📈", layout="wide")

# Terapkan Tema Premium
ui.apply_premium_theme()

# ... sisa kode di bawahnya ...


# ---------------------------------------------------------------------------
# Wrapper cache Streamlit di atas fungsi API
# ---------------------------------------------------------------------------

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_market_data(vs_currency: str, limit: int) -> pd.DataFrame:
    return api.fetch_market_data(vs_currency, limit)

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_usd_idr_rate() -> float:
    """Hitung kurs USD -> IDR dari harga BTC di CoinGecko.

    Jika gagal (offline / API error), kembalikan kurs tetap dari config.
    """
    try:
        df_usd = api.fetch_market_data("usd", 1)
        df_idr = api.fetch_market_data("idr", 1)
        if not df_usd.empty and not df_idr.empty:
            usd_price = float(df_usd.iloc[0]["current_price"])
            idr_price = float(df_idr.iloc[0]["current_price"])
            if usd_price > 0:
                return idr_price / usd_price
    except Exception:  # noqa: BLE001
        pass
    return float(config.DEMO_USD_TO_IDR)

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_price_history(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_price_history(coin_id, vs_currency, days)

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def cached_ohlc(coin_id: str, vs_currency: str, days: int = 7) -> pd.DataFrame:
    return api.fetch_ohlc(coin_id, vs_currency, days)

# ---------------------------------------------------------------------------
# CEK AUTENTIKASI (Hentikan aplikasi jika belum login)
# ---------------------------------------------------------------------------
if "user" not in st.session_state or st.session_state.user is None:
    auth.show_auth_page()
    st.stop()  # Aplikasi berhenti di sini jika belum login

user = st.session_state.user
user_profile = db.get_user_profile(user.id)
is_dev = user_profile.get("role") == "dev"
sub_tier = user_profile.get("subscription_tier", "free").title()

# ---------------------------------------------------------------------------
# UI - Header & Sidebar
# ---------------------------------------------------------------------------

st.title("📈 ChainScope ID")
st.caption(
    "Dashboard pasar kripto sederhana. Data publik dari CoinGecko. "
    "Bukan saran investasi."
)

with st.sidebar:
    st.header("Pengaturan")
    st.caption(f"Login sebagai: **{user.email}**")
    
    # --- Info Langganan ---
    end_date = user_profile.get("subscription_end")
    if end_date:
        end_date = end_date[:10] # Ambil tanggalnya saja (YYYY-MM-DD)
        st.info(f"🌟 Plan: **{sub_tier}**\n\nAktif s/d: **{end_date}**")
    else:
        st.info(f"🌟 Plan: **{sub_tier}**")
        
    if is_dev:
        st.success("👑 Dev Mode")
    
    if st.button("🚪 Logout"):
        auth.logout_user()
        
    st.markdown("---")

    # (Di bawah ini adalah kode sidebar lamamu: currency = st.radio(... dst)
    currency = st.radio(
        "Mata uang:",
        options=list(config.CURRENCY_OPTIONS.keys()),
        index=list(config.CURRENCY_OPTIONS.keys()).index(config.DEFAULT_CURRENCY),
        format_func=lambda c: config.CURRENCY_OPTIONS[c]["label"],
        horizontal=True,
    )

    coin_count = st.selectbox(
        "Jumlah koin ditampilkan:",
        options=config.COIN_COUNT_OPTIONS,
        index=config.COIN_COUNT_OPTIONS.index(config.DEFAULT_COIN_COUNT),
        help="Koin teratas berdasarkan kapitalisasi pasar.",
    )

    demo_mode = st.checkbox(
        "Gunakan Mode Demo (data contoh)",
        value=False,
        help="Aktifkan jika tidak ada internet atau API sedang bermasalah.",
    )

    st.markdown("---")
    st.markdown(
        "**Sumber data:** CoinGecko API publik\n\n"
        f"**Cache:** {config.CACHE_TTL_SECONDS} detik\n\n"
        f"**Mata uang:** {config.CURRENCY_OPTIONS[currency]['label']}"
    )
    if demo_mode and currency.upper() == "IDR":
        st.caption(f"(Mode demo pakai kurs tetap 1 USD ≈ Rp{config.DEMO_USD_TO_IDR:,.0f})")

    wl_count = len(watchlist.load_watchlist())
    st.markdown("---")
    st.markdown(f"⭐ **Watchlist:** {wl_count} koin")


# ---------------------------------------------------------------------------
# Ambil data pasar
# ---------------------------------------------------------------------------

market_df = None
data_source = "LIVE"
error_message = None

if demo_mode:
    market_df = demo.get_demo_market_data(limit=coin_count, currency=currency)
    data_source = "DEMO"
else:
    try:
        market_df = cached_market_data(currency, coin_count)
    except api.ChainScopeAPIError as exc:
        error_message = str(exc) + " Coba lagi nanti atau aktifkan Mode Demo."
    except Exception as exc:  # noqa: BLE001
        error_message = f"Terjadi kesalahan tak terduga: {exc}"

if error_message:
    st.error(error_message)
    st.stop()

if data_source == "DEMO":
    st.warning(
        "⚠️ Mode Demo aktif — angka di bawah adalah data contoh, bukan harga nyata."
    )
else:
    st.success(f"✅ Data live dari CoinGecko (Top {len(market_df)} koin, {currency}).")
    if data_source == "LIVE":
        with st.expander("ℹ️ Info penyimpanan (klik untuk detail)"):
            st.caption(
            "Watchlist dan portofolio disimpan di file lokal. Jika aplikasi "
            "ini di-deploy di Streamlit Community Cloud (versi gratis), "
            "kedua data tersebut akan **reset** setiap kali aplikasi di-restart "
            "atau di-redeploy. Untuk penyimpanan permanen, versi berikutnya "
            "akan memakai database cloud."
        )


# ---------------------------------------------------------------------------
# Kolom bantu
# ---------------------------------------------------------------------------

market_df = market_df.copy()
market_df["symbol_upper"] = market_df["symbol"].astype(str).str.upper()
market_df["label"] = market_df["name"] + " (" + market_df["symbol_upper"] + ")"

unit_label = f"Harga ({currency})"


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tabs_list = st.tabs([
    "📊 Ringkasan", "📒 Journal", "🔔 Alerts", "📉 Teknikal", "📈 Perbandingan",
    "💼 Portofolio", "💱 Konverter", "⭐ Watchlist", "🚀 Gainers & Losers", "📄 Laporan PDF",
    "👑 Admin Panel"
])

tab_summary = tabs_list[0]
tab_journal = tabs_list[1]
tab_alerts = tabs_list[2]     # <-- TAB BARU
tab_technical = tabs_list[3]
tab_compare = tabs_list[4]
tab_portfolio = tabs_list[5]
tab_converter = tabs_list[6]
tab_watchlist = tabs_list[7]
tab_movers = tabs_list[8]
tab_report = tabs_list[9]
tab_admin = tabs_list[10]

# ===========================================================================
# TAB 1 - Ringkasan
# ===========================================================================

with tab_summary:
    top_n = min(config.SUMMARY_CARD_COUNT, len(market_df))
    st.subheader(f"Ringkasan {top_n} Koin Teratas")

    top_rows = market_df.head(top_n)
    cols = st.columns(top_n)
    for col, (_, row) in zip(cols, top_rows.iterrows()):
        col.metric(
            label=row["label"],
            value=formatting.format_money(row.get("current_price"), currency),
            delta=formatting.format_percent(row.get("price_change_percentage_24h")),
        )

    st.subheader("Grafik Harga 7 Hari")

    coin_labels = market_df["label"].tolist()
    selected_label = st.selectbox("Pilih koin:", options=coin_labels, index=0)
    selected_row = market_df.iloc[coin_labels.index(selected_label)]
    selected_id = selected_row["id"]
    selected_name = selected_row["name"]

    history_df = None
    if demo_mode:
        history_df = demo.get_demo_price_history(
            float(selected_row.get("current_price", 100.0))
        )
    else:
        try:
            history_df = cached_price_history(selected_id, currency, days=7)
        except api.ChainScopeAPIError as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Terjadi kesalahan saat mengambil riwayat harga: {exc}")

    if history_df is not None and not history_df.empty:
        fig = px.line(
            history_df,
            x="waktu",
            y="price",
            title=f"Harga {selected_name} (7 hari terakhir, {currency})",
            labels={"waktu": "Waktu", "price": unit_label},
        )
        fig.update_traces(line_color="#1f77b4")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Riwayat harga tidak tersedia.")

       # --- Tabel data ---
    st.subheader("Tabel Data Pasar")

    search_query = st.text_input(
        "🔍 Cari koin (nama atau simbol):",
        value="",
        placeholder="Contoh: bitcoin, eth, sol, ...",
        help="Filter tabel berdasarkan nama atau simbol. Kosongkan untuk melihat semua.",
    )

    filtered_df = search.filter_coins(market_df, search_query)

    if filtered_df.empty:
        st.warning(
            f"Tidak ada koin yang cocok dengan pencarian **'{search_query}'**. "
            "Coba kata kunci lain."
        )
    else:
        st.caption(
            f"Menampilkan {len(filtered_df)} dari {len(market_df)} koin."
        )

    # Data yang dipakai untuk tabel & CSV
    table_source = filtered_df if not filtered_df.empty else market_df.iloc[0:0]

    table_view = pd.DataFrame({
        "Nama": table_source["name"].values,
        "Simbol": table_source["symbol_upper"].values,
        f"Harga ({currency})": table_source["current_price"].map(
            lambda v: formatting.format_money(v, currency)
        ).values,
        f"Kap. Pasar ({currency})": table_source["market_cap"].map(
            lambda v: formatting.format_money(v, currency)
        ).values,
        f"Volume 24j ({currency})": table_source["total_volume"].map(
            lambda v: formatting.format_money(v, currency)
        ).values,
        "Perubahan 24j (%)": table_source["price_change_percentage_24h"].map(
            formatting.format_percent
        ).values,
    })

    st.dataframe(table_view, width="stretch", hide_index=True)

    # --- Ekspor CSV (angka mentah) ---
    csv_export = pd.DataFrame({
        "Nama": table_source["name"],
        "Simbol": table_source["symbol_upper"],
        f"harga_{currency.lower()}": table_source["current_price"],
        f"kap_pasar_{currency.lower()}": table_source["market_cap"],
        f"volume_24j_{currency.lower()}": table_source["total_volume"],
        "perubahan_24j_persen": table_source["price_change_percentage_24h"],
    })
    csv_bytes = csv_export.to_csv(index=False).encode("utf-8")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = (
        f"chainscope_{data_source.lower()}_{currency.lower()}"
        f"_top{len(table_source)}_{timestamp}.csv"
    )

    st.download_button(
        label="⬇️ Unduh CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
    )
    st.caption(
        "Nilai di CSV adalah angka mentah (belum diformat) agar bisa "
        "diolah di Excel atau Google Sheets."
    )

# ===========================================================================
# TAB ALERTS (PRICE NOTIFICATION)
# ===========================================================================
with tab_alerts:
    st.subheader("🔔 Price Alerts")
    st.caption("Set target harga. Dapatkan notifikasi via Telegram saat harga tembus level target.")
    
    # --- Konfigurasi Telegram (Disimpan sementara di Session State) ---
    with st.expander("⚙️ Hubungkan ke Telegram", expanded=False):
        st.markdown(
            "1. Cari bot **@ChainScope_ID_Bot** (atau bot buatanmu) di Telegram.\n"
            "2. Kirim pesan `/start`.\n"
            "3. Buka `https://api.telegram.org/bot<TOKEN_BOT_KAMU>/getUpdates` untuk melihat Chat ID."
        )
        
        current_chat_id = user_profile.get("telegram_chat_id", "")
        tg_chat = st.text_input("Chat ID Telegram Kamu:", value=current_chat_id)
        
        if st.button("💾 Simpan Chat ID"):
            db.update_telegram_chat_id(user.id, tg_chat)
            st.success("Chat ID tersimpan!")
            st.rerun()
            
        if st.button("📨 Test Kirim Pesan"):
            if not tg_chat:
                st.error("Isi Chat ID dulu.")
            else:
                from chainscope import telegram
                global_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
                ok = telegram.send_message(global_token, tg_chat, "✅ ChainScope ID: Koneksi Telegram Berhasil!")
                if ok:
                    st.success("Pesan test terkirim! Cek Telegram kamu.")
                else:
                    st.error("Gagal kirim. Pastikan Chat ID benar dan bot sudah di-start.")
    
    # --- Form Buat Alert Baru ---
    st.markdown("### Buat Alert Baru")
    with st.form("new_alert_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
        
        alert_coin = c1.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
        alert_cond = c2.selectbox("Kondisi", ["above", "below"], format_func=lambda x: "≥ Naik ke atas" if x == "above" else "≤ Turun ke bawah")
        alert_price = c3.number_input("Target Harga", min_value=0.01, value=1000.0)
        alert_cur = c4.selectbox("Mata Uang", ["USD", "IDR"])
        
        alert_note = st.text_input("Catatan (Opsional)", placeholder="Contoh: Jual 50% posisi di sini")
        
        if st.form_submit_button("➕ Tambah Alert"):
            sym = market_df[market_df["id"]==alert_coin]["symbol_upper"].values[0]
            db.add_alert(user.id, alert_coin, sym, alert_cond, alert_price, alert_cur, alert_note)
            st.success("Alert berhasil dibuat!")
            st.rerun()

    # --- Daftar Alert Aktif ---
    st.markdown("---")
    st.markdown("### Daftar Alert")
    
    user_alerts = db.get_user_alerts(user.id)
    if not user_alerts:
        st.info("Belum ada alert yang dibuat.")
    else:
        for a in user_alerts:
            # Status
            status = "✅ TRIGGERED" if not a["is_active"] else "⏳ MENUNGGU"
            if not a["is_active"] and a.get("triggered_at"):
                status += f" ({a['triggered_at'][:10]})"
                
            col_info, col_del = st.columns([5, 1])
            
            with col_info:
                cond_str = "≥" if a["condition"] == "above" else "≤"
                st.markdown(f"**{a['symbol']}** {cond_str} **{a['target_price']:,.2f} {a['currency']}** — *{status}*")
                if a.get("note"):
                    st.caption(f"Catatan: {a['note']}")
                    
            with col_del:
                if st.button("🗑️", key=f"del_{a['id']}"):
                    db.delete_alert(a['id'])
                    st.rerun()
            st.markdown("---")

    # --- Tombol Cek Manual ---
    st.markdown("### Cek Alert Sekarang")
    st.caption("Klik tombol ini untuk mengecek harga saat ini dan mengirim notifikasi jika target tercapai.")
    
    if st.button("🔍 Cek Alert Saat Ini", type="primary"):
        tg_t = st.session_state.get("tg_token", "")
        tg_c = st.session_state.get("tg_chat", "")
        
        if not tg_t or not tg_c:
            st.warning("⚠️ Simpan Token dan Chat ID Telegram terlebih dahulu di menu atas.")
        else:
            from chainscope import telegram
            triggered_count = 0
            
            for a in user_alerts:
                if not a["is_active"]:
                    continue # Skip yang sudah trigger
                
                # Dapatkan harga koin di market_df
                coin_data = market_df[market_df["id"] == a["coin_id"]]
                if coin_data.empty:
                    continue # Koin tidak ada di Top-N saat ini
                    
                current_price = float(coin_data.iloc[0]["current_price"])
                
                # Cek apakah kondisi terpenuhi
                is_hit = (
                    (a["condition"] == "above" and current_price >= a["target_price"]) or
                    (a["condition"] == "below" and current_price <= a["target_price"])
                )
                
                if is_hit:
                    # Kirim Telegram
                    msg = (
                        f"🚨 <b>ALERT TRIGGERED!</b> 🚨\n\n"
                        f"<b>{a['symbol']}</b> telah menyentuh <b>{current_price:,.2f} {a['currency']}</b>\n"
                        f"Target: {a['condition'].upper()} {a['target_price']:,.2f} {a['currency']}\n"
                    )
                    if a.get("note"):
                        msg += f"📝 Catatan: {a['note']}\n"
                        
                    ok = telegram.send_message(tg_t, tg_c, msg)
                    if ok:
                        db.mark_alert_triggered(a["id"])
                        triggered_count += 1
            
            if triggered_count > 0:
                st.success(f"✅ {triggered_count} alert terpicu dan notifikasi terkirim ke Telegram!")
                st.rerun()
            else:
                st.info("Belum ada harga yang menyentuh target alert kamu.")

# ===========================================================================
# TAB 3 - Portofolio
# ===========================================================================

with tab_portfolio:
    st.subheader("💼 Portofolio Otomatis")
    st.caption(
        "Nilai dan P&L dihitung secara otomatis berdasarkan histori transaksi "
        "di Trading Journal Anda."
    )

    # 1. Ambil data trades dari database
    trades = db.get_user_trades(user.id)
    
    if not trades:
        st.info("Belum ada transaksi di Trading Journal. Silakan isi tab 📒 Journal terlebih dahulu.")
    else:
        # 2. Hitung portofolio
        from chainscope import journal_calc
        pf_df = journal_calc.calculate_portfolio_from_trades(trades)

        if pf_df.empty:
            st.warning("Semua aset Anda sudah terjual (saldo 0).")
        else:
            # 3. Gabungkan dengan data harga saat ini (market_df)
            # Kita perlu tahu harga terkini untuk menghitung P&L
            pf_df = pf_df.merge(
                market_df[["id", "current_price", "name"]], 
                left_on="coin_id", right_on="id", how="left"
            )
            
            # 4. Kalkulasi Nilai & P&L
            usd_idr_rate_pf = cached_usd_idr_rate()
            if demo_mode:
                usd_idr_rate_pf = float(config.DEMO_USD_TO_IDR)

            # Jika mata uang IDR, konversi semua angka
            rate = usd_idr_rate_pf if currency == "IDR" else 1.0

                        # Harga dari market_df SUDAH dalam bentuk IDR/USD, jadi jangan dikali rate lagi!
            pf_df["current_price"] = pf_df["current_price"].fillna(0)
            
            # Harga dari database Trading Journal masih USD, jadi HARUS dikali rate
            pf_df["avg_buy_price"] = pf_df["avg_buy_price_usd"] * rate
            pf_df["invested"] = pf_df["total_invested_usd"] * rate
            pf_df["current_value"] = pf_df["amount"] * pf_df["current_price"]
            pf_df["pnl"] = pf_df["current_value"] - pf_df["invested"]
            pf_df["pnl_pct"] = (pf_df["pnl"] / pf_df["invested"] * 100).fillna(0)

            # 5. Kartu Ringkasan
            total_val = pf_df["current_value"].sum()
            total_inv = pf_df["invested"].sum()
            total_pnl = total_val - total_inv
            total_pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Nilai Portofolio", formatting.format_money(total_val, currency))
            col2.metric("Total Modal", formatting.format_money(total_inv, currency))
            col3.metric(
                "P&L Keseluruhan", 
                formatting.format_money(total_pnl, currency),
                delta=f"{formatting.format_percent(total_pnl_pct)}"
            )

            # 6. Tabel Portofolio
            st.markdown("### Rincian Aset")
            display_df = pd.DataFrame({
                "Koin": pf_df["name"] + " (" + pf_df["symbol"] + ")",
                "Jumlah": pf_df["amount"].map(lambda x: f"{x:.8f}"),
                "Harga Rata-rata": pf_df["avg_buy_price"].map(lambda v: formatting.format_money(v, currency)),
                "Harga Kini": pf_df["current_price"].map(lambda v: formatting.format_money(v, currency)),
                "Nilai Kini": pf_df["current_value"].map(lambda v: formatting.format_money(v, currency)),
                "P&L": pf_df["pnl"].map(lambda v: formatting.format_money(v, currency)),
                "P&L (%)": pf_df["pnl_pct"].map(formatting.format_percent),
            })
            st.dataframe(display_df, width="stretch", hide_index=True)

            # 7. Pie Chart
            fig_pie = px.pie(
                pf_df, values="current_value", names="name",
                title=f"Alokasi Aset ({currency})", hole=0.4
            )
            st.plotly_chart(fig_pie, width="stretch")

# ===========================================================================
# TAB 2 - Analisis Teknikal
# ===========================================================================

# ===========================================================================
# TAB JOURNAL (Manual & CSV Import)
# ===========================================================================
with tab_journal:
    st.subheader("📒 Trading Journal")
    st.caption("Catat transaksi manual atau import dari CSV exchange.")
    
    col_manual, col_csv = st.columns(2)
    
    # A. Input Manual
    with col_manual:
        st.markdown("**Input Manual**")
        with st.form("manual_trade_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            t_coin = c1.selectbox("Koin", market_df["id"].tolist(), format_func=lambda x: market_df[market_df["id"]==x]["label"].values[0])
            t_side = c2.selectbox("Aksi", ["buy", "sell"])
            t_date = c3.date_input("Tanggal", datetime.now())
            
            c4, c5 = st.columns(2)
            t_amount = c4.number_input("Jumlah Koin", min_value=0.00000001, format="%.8f")
            t_price = c5.number_input("Harga (USD)", min_value=0.01)
            
            if st.form_submit_button("Simpan Transaksi"):
                sym = market_df[market_df["id"]==t_coin]["symbol_upper"].values[0]
                db.add_trade(user.id, t_coin, sym, t_side, t_amount, t_price, str(t_date))
                st.success("Transaksi tersimpan!")
                st.rerun()

    # B. CSV Import
    with col_csv:
        st.markdown("**Import CSV (Exchange)**")
        uploaded_file = st.file_uploader("Pilih file CSV", type=["csv"])
        if uploaded_file:
            try:
                df_csv = pd.read_csv(uploaded_file)
                st.write("Pratinjau Data:", df_csv.head(3))
                
                # Pemetaan Kolom sederhana
                st.markdown("**Pemetaan Kolom**")
                col_options = df_csv.columns.tolist()
                
                map_coin = st.selectbox("Kolom Koin", col_options)
                map_side = st.selectbox("Kolom Aksi (Buy/Sell)", col_options)
                map_amount = st.selectbox("Kolom Jumlah", col_options)
                map_price = st.selectbox("Kolom Harga", col_options)
                map_date = st.selectbox("Kolom Tanggal", col_options)
                
                if st.button("Proses & Simpan CSV"):
                    success_count = 0
                    for _, row in df_csv.iterrows():
                        c_id = str(row[map_coin]).lower()
                        valid = market_df[market_df["id"].str.contains(c_id, case=False) | market_df["symbol"].str.contains(c_id, case=False)]
                        if valid.empty:
                            continue 
                        
                        real_id = valid.iloc[0]["id"]
                        real_sym = valid.iloc[0]["symbol_upper"]
                        
                        db.add_trade(
                            user.id, real_id, real_sym, 
                            str(row[map_side]).lower(), 
                            float(row[map_amount]), 
                            float(row[map_price]), 
                            str(row[map_date]), 
                            source="csv"
                        )
                        success_count += 1
                    st.success(f"Berhasil mengimport {success_count} transaksi!")
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal membaca CSV: {e}")

        # C. Riwayat Transaksi
    st.markdown("---")
    st.markdown("### Riwayat Transaksi")
    trades = db.get_user_trades(user.id)
    if not trades:
        st.info("Belum ada transaksi.")
    else:
        df_trades = pd.DataFrame(trades)
        df_trades["trade_time"] = pd.to_datetime(df_trades["trade_time"]).dt.date
        st.dataframe(df_trades[["trade_time", "symbol", "side", "amount", "price_usd"]].rename(columns={
            "trade_time": "Tanggal", "symbol": "Koin", "side": "Aksi", "amount": "Jumlah", "price_usd": "Harga (USD)"
        }), width="stretch", hide_index=True)

    # --- TOMBOL HAPUS (KODE YANG BENAR) ---
    st.markdown("---")
    if st.button("🗑️ Hapus Semua Transaksi", type="secondary", key="btn_hapus_journal"):
        db.delete_all_user_trades(user.id)  # <-- Hapus tanda '=' dan teks anehnya
        st.success("Semua transaksi berhasil dihapus.")
        st.rerun()

with tab_technical:
    st.subheader("📉 Analisis Teknikal")
    st.caption(
        "Analisis harga dengan candlestick, moving average, Bollinger Bands, "
        "dan RSI. Cocok untuk mengidentifikasi tren dan momentum."
    )
    

    # --- Pilihan koin & timeframe ---
    id_to_label_t = dict(zip(market_df["id"], market_df["label"]))
    label_to_id_t = dict(zip(market_df["label"], market_df["id"]))

    col_coin, col_tf, col_mode = st.columns([3, 2, 2])
    with col_coin:
        tech_label = st.selectbox(
            "Koin:",
            options=market_df["label"].tolist(),
            index=0,
            key="tech_coin",
        )
    with col_tf:
        # CoinGecko OHLC hanya menerima days tertentu
        TF_OPTIONS = {
            "1 jam": 1,
            "24 jam": 1,
            "7 hari": 7,
            "30 hari": 30,
            "90 hari": 90,
            "1 tahun": 365,
        }
        tech_tf_label = st.selectbox(
            "Timeframe:",
            options=list(TF_OPTIONS.keys()),
            index=2,
            key="tech_tf",
        )
    with col_mode:
        chart_mode = st.radio(
            "Mode grafik:",
            options=["Line", "Candlestick"],
            horizontal=True,
            key="tech_mode",
        )

    tech_id = label_to_id_t[tech_label]
    tech_tf_days = TF_OPTIONS[tech_tf_label]

    # --- Indikator toggles ---
    with st.expander("Indikator", expanded=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            show_ma20 = st.checkbox("MA20", value=True)
        with c2:
            show_ma50 = st.checkbox("MA50", value=False)
        with c3:
            show_bb = st.checkbox("Bollinger Bands", value=False)
        with c4:
            sub_chart = st.selectbox(
                "Sub-chart:", ["RSI", "Volume", "Tidak ada"], index=0
            )
        with c5:
            log_scale = st.checkbox("Skala log", value=False)

    # --- Ambil data ---
    tech_history = None
    tech_ohlc = None

    if demo_mode:
        row = market_df[market_df["id"] == tech_id].iloc[0]
        tech_history = demo.get_demo_price_history(
            float(row.get("current_price", 100.0))
        )
        # Buat OHLC sintetis dari line
        tech_ohlc = tech_history.copy()
        tech_ohlc = tech_ohlc.rename(columns={"price": "close"})
        tech_ohlc["open"] = tech_ohlc["close"].shift(1).fillna(tech_ohlc["close"])
        tech_ohlc["high"] = tech_ohlc[["open", "close"]].max(axis=1) * 1.005
        tech_ohlc["low"] = tech_ohlc[["open", "close"]].min(axis=1) * 0.995
        tech_history["volume"] = None
    else:
        try:
            tech_history = cached_price_history(tech_id, currency, tech_tf_days)
        except api.ChainScopeAPIError as exc:
            st.error(f"Gagal mengambil data harga: {exc}")
        try:
            if chart_mode == "Candlestick":
                tech_ohlc = cached_ohlc(tech_id, currency, tech_tf_days)
        except api.ChainScopeAPIError as exc:
            st.warning(f"OHLC tidak tersedia: {exc}. Menampilkan mode Line.")

    # --- Grafik utama ---
    if tech_history is None or tech_history.empty:
        st.info("Data teknikal tidak tersedia.")
    else:
        history = tech_history.copy()

        # Hitung indikator
        history["ma20"] = indicators.sma(history["price"], 20)
        history["ma50"] = indicators.sma(history["price"], 50)
        bb_mid, bb_upper, bb_lower = indicators.bollinger_bands(
            history["price"], window=20, num_std=2
        )
        history["bb_mid"] = bb_mid
        history["bb_upper"] = bb_upper
        history["bb_lower"] = bb_lower
        history["rsi"] = indicators.rsi(history["price"], 14)

        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Layout: 1 baris untuk harga, 1 baris untuk sub-chart (jika ada)
        if sub_chart == "Tidak ada":
            fig_t = make_subplots(
                rows=1, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
            )
        else:
            fig_t = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3],
            )

        # --- Chart utama: Line atau Candlestick ---
        use_candle = (
            chart_mode == "Candlestick"
            and tech_ohlc is not None
            and not tech_ohlc.empty
        )

        if use_candle:
            fig_t.add_trace(
                go.Candlestick(
                    x=tech_ohlc["waktu"],
                    open=tech_ohlc["open"],
                    high=tech_ohlc["high"],
                    low=tech_ohlc["low"],
                    close=tech_ohlc["close"],
                    name="OHLC",
                    increasing_line_color="#2ca02c",
                    decreasing_line_color="#d62728",
                ),
                row=1, col=1,
            )
        else:
            fig_t.add_trace(
                go.Scatter(
                    x=history["waktu"],
                    y=history["price"],
                    mode="lines",
                    name="Harga",
                    line=dict(color="#1f77b4", width=2),
                ),
                row=1, col=1,
            )

        # --- Overlay indikator ---
        if show_ma20:
            fig_t.add_trace(
                go.Scatter(
                    x=history["waktu"], y=history["ma20"],
                    mode="lines", name="MA20",
                    line=dict(color="#ff7f0e", width=1.5),
                ),
                row=1, col=1,
            )
        if show_ma50:
            fig_t.add_trace(
                go.Scatter(
                    x=history["waktu"], y=history["ma50"],
                    mode="lines", name="MA50",
                    line=dict(color="#9467bd", width=1.5),
                ),
                row=1, col=1,
            )
        if show_bb:
            fig_t.add_trace(
                go.Scatter(
                    x=history["waktu"], y=history["bb_upper"],
                    mode="lines", name="BB Upper",
                    line=dict(color="rgba(128,128,128,0.6)", width=1),
                ),
                row=1, col=1,
            )
            fig_t.add_trace(
                go.Scatter(
                    x=history["waktu"], y=history["bb_lower"],
                    mode="lines", name="BB Lower",
                    line=dict(color="rgba(128,128,128,0.6)", width=1),
                    fill="tonexty",
                    fillcolor="rgba(128,128,128,0.1)",
                ),
                row=1, col=1,
            )

        # --- Sub-chart ---
        if sub_chart == "RSI":
            fig_t.add_trace(
                go.Scatter(
                    x=history["waktu"], y=history["rsi"],
                    mode="lines", name="RSI(14)",
                    line=dict(color="#8c564b", width=1.5),
                ),
                row=2, col=1,
            )
            # Garis referensi 70/30
            fig_t.add_hline(
                y=70, line_dash="dash", line_color="red",
                opacity=0.5, row=2, col=1,
            )
            fig_t.add_hline(
                y=30, line_dash="dash", line_color="green",
                opacity=0.5, row=2, col=1,
            )
            fig_t.update_yaxes(range=[0, 100], row=2, col=1, title_text="RSI")

        elif sub_chart == "Volume":
            if "volume" in history.columns and history["volume"].notna().any():
                fig_t.add_trace(
                    go.Bar(
                        x=history["waktu"], y=history["volume"],
                        name="Volume",
                        marker_color="#7f7f7f",
                    ),
                    row=2, col=1,
                )
                fig_t.update_yaxes(title_text="Volume", row=2, col=1)
            else:
                fig_t.add_annotation(
                    text="Volume tidak tersedia",
                    xref="paper", yref="paper",
                    x=0.5, y=0.15,
                    showarrow=False,
                )

        # --- Skala log ---
        if log_scale:
            fig_t.update_yaxes(type="log", row=1, col=1)

        # --- Layout ---
        fig_t.update_layout(
            title=f"{tech_label} — {tech_tf_label} ({currency})",
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            height=620 if sub_chart != "Tidak ada" else 460,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_t, width="stretch")

        # --- Info indikator terkini ---
        st.markdown("#### Nilai Indikator Terkini")
        last = history.iloc[-1]
        c_i1, c_i2, c_i3, c_i4 = st.columns(4)
        c_i1.metric("Harga", formatting.format_money(last["price"], currency))
        c_i2.metric(
            "MA20",
            formatting.format_money(last["ma20"], currency)
            if pd.notna(last["ma20"]) else "—",
        )
        c_i3.metric(
            "MA50",
            formatting.format_money(last["ma50"], currency)
            if pd.notna(last["ma50"]) else "—",
        )
        rsi_val = last["rsi"]
        rsi_status = (
            "Overbought" if rsi_val > 70
            else "Oversold" if rsi_val < 30
            else "Netral"
        )
        c_i4.metric(
            "RSI(14)",
            f"{rsi_val:.1f}",
            delta=rsi_status,
            delta_color="off",
        )

        st.caption(
            "RSI > 70 = overbought (potensi koreksi), "
            "RSI < 30 = oversold (potensi rebound). "
            "MA20 > MA50 = tren naik, sebaliknya tren turun. "
            "Indikator bukan jaminan — selalu kombinasikan dengan analisis lain."
        )

    # Tambahkan di bagian paling bawah tab_journal:
    st.markdown("---")
    if st.button("🗑️ Hapus Semua Transaksi", type="secondary"):
        db.delete_all_user_trades(user.id)
        st.success("Semua transaksi berhasil dihapus.")
        st.rerun()

# ===========================================================================
# TAB 2 - Perbandingan Multi-Koin
# ===========================================================================

with tab_compare:
    st.subheader("📈 Perbandingan Performa Multi-Koin")
    st.caption(
        "Bandingkan performa beberapa koin dalam satu grafik. "
        "Mode Normalisasi memulai semua koin dari nilai 100 agar "
        "perbandingan adil, meski harganya jauh berbeda."
    )

    coin_labels_all = market_df["label"].tolist()
    id_to_label = dict(zip(market_df["id"], market_df["label"]))
    label_to_id = dict(zip(market_df["label"], market_df["id"]))

    default_labels = coin_labels_all[:min(3, len(coin_labels_all))]

    selected_labels = st.multiselect(
        "Pilih 2–5 koin untuk dibandingkan:",
        options=coin_labels_all,
        default=default_labels,
        max_selections=5,
    )

    normalize = st.toggle(
        "Normalisasi ke 100 di awal periode (perbandingan adil)",
        value=True,
        help="Aktif: semua koin mulai dari 100. Nonaktif: tampilkan harga mentah.",
    )

    if len(selected_labels) < 2:
        st.info("Pilih minimal 2 koin untuk menampilkan grafik perbandingan.")
    else:
        selected_ids = [label_to_id[lbl] for lbl in selected_labels]

        # Ambil riwayat harga untuk setiap koin (memakai cache Streamlit)
        history_by_coin: dict[str, pd.DataFrame] = {}
        failed: list[str] = []

        for cid in selected_ids:
            if demo_mode:
                row = market_df[market_df["id"] == cid].iloc[0]
                history_by_coin[cid] = demo.get_demo_price_history(
                    float(row.get("current_price", 100.0))
                )
            else:
                try:
                    history_by_coin[cid] = cached_price_history(
                        cid, currency, days=7
                    )
                except api.ChainScopeAPIError as exc:
                    failed.append(f"{id_to_label.get(cid, cid)}: {exc}")
                except Exception as exc:  # noqa: BLE001
                    failed.append(f"{id_to_label.get(cid, cid)}: {exc}")

        if failed:
            st.warning(
                "Sebagian koin gagal diambil: " + "; ".join(failed)
            )

        comp_df = compare.build_comparison_df(history_by_coin)

        if comp_df.empty:
            st.error("Tidak ada data perbandingan yang bisa ditampilkan.")
        else:
            if normalize:
                plot_df = compare.normalize_to_100(comp_df)
                y_label = "Nilai relatif (mulai dari 100)"
                title = (
                    f"Perbandingan Performa 7 Hari "
                    f"({currency}, dinormalisasi)"
                )
            else:
                plot_df = comp_df.copy()
                y_label = f"Harga ({currency})"
                title = f"Perbandingan Harga 7 Hari ({currency})"

            # Rename kolom id -> label supaya legendanya rapi
            rename_for_plot = {
                cid: id_to_label.get(cid, cid)
                for cid in plot_df.columns
                if cid != "waktu"
            }
            plot_df = plot_df.rename(columns=rename_for_plot)

            fig_cmp = px.line(
                plot_df,
                x="waktu",
                y=[c for c in plot_df.columns if c != "waktu"],
                title=title,
                labels={"waktu": "Waktu", "value": y_label, "variable": "Koin"},
            )
            fig_cmp.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_cmp, width="stretch")

            # Ringkasan performa periode
            st.markdown("#### Ringkasan Performa 7 Hari")

            summary_rows = []
            for cid in selected_ids:
                df_coin = history_by_coin.get(cid)
                if df_coin is None or df_coin.empty:
                    continue
                first_price = float(df_coin["price"].iloc[0])
                last_price = float(df_coin["price"].iloc[-1])
                if first_price == 0:
                    continue
                change_pct = (last_price - first_price) / first_price * 100.0
                summary_rows.append({
                    "Koin": id_to_label.get(cid, cid),
                    "Harga Awal": formatting.format_money(first_price, currency),
                    "Harga Akhir": formatting.format_money(last_price, currency),
                    "Perubahan 7h (%)": formatting.format_percent(change_pct),
                })

            if summary_rows:
                st.dataframe(
                    pd.DataFrame(summary_rows),
                    width="stretch",
                    hide_index=True,
                )

# ===========================================================================
# TAB 2 - Konverter
# ===========================================================================

with tab_converter:
    st.subheader("💱 Konverter Koin")
    st.caption(
        "Hitung nilai tukar antar-aset berdasarkan harga pasar terbaru. "
        "Termasuk koin, USD, dan IDR."
    )

    # --- Hitung kurs & peta harga ---
    usd_idr_rate = cached_usd_idr_rate()

    if demo_mode:
        # Mode demo: pakai harga pasar demo, rate tetap
        usd_idr_rate = float(config.DEMO_USD_TO_IDR)

    price_map = converter.build_price_map(market_df, currency, usd_idr_rate)

    # --- Daftar aset yang bisa dipilih ---
    asset_options = ["USD", "IDR"] + market_df["id"].tolist()

    def asset_label(aid: str) -> str:
        if aid == "USD":
            return "USD — Dolar AS"
        if aid == "IDR":
            return "IDR — Rupiah"
        m = market_df[market_df["id"] == aid]
        if not m.empty:
            return m.iloc[0]["label"]
        return aid

    # --- Siapkan session state untuk fitur tukar ---
    if "conv_from" not in st.session_state:
        st.session_state.conv_from = (
            "bitcoin" if "bitcoin" in asset_options else asset_options[0]
        )
    if "conv_to" not in st.session_state:
        st.session_state.conv_to = "IDR"

    if st.session_state.conv_from not in asset_options:
        st.session_state.conv_from = asset_options[0]
    if st.session_state.conv_to not in asset_options:
        st.session_state.conv_to = (
            asset_options[1] if len(asset_options) > 1 else asset_options[0]
        )

    def _swap_assets() -> None:
        a = st.session_state.conv_from
        b = st.session_state.conv_to
        st.session_state.conv_from = b
        st.session_state.conv_to = a

    # --- Layout: Dari | Tukar | Ke ---
    col_from, col_swap, col_to = st.columns([5, 1, 5])

    with col_from:
        from_asset = st.selectbox(
            "Dari:",
            options=asset_options,
            format_func=asset_label,
            key="conv_from",
        )
    with col_swap:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        st.button("🔄", on_click=_swap_assets, help="Tukar aset")

    with col_to:
        to_asset = st.selectbox(
            "Ke:",
            options=asset_options,
            format_func=asset_label,
            key="conv_to",
        )

    # --- Input jumlah ---
    amount = st.number_input(
        f"Jumlah ({asset_label(from_asset)}):",
        min_value=0.0,
        value=1.0,
        step=0.1,
        format="%.8f",
    )

    # --- Hasil konversi ---
    st.markdown("---")

    if from_asset == to_asset:
        st.info("Pilih aset yang berbeda untuk konversi.")
    elif amount <= 0:
        st.info("Masukkan jumlah di atas nol.")
    else:
        result = converter.convert(amount, from_asset, to_asset, price_map)
        if result is None:
            st.error("Harga tidak tersedia untuk salah satu aset.")
        else:
            # Format hasil sesuai jenis aset tujuan
            if to_asset == "IDR":
                result_str = f"Rp{result:,.0f}".replace(",", ".")
            elif to_asset == "USD":
                result_str = f"${result:,.2f}"
            else:
                sym = str(
                    market_df[market_df["id"] == to_asset].iloc[0]["symbol_upper"]
                )
                if result >= 1:
                    result_str = f"{result:,.4f} {sym}"
                else:
                    result_str = f"{result:.8f} {sym}"

            st.metric(
                label=f"Hasil konversi",
                value=result_str,
                delta=None,
            )

            # Info kurs satuan
            one_unit = converter.convert(1.0, from_asset, to_asset, price_map)
            if one_unit is not None:
                if to_asset == "IDR":
                    one_unit_str = f"Rp{one_unit:,.0f}".replace(",", ".")
                elif to_asset == "USD":
                    one_unit_str = f"${one_unit:,.2f}"
                else:
                    sym = str(
                        market_df[market_df["id"] == to_asset]
                        .iloc[0]["symbol_upper"]
                    )
                    one_unit_str = f"{one_unit:.8f} {sym}"

                st.caption(
                    f"1 {asset_label(from_asset)} ≈ {one_unit_str}"
                )

    # --- Info kurs ---
    st.markdown("---")
    st.caption(
        f"💡 Kurs referensi: 1 USD ≈ Rp{usd_idr_rate:,.0f}".replace(",", ".")
        + (" (kurs tetap — Mode Demo)" if demo_mode else " (live dari CoinGecko)")
    )



# ===========================================================================
# TAB 2 - Watchlist
# ===========================================================================

with tab_watchlist:
    st.subheader("⭐ Watchlist Saya")
    st.caption(
        "Tandai koin favorit Anda. Watchlist tersimpan permanen di file "
        "`watchlist.json` di folder proyek."
    )

    available_ids = market_df["id"].tolist()
    id_to_label = dict(zip(market_df["id"], market_df["label"]))

    current_watchlist = watchlist.load_watchlist()
    valid_default = [cid for cid in current_watchlist if cid in available_ids]

    st.markdown("**Pilih koin untuk watchlist:**")

    selected_ids = st.multiselect(
        label="Koin yang tersedia (dari Top-N di sidebar):",
        options=available_ids,
        default=valid_default,
        format_func=lambda cid: id_to_label.get(cid, cid),
        label_visibility="collapsed",
    )

    # Simpan hanya jika berubah
    if set(selected_ids) != set(current_watchlist):
        watchlist.save_watchlist(selected_ids)
        current_watchlist = selected_ids

    # Peringatan jika ada koin watchlist yang tidak muncul di Top-N
    missing_ids = [
        cid for cid in current_watchlist if cid not in available_ids
    ]
    if missing_ids:
        st.info(
            f"ℹ️ {len(missing_ids)} koin watchlist Anda tidak ada di Top-"
            f"{coin_count} saat ini. Naikkan jumlah koin di sidebar untuk melihatnya."
        )

    st.markdown("---")

    if not current_watchlist:
        st.info(
            "Watchlist Anda masih kosong. Pilih koin di atas untuk menambahkannya."
        )
    else:
        wl_df = market_df[market_df["id"].isin(current_watchlist)].copy()
        wl_df = wl_df.set_index("id").reindex(current_watchlist).reset_index()
        wl_df = wl_df.dropna(subset=["label"])

        if wl_df.empty:
            st.warning(
                "Tidak ada koin watchlist yang muncul di Top-N saat ini."
            )
        else:
            st.markdown(f"### Ringkasan ({len(wl_df)} koin)")

            # Kartu ringkas
            card_cols = st.columns(min(3, len(wl_df)))
            for col, (_, row) in zip(card_cols, wl_df.head(3).iterrows()):
                col.metric(
                    label=row["label"],
                    value=formatting.format_money(
                        row.get("current_price"), currency
                    ),
                    delta=formatting.format_percent(
                        row.get("price_change_percentage_24h")
                    ),
                )

            # Tabel watchlist
            wl_table = pd.DataFrame({
                "Nama": wl_df["name"].values,
                "Simbol": wl_df["symbol_upper"].values,
                f"Harga ({currency})": wl_df["current_price"].map(
                    lambda v: formatting.format_money(v, currency)
                ).values,
                f"Kap. Pasar ({currency})": wl_df["market_cap"].map(
                    lambda v: formatting.format_money(v, currency)
                ).values,
                "Perubahan 24j (%)": wl_df["price_change_percentage_24h"].map(
                    formatting.format_percent
                ).values,
            })
            st.dataframe(wl_table, width="stretch", hide_index=True)

            # Ekspor CSV watchlist
            wl_csv = pd.DataFrame({
                "Nama": wl_df["name"],
                "Simbol": wl_df["symbol_upper"],
                f"harga_{currency.lower()}": wl_df["current_price"],
                f"kap_pasar_{currency.lower()}": wl_df["market_cap"],
                f"volume_24j_{currency.lower()}": wl_df["total_volume"],
                "perubahan_24j_persen": wl_df["price_change_percentage_24h"],
            })
            wl_bytes = wl_csv.to_csv(index=False).encode("utf-8")
            wl_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="⬇️ Unduh CSV Watchlist",
                data=wl_bytes,
                file_name=(
                    f"chainscope_watchlist_{currency.lower()}_"
                    f"{wl_timestamp}.csv"
                ),
                mime="text/csv",
            )

            # Tombol hapus semua
            if st.button("🗑️ Kosongkan Watchlist"):
                watchlist.save_watchlist([])
                st.success("Watchlist telah dikosongkan.")
                st.rerun()


# ===========================================================================
# TAB 3 - Gainers & Losers
# ===========================================================================

with tab_movers:
    st.subheader("Pergerakan 24 Jam")
    st.caption(f"Berdasarkan {len(market_df)} koin teratas yang dipilih di sidebar.")

    movers_df = market_df.dropna(subset=["price_change_percentage_24h"]).copy()
    movers_df = movers_df.sort_values(
        "price_change_percentage_24h", ascending=False
    ).reset_index(drop=True)

    if movers_df.empty:
        st.info("Tidak ada data perubahan 24 jam yang tersedia.")
    else:
        n_each = max(1, min(config.MOVERS_PER_SIDE, len(movers_df) // 2))

        gainers = movers_df.head(n_each).iloc[::-1]
        losers = movers_df.tail(n_each).iloc[::-1]

        col_g, col_l = st.columns(2)

        with col_g:
            st.markdown(f"#### 🟢 Top {n_each} Gainers")
            fig_g = px.bar(
                gainers,
                x="price_change_percentage_24h",
                y="symbol_upper",
                orientation="h",
                text="price_change_percentage_24h",
                labels={
                    "price_change_percentage_24h": "Perubahan 24j (%)",
                    "symbol_upper": "",
                },
            )
            fig_g.update_traces(
                marker_color="#2ca02c",
                texttemplate="%{text:+.2f}%",
                textposition="outside",
                cliponaxis=False,
            )
            fig_g.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
            st.plotly_chart(fig_g, width="stretch")

        with col_l:
            st.markdown(f"#### 🔴 Top {n_each} Losers")
            fig_l = px.bar(
                losers,
                x="price_change_percentage_24h",
                y="symbol_upper",
                orientation="h",
                text="price_change_percentage_24h",
                labels={
                    "price_change_percentage_24h": "Perubahan 24j (%)",
                    "symbol_upper": "",
                },
            )
            fig_l.update_traces(
                marker_color="#d62728",
                texttemplate="%{text:+.2f}%",
                textposition="outside",
                cliponaxis=False,
            )
            fig_l.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
            st.plotly_chart(fig_l, width="stretch")

        # Scatter
        st.markdown("#### Sebaran Perubahan vs Volume 24 Jam")
        scatter_df = movers_df.dropna(
            subset=["total_volume", "market_cap", "current_price"]
        ).copy()
        scatter_df = scatter_df[scatter_df["total_volume"] > 0]

        if scatter_df.empty:
            st.info("Data tidak cukup untuk menampilkan scatter plot.")
        else:
            fig_s = px.scatter(
                scatter_df,
                x="price_change_percentage_24h",
                y="total_volume",
                size="market_cap",
                color="price_change_percentage_24h",
                color_continuous_scale="RdYlGn",
                hover_name="name",
                log_y=True,
                labels={
                    "price_change_percentage_24h": "Perubahan 24j (%)",
                    "total_volume": f"Volume 24j ({currency}, skala log)",
                    "market_cap": "Kap. Pasar",
                },
            )
            fig_s.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_s, width="stretch")
            st.caption(
                "Titik lebih besar = kapitalisasi pasar lebih besar. "
                "Warna hijau = naik, merah = turun."
            )

        # Tabel mini
        st.markdown("#### Rincian Movers")

        def _mini_table(df: pd.DataFrame, label: str) -> pd.DataFrame:
            view = pd.DataFrame({
                "Koin": df["label"].values,
                f"Harga ({currency})": df["current_price"].map(
                    lambda v: formatting.format_money(v, currency)
                ).values,
                "Perubahan 24j (%)": df["price_change_percentage_24h"]
                    .map(formatting.format_percent).values,
                f"Volume 24j ({currency})": df["total_volume"].map(
                    lambda v: formatting.format_money(v, currency)
                ).values,
            })
            view.index = range(1, len(view) + 1)
            view.index.name = label
            return view

        cg, cl = st.columns(2)
        with cg:
            st.markdown("**Gainers**")
            st.dataframe(
                _mini_table(gainers.iloc[::-1], "Peringkat"),
                width="stretch",
            )
        with cl:
            st.markdown("**Losers**")
            st.dataframe(
                _mini_table(losers.iloc[::-1], "Peringkat"),
                width="stretch",
            )

# ===========================================================================
# TAB 5 - Laporan PDF
# ===========================================================================

with tab_report:
    st.subheader("📄 Laporan PDF Mingguan")
    st.caption(
        "Unduh ringkasan pasar dalam format PDF. Cocok untuk diarsipkan "
        "atau dibagikan ke rekan. Laporan berisi harga, perubahan 24 jam, "
        "dan disclaimer."
    )

    col_a, col_b = st.columns([2, 3])
    with col_a:
        report_top_n = st.selectbox(
            "Jumlah koin di tabel laporan:",
            options=[5, 10, 20],
            index=1,
        )

    # --- Session state agar PDF tidak hilang saat klik di tempat lain ---
    if "report_bytes" not in st.session_state:
        st.session_state.report_bytes = None
        st.session_state.report_filename = None

    if st.button("📄 Buat Laporan PDF"):
        try:
            pdf_bytes = report.build_weekly_report(
                market_df,
                currency=currency,
                data_source=data_source,
                top_n=report_top_n,
            )
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            st.session_state.report_bytes = pdf_bytes
            st.session_state.report_filename = (
                f"chainscope_report_{data_source.lower()}"
                f"_{currency.lower()}_top{report_top_n}_{ts}.pdf"
            )
            st.success(
                f"Laporan berhasil dibuat "
                f"({len(pdf_bytes):,} bytes). Klik tombol unduh di bawah."
            )
        except Exception as exc:  # noqa: BLE001
            st.session_state.report_bytes = None
            st.error(f"Gagal membuat laporan: {exc}")

    if st.session_state.report_bytes:
        st.download_button(
            label="⬇️ Unduh Laporan PDF",
            data=st.session_state.report_bytes,
            file_name=st.session_state.report_filename or "chainscope_report.pdf",
            mime="application/pdf",
            key="download_report_pdf",
        )
        st.caption(
            f"File: `{st.session_state.report_filename}`"
        )

    st.markdown("---")
    st.markdown(
        "**Isi laporan:**\n"
        "- Sumber data (live / demo) dan mata uang\n"
        "- Ringkasan 3 koin teratas\n"
        f"- Tabel top-N koin (N = pilihan di atas)\n"
        "- Disclaimer investasi"
    )

# ===========================================================================
# TAB ADMIN PANEL (KHUSUS DEV)
# ===========================================================================
with tab_admin:
    if not is_dev:
        st.error("⛔ Akses ditolak. Hanya untuk Developer.")
    else:
        from chainscope import admin
        st.subheader("👑 Developer Admin Panel")
        st.caption("Kelola user, role, dan status langganan.")
        
        # Ambil semua user
        all_users = admin.get_all_users()
        
        if not all_users:
            st.info("Belum ada user yang terdaftar.")
        else:
            import pandas as pd
            
            # Tampilkan Tabel Semua User
            df_users = pd.DataFrame(all_users)
            if "subscription_end" in df_users.columns:
                df_users["subscription_end"] = df_users["subscription_end"].fillna("—").str[:10]
                
            display_cols = ["email", "role", "subscription_tier", "subscription_end"]
            st.dataframe(df_users[display_cols].rename(columns={
                "email": "Email", "role": "Role", "subscription_tier": "Plan", "subscription_end": "Berakhir Pada"
            }), width="stretch", hide_index=True)
            
            st.markdown("---")
            st.markdown("### Kelola User")
            
            # Pilih user yang ingin diedit
            user_emails = [u["email"] for u in all_users]
            selected_email = st.selectbox("Pilih user untuk diedit:", options=user_emails)
            
            if selected_email:
                selected_user = next((u for u in all_users if u["email"] == selected_email), None)
                uid = selected_user["id"]
                
                col_r, col_t, col_d = st.columns(3)
                
                with col_r:
                    # Ubah Role
                    current_role = selected_user.get("role", "user")
                    new_role = st.selectbox("Role:", ["user", "dev"], index=0 if current_role == "user" else 1)
                    if st.button("Update Role"):
                        admin.update_user_role(uid, new_role)
                        st.success("Role berhasil diupdate.")
                        st.rerun()
                        
                with col_t:
                    # Ubah Tier
                    current_tier = selected_user.get("subscription_tier", "free")
                    new_tier = st.selectbox("Langganan:", ["free", "premium"], index=0 if current_tier == "free" else 1)
                    if st.button("Update Tier"):
                        admin.update_user_subscription(uid, new_tier)
                        st.success("Langganan berhasil diupdate.")
                        st.rerun()
                        
                with col_d:
                    # Ubah Tanggal Berakhir
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    new_end = st.date_input("Perpanjang s/d:")
                    if st.button("Set Tanggal Expired"):
                        admin.update_user_subscription(uid, new_tier, str(new_end))
                        st.success("Masa aktif berhasil diperbarui.")
                        st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.caption(
    "ChainScope ID — data publik, tanpa jaminan keuntungan. "
    "Selalu lakukan riset mandiri."
)