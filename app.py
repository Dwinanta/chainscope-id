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

from chainscope import (
    api, compare, config, converter, demo, formatting, portfolio,
    report, search, watchlist,
)

# ---------------------------------------------------------------------------
# Konfigurasi halaman
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ChainScope ID",
    page_icon="📈",
    layout="wide",
)


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


(
    tab_summary,
    tab_compare,
    tab_portfolio,
    tab_converter,
    tab_watchlist,
    tab_movers,
    tab_report,
) = st.tabs(
    [
        "📊 Ringkasan",
        "📈 Perbandingan",
        "💼 Portofolio",
        "💱 Konverter",
        "⭐ Watchlist",
        "🚀 Gainers & Losers",
        "📄 Laporan PDF",
    ]
)

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
# TAB 3 - Portofolio
# ===========================================================================

with tab_portfolio:
    st.subheader("💼 Portofolio Saya")
    st.caption(
        "Lacak nilai portofolio Anda. Harga beli diinput dalam USD "
        "(denominasi umum crypto), nilai ditampilkan dalam mata uang "
        "yang dipilih di sidebar. Data tersimpan di `portfolio.json`."
    )

    # --- Hitung kurs & portofolio ---
    usd_idr_rate_pf = cached_usd_idr_rate()
    if demo_mode:
        usd_idr_rate_pf = float(config.DEMO_USD_TO_IDR)

    holdings = portfolio.load_holdings()

    # --- Form tambah / perbarui holding ---
    st.markdown("### Tambah / Perbarui Holding")

    coin_options_pf = market_df["id"].tolist()
    id_to_label_pf = dict(zip(market_df["id"], market_df["label"]))

    with st.form("portfolio_form", clear_on_submit=False):
        col_c, col_a, col_p = st.columns([3, 2, 2])
        with col_c:
            pf_coin = st.selectbox(
                "Koin:",
                options=coin_options_pf,
                format_func=lambda cid: id_to_label_pf.get(cid, cid),
            )
        with col_a:
            pf_amount = st.number_input(
                "Jumlah (unit koin):",
                min_value=0.0,
                value=1.0,
                step=0.01,
                format="%.8f",
            )
        with col_p:
            pf_buy_price = st.number_input(
                "Harga beli rata-rata (USD):",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
                help="Isi 0 jika tidak ingin menghitung P&L.",
            )

        submitted = st.form_submit_button("➕ Simpan Holding")

        if submitted:
            if pf_amount <= 0:
                st.error("Jumlah harus lebih besar dari 0.")
            else:
                portfolio.add_or_update_holding(
                    pf_coin, pf_amount, pf_buy_price
                )
                st.success(
                    f"Holding {id_to_label_pf.get(pf_coin, pf_coin)} "
                    f"tersimpan."
                )
                st.rerun()

    # --- Tampilkan portofolio ---
    st.markdown("---")

    if not holdings:
        st.info(
            "Portofolio masih kosong. Tambahkan holding di form di atas."
        )
    else:
        pf_df = portfolio.compute_portfolio(
            holdings, market_df, usd_idr_rate_pf, currency
        )

        # --- Hitung total ---
        valid = pf_df[pf_df["found"] & pf_df["current_value"].notna()]
        total_value = float(valid["current_value"].sum()) if not valid.empty else 0.0
        total_invested = float(valid["invested"].sum()) if not valid.empty else 0.0
        total_pnl = total_value - total_invested
        total_pnl_pct = (
            total_pnl / total_invested * 100.0 if total_invested > 0 else None
        )

        # --- Kartu ringkasan ---
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Nilai Portofolio",
            formatting.format_money(total_value, currency),
        )
        col2.metric(
            "Total Modal",
            formatting.format_money(total_invested, currency),
        )
        delta_str = (
            f"{formatting.format_money(total_pnl, currency)}"
            f" ({formatting.format_percent(total_pnl_pct)})"
            if total_pnl_pct is not None
            else formatting.format_money(total_pnl, currency)
        )
        col3.metric("P&L", formatting.format_money(total_pnl, currency), delta=delta_str)

        # --- Tabel holding ---
        st.markdown("### Rincian Holding")

        display_rows = []
        for _, row in pf_df.iterrows():
            if not row["found"]:
                display_rows.append({
                    "Koin": row["name"],
                    "Jumlah": f"{row['amount']:.8f}",
                    "Harga Beli": formatting.format_money(
                        row["buy_price"], currency
                    ),
                    "Harga Kini": "—",
                    "Nilai Kini": "—",
                    "P&L": "—",
                    "P&L (%)": "—",
                })
                continue

            pnl_display = (
                formatting.format_money(row["pnl"], currency)
                if row["pnl"] is not None
                else "—"
            )
            pnl_pct_display = (
                formatting.format_percent(row["pnl_pct"])
                if row["pnl_pct"] is not None
                else "—"
            )

            display_rows.append({
                "Koin": f"{row['name']} ({row['symbol']})",
                "Jumlah": f"{row['amount']:.8f}",
                "Harga Beli": formatting.format_money(row["buy_price"], currency),
                "Harga Kini": formatting.format_money(row["current_price"], currency),
                "Nilai Kini": formatting.format_money(row["current_value"], currency),
                "P&L": pnl_display,
                "P&L (%)": pnl_pct_display,
            })

        st.dataframe(
            pd.DataFrame(display_rows),
            width="stretch",
            hide_index=True,
        )

        # --- Pie chart alokasi ---
        if not valid.empty:
            st.markdown("### Alokasi Portofolio")

            pie_df = valid.copy()
            pie_df["label_full"] = (
                pie_df["name"] + " (" + pie_df["symbol"] + ")"
            )
            fig_pie = px.pie(
                pie_df,
                values="current_value",
                names="label_full",
                title=f"Alokasi berdasarkan nilai ({currency})",
                hole=0.4,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, width="stretch")

        # --- Ekspor CSV portofolio ---
        csv_pf = pd.DataFrame({
            "Nama": pf_df["name"],
            "Simbol": pf_df["symbol"],
            "Jumlah": pf_df["amount"],
            f"harga_beli_{currency.lower()}": pf_df["buy_price"],
            f"harga_kini_{currency.lower()}": pf_df["current_price"],
            f"nilai_kini_{currency.lower()}": pf_df["current_value"],
            f"pnl_{currency.lower()}": pf_df["pnl"],
            "pnl_persen": pf_df["pnl_pct"],
        })
        csv_pf_bytes = csv_pf.to_csv(index=False).encode("utf-8")
        ts_pf = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇️ Unduh CSV Portofolio",
            data=csv_pf_bytes,
            file_name=f"chainscope_portfolio_{currency.lower()}_{ts_pf}.csv",
            mime="text/csv",
        )

        # --- Tombol hapus ---
        col_del1, col_del2 = st.columns([2, 2])
        with col_del1:
            coin_to_delete = st.selectbox(
                "Hapus holding:",
                options=["—"] + pf_df["coin_id"].tolist(),
                format_func=lambda cid: "—"
                if cid == "—"
                else id_to_label_pf.get(cid, cid),
            )
            if st.button("🗑️ Hapus") and coin_to_delete != "—":
                portfolio.remove_holding(coin_to_delete)
                st.success(f"Holding dihapus.")
                st.rerun()
        with col_del2:
            st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Kosongkan Semua"):
                portfolio.clear_holdings()
                st.success("Portofolio dikosongkan.")
                st.rerun()

        st.caption(
            f"💡 Kurs referensi: 1 USD ≈ Rp{usd_idr_rate_pf:,.0f}".replace(",", ".")
            + (" (kurs tetap — Mode Demo)" if demo_mode else " (live dari CoinGecko)")
        )



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

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.caption(
    "ChainScope ID — data publik, tanpa jaminan keuntungan. "
    "Selalu lakukan riset mandiri."
)