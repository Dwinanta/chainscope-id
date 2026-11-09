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
    indicators, journal_calc, performance_coach, report, search, telegram,
    admin, payment, ai_assistant, exports, research, risk,
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
            "<div class='landing-shell'><div class='landing-hero-panel'>"
            "<span class='landing-eyebrow'>"
            "<span class='auth-brand-mark'>C</span> ChainScope ID · Market intelligence"
            "</span>"
            "<div class='landing-hero'>"
            "<h1>Kenali pasar. Kelola langkah investasi Anda.</h1>"
            "<p>Pantau aset crypto, catat transaksi, dan evaluasi portofolio "
            "dalam satu dashboard yang dirancang agar mudah dipahami sejak awal.</p>"
            </div>
            "</div></div>",
            unsafe_allow_html=True,
        )

        action_col, secondary_action_col, _ = st.columns([1, 1, 3], gap="small")
        with action_col:
            if st.button(
                "Mulai gratis",
                type="primary",
                width="stretch",
                key="landing_get_started",
            ):
                st.session_state.show_landing = False
                st.rerun()
        with secondary_action_col:
            if st.button(
                "Saya sudah punya akun",
                width="stretch",
                key="landing_sign_in",
            ):
                st.session_state.show_landing = False
                st.rerun()

        st.markdown(
            "<div class='landing-section-title'>Semua yang Anda perlukan untuk mulai</div>"
            "<p style='color:var(--cs-secondary-text);margin-top:0'>"
            "Mulai dari memantau harga hingga memahami hasil transaksi Anda.</p>",
            unsafe_allow_html=True,
        )
        feature_cols = st.columns(3)
        features = [
            (
                "Pasar dalam satu tampilan",
                "Lihat harga, pergerakan, dan indikator pasar crypto dengan konteks mata uang pilihan Anda.",
            ),
            (
                "Catatan dan portofolio",
                "Simpan transaksi jurnal dan pantau posisi berdasarkan aset serta strategi.",
            ),
            (
                "Evaluasi yang lebih jelas",
                "Tinjau performa, konsentrasi aset, dan skenario risiko tanpa mengeksekusi perdagangan.",
            ),
        ]
        for column, (title, description) in zip(feature_cols, features):
            with column:
                st.markdown(
                    f"<div class='landing-card'><h3>{escape(title)}</h3>"
                    f"<p>{description}</p></div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div class='landing-section-title'>Mulai dalam tiga langkah</div>",
            unsafe_allow_html=True,
        )
        steps = [
            ("1", "Jelajahi", "Pilih mata uang dan aset yang ingin Anda pantau."),
            ("2", "Catat", "Tambahkan transaksi Anda ke jurnal untuk menjaga riwayat tetap rapi."),
            ("3", "Evaluasi", "Gunakan ringkasan portofolio dan risiko untuk membantu meninjau keputusan."),
        ]
        step_cols = st.columns(3)
        for column, (number, title, description) in zip(step_cols, steps):
            with column:
                st.markdown(
                    f"<div class='landing-card'><div class='landing-step-number'>{number}</div>"
                    f"<h3>{escape(title)}</h3><p>{description}</p></div>",
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div class='landing-disclaimer'>Informasi pasar dapat berubah dan "
            "dapat terlambat. Analitik dan kalkulator bersifat informasional, "
            "bukan rekomendasi atau jaminan hasil investasi.</div>"
            "<div class='landing-footer'>ChainScope ID · Dibuat untuk investor "
            "dan trader Indonesia.</div>",
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

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, max_entries=256, show_spinner=False)
def cached_market_data_for_ids(
    vs_currency: str,
    coin_ids: tuple[str, ...],
) -> pd.DataFrame:
    return api.fetch_market_data_for_ids(vs_currency, coin_ids)

@st.cache_data(ttl=86400, show_spinner=False)
def cached_all_coins() -> pd.DataFrame:
    return api.prepare_coin_catalog(pd.DataFrame(api.fetch_all_coins()))

@st.cache_data(ttl=300, max_entries=256, show_spinner=False)
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
def cached_usd_currency_rate(currency: str) -> tuple[float, str]:
    """Return the cached USD rate and the time it was last fetched."""
    return api.fetch_usd_currency_rate(currency), datetime.now(timezone.utc).isoformat()


def render_performance_coach(trades: list[dict], market_data: pd.DataFrame, dark_mode: bool) -> None:
    st.markdown("<h1>Performance Coach</h1>", unsafe_allow_html=True)
    st.caption(
        "Analisis hanya menggunakan transaksi jurnal akun ini. Nilai USD, "
        "metode FIFO, dan cakupan data bergantung pada catatan yang tersedia."
    )
    current_prices_usd = {
        row["id"]: row["current_price"]
        for _, row in market_data.iterrows()
        if pd.notna(row.get("current_price"))
    }
    coach = performance_coach.analyze_trades(trades, current_prices_usd)
    if not trades:
        st.info("Belum ada transaksi jurnal untuk dianalisis.")
        return

    if coach["invalid_trades"]:
        st.warning(
            f"{coach['invalid_trades']} baris jurnal tidak valid dan tidak "
            "diikutkan dalam analisis."
        )
    if coach["date_only_trades"]:
        st.info(
            f"{coach['date_only_trades']} transaksi hanya memiliki tanggal. "
            "Urutan transaksi pada hari yang sama tidak dapat dipastikan; "
            "analisis sesi UTC tidak tersedia untuk catatan tersebut."
        )
    if coach["ambiguous_trades"]:
        st.warning(
            f"{coach['ambiguous_trades']} transaksi pada aset/strategi dengan "
            "timestamp yang sama dikecualikan karena urutan FIFO-nya tidak pasti."
        )
    if coach["unmatched_sells_amount"] > 1e-12:
        st.warning(
            f"Penjualan sebanyak {coach['unmatched_sells_amount']:.8g} unit "
            "tidak cocok dengan pembelian pada strategi/aset yang sama dan "
            "tidak dihitung sebagai posisi short."
        )

    metric_columns = st.columns(5)
    metric_columns[0].metric(
        "Win rate",
        f"{coach['win_rate_pct']:.1f}%"
        if coach["win_rate_pct"] is not None else "—",
        help="Persentase penutupan FIFO dengan realized P/L positif.",
    )
    metric_columns[1].metric(
        "Profit factor",
        f"{coach['profit_factor']:.2f}"
        if coach["profit_factor"] is not None else "—",
    )
    metric_columns[2].metric(
        "Avg win",
        formatting.format_money(coach["average_win_usd"], "USD")
        if coach["average_win_usd"] is not None else "—",
    )
    metric_columns[3].metric(
        "Avg loss",
        formatting.format_money(coach["average_loss_usd"], "USD")
        if coach["average_loss_usd"] is not None else "—",
    )
    metric_columns[4].metric(
        "Avg win / loss",
        f"{coach['average_win_loss_ratio']:.2f}"
        if coach["average_win_loss_ratio"] is not None else "—",
        help="Rasio rata-rata nominal menang terhadap rugi; bukan R-multiple.",
    )

    detail_columns = st.columns(5)
    detail_columns[0].metric("Closed trades", f"{coach['closed_trades']:,}")
    detail_columns[1].metric(
        "Max realized drawdown",
        formatting.format_money(coach["max_drawdown_usd"], "USD"),
        help="Drawdown absolut pada kurva realized P/L; modal akun tidak tersedia.",
    )
    detail_columns[2].metric(
        "Best win streak",
        coach["best_win_streak"] if coach["streak_analysis_available"] else "—",
    )
    detail_columns[3].metric(
        "Best loss streak",
        coach["best_loss_streak"] if coach["streak_analysis_available"] else "—",
    )
    detail_columns[4].metric(
        "Trades / week",
        f"{coach['trades_per_week']:.1f}"
        if coach["trades_per_week"] is not None else "—",
    )

    st.info(
        "Risiko per trade dan konsistensi risiko tidak dapat dinilai tanpa "
        "stop-loss serta ekuitas/modal akun. Timeframe tidak tersimpan pada "
        "jurnal saat ini; tag strategi tidak diperlakukan sebagai timeframe."
    )
    if not coach["streak_analysis_available"]:
        st.caption(
            "Streak menang/kalah disembunyikan bila waktu penutupan tidak cukup "
            "presisi untuk menentukan urutannya."
        )
    if not coach["post_loss_size_analysis_available"]:
        st.caption(
            "Perbandingan ukuran pembelian setelah rugi memerlukan timestamp "
            "intraday yang unik; data jurnal saat ini belum cukup."
        )
    if coach["insights"]:
        st.markdown("### Insights dari jurnal")
        for insight in coach["insights"]:
            st.write(f"- {insight}")
    if coach["trend"]:
        st.caption(
            f"Perbandingan P/L terealisasi: paruh awal "
            f"{formatting.format_money(coach['trend']['earlier_realized_pnl_usd'], 'USD')}; "
            f"paruh akhir "
            f"{formatting.format_money(coach['trend']['recent_realized_pnl_usd'], 'USD')}."
        )

    strategy_stats = coach["strategy_stats"]
    asset_stats = coach["asset_stats"]
    if not strategy_stats.empty or not asset_stats.empty:
        strategy_column, asset_column = st.columns(2)
        with strategy_column:
            st.markdown("### Kinerja strategi")
            if strategy_stats.empty:
                st.info("Belum ada penutupan strategi.")
            else:
                fig = px.bar(
                    strategy_stats,
                    x="strategy_tag",
                    y="realized_pnl_usd",
                    title="Realized P/L per strategi (USD)",
                    labels={
                        "strategy_tag": "Strategi",
                        "realized_pnl_usd": "Realized P/L (USD)",
                    },
                )
                ui.apply_plotly_theme(fig, dark_mode)
                st.plotly_chart(fig, width="stretch")
                st.dataframe(
                    ui.style_dataframe(
                        strategy_stats.rename(columns={
                            "strategy_tag": "Strategi",
                            "closed_trades": "Penutupan",
                            "win_rate_pct": "Win rate (%)",
                            "realized_pnl_usd": "Realized P/L (USD)",
                            "allocated_capital_usd": "Modal terbuka (USD)",
                            "current_value_usd": "Nilai kini (USD)",
                            "unrealized_pnl_usd": "Unrealized P/L (USD)",
                            "allocation_pct": "Alokasi (%)",
                        }),
                        dark_mode,
                    ),
                    width="stretch",
                    hide_index=True,
                )
        with asset_column:
            st.markdown("### Kinerja aset")
            if asset_stats.empty:
                st.info("Belum ada hasil penutupan aset.")
            else:
                fig = px.bar(
                    asset_stats,
                    x="coin_id",
                    y="realized_pnl_usd",
                    title="Realized P/L per aset (USD)",
                    labels={
                        "coin_id": "Aset",
                        "realized_pnl_usd": "Realized P/L (USD)",
                    },
                )
                ui.apply_plotly_theme(fig, dark_mode)
                st.plotly_chart(fig, width="stretch")
    if coach["session_analysis_available"]:
        st.markdown("### Hasil per bucket waktu UTC")
        st.caption(
            "Bucket sesi adalah pengelompokan jam UTC yang sederhana, bukan "
            "jadwal bursa resmi."
        )
        st.dataframe(
            ui.style_dataframe(coach["sessions"], dark_mode),
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption(
            "Analisis sesi belum tersedia karena waktu intraday tidak tercatat "
            "pada transaksi jurnal."
        )


def render_research_assistant(
    market_data: pd.DataFrame,
    currency: str,
    dark_mode: bool,
    language: str,
    user_id: str,
    watchlist_ids: list[str],
) -> None:
    st.title(config.translate(language, "AI Research"))
    st.caption(
        "Cakupan data saat ini: aset crypto CoinGecko dan headline crypto dari "
        "feed yang tersedia. Fundamental saham/forex dan data on-chain tidak "
        "tersedia. Tidak ada data jurnal atau portofolio yang dikirim ke AI."
    )
    if market_data.empty:
        st.warning("Data pasar tidak tersedia; riset belum dapat dibuat.")
        return

    assets = market_data.drop_duplicates("id", keep="first")
    asset_ids = assets["id"].astype(str).tolist()
    labels = dict(zip(assets["id"], assets["label"]))
    watchlist_defaults = [
        asset_id
        for asset_id in sorted(set(watchlist_ids))
        if asset_id in labels
    ][:5]
    defaults = watchlist_defaults or [
        asset_id for asset_id in ("bitcoin", "ethereum") if asset_id in labels
    ] or asset_ids[:1]
    with st.form(ui.user_state_key("research_request", user_id)):
        selected_ids = st.multiselect(
            "Aset (maksimal 5)",
            options=asset_ids,
            default=defaults,
            format_func=lambda asset_id: labels.get(asset_id, asset_id),
            key=ui.user_state_key("research_asset_ids", user_id),
        )
        history_days = st.selectbox(
            "Periode data historis",
            options=[7, 30, 90],
            format_func=lambda days: f"{days} hari",
            key=ui.user_state_key("research_history_days", user_id),
        )
        question = st.text_area(
            "Pertanyaan riset",
            value="Ringkas kondisi dan risiko berdasarkan data yang tersedia.",
            max_chars=1000,
            key=ui.user_state_key("research_question", user_id),
        )
        use_ai = st.checkbox(
            "Kirim pertanyaan dan data pasar/news publik ke Gemini "
            "(penggunaan dapat dikenai biaya)",
            key=ui.user_state_key("research_use_ai", user_id),
        )
        st.caption(
            "Jangan masukkan kredensial atau informasi sensitif. Data jurnal dan "
            "portofolio ChainScope tidak disertakan."
        )
        submitted = st.form_submit_button("Buat laporan riset", type="primary")

    if submitted:
        if not selected_ids:
            st.error("Pilih setidaknya satu aset.")
        elif len(selected_ids) > 5:
            st.error("Pilih maksimal lima aset agar permintaan data tetap terbatas.")
        elif not question.strip():
            st.error("Masukkan pertanyaan riset.")
        else:
            snapshots = []
            unavailable_assets = []
            for asset_id in selected_ids:
                market_rows = market_data.loc[market_data["id"] == asset_id]
                if market_rows.empty:
                    unavailable_assets.append(str(asset_id))
                    continue
                try:
                    history = cached_price_history(
                        asset_id, currency.lower(), int(history_days)
                    )
                except api.ChainScopeAPIError:
                    unavailable_assets.append(str(asset_id))
                    continue
                snapshots.append(research.build_asset_snapshot(
                    market_rows.iloc[0].to_dict(), history, currency
                ))
            try:
                news = cached_crypto_news()
            except api.ChainScopeAPIError:
                news = []
                st.warning(
                    "Feed berita tidak tersedia; laporan tetap dibuat tanpa headline."
                )
            try:
                fear_greed = cached_fear_greed_index()
            except api.ChainScopeAPIError:
                fear_greed = None
                st.warning(
                    "Indeks Fear & Greed tidak tersedia; laporan tetap dibuat."
                )

            if snapshots:
                if unavailable_assets:
                    st.warning(
                        "Riwayat tidak tersedia untuk: "
                        + ", ".join(unavailable_assets)
                        + ". Aset tersebut dikecualikan."
                    )
                market_conditions = (
                    {
                        "source": "Alternative.me Fear & Greed Index",
                        "value": fear_greed.get("value"),
                        "classification": fear_greed.get("classification"),
                    }
                    if fear_greed else None
                )
                context = research.build_report_context(
                    snapshots, news, market_conditions
                )
                interpretation = None
                if use_ai:
                    gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
                    if not gemini_api_key:
                        st.warning(
                            "GEMINI_API_KEY belum dikonfigurasi; laporan faktual "
                            "tetap tersedia tanpa interpretasi AI."
                        )
                    else:
                        try:
                            interpretation = ai_assistant.ask_gemini(
                                gemini_api_key,
                                research.build_prompt(context, question),
                            )
                        except GoogleAPIError as exc:
                            st.error(
                                "Interpretasi AI gagal. Periksa konfigurasi dan "
                                f"coba lagi ({type(exc).__name__})."
                            )
                        except ValueError as exc:
                            st.error(f"Interpretasi AI tidak dapat disiapkan: {exc}")
                report_text = research.build_report_text(context, interpretation)
                st.session_state[
                    ui.user_state_key("research_report_result", user_id)
                ] = {
                    "context": context,
                    "interpretation": interpretation,
                    "report": report_text,
                }
            else:
                st.error(
                    "Tidak ada aset dengan riwayat harga yang tersedia; laporan "
                    "belum dibuat."
                )

    result = st.session_state.get(
        ui.user_state_key("research_report_result", user_id)
    )
    if result:
        context = result["context"]
        st.markdown("### Data terverifikasi dari provider")
        for asset in context["assets"]:
            verified = asset["verified_market_data"]
            derived = asset["derived_historical_indicators"]
            with st.container(border=True):
                st.subheader(
                    f"{verified['name']} ({verified['symbol']})"
                )
                st.caption(
                    f"ID: {verified['asset_id']} · Sumber market: CoinGecko · "
                    f"Mata uang: {verified['currency']} · "
                    f"Updated: {verified.get('provider_updated_at', 'not supplied')}"
                )
                left, right = st.columns(2)
                with left:
                    st.write(
                        f"Harga terakhir: "
                        f"{verified.get('current_price', 'Tidak tersedia')} "
                        f"{verified['currency']}"
                    )
                    st.write(
                        "Perubahan 24 jam: "
                        f"{verified.get('price_change_24h_pct', 'Tidak tersedia')}%"
                    )
                    st.write(
                        "Kapitalisasi pasar: "
                        f"{verified.get('market_cap', 'Tidak tersedia')}"
                    )
                    st.write(
                        "Volume 24 jam: "
                        f"{verified.get('total_volume', 'Tidak tersedia')}"
                    )
                    st.write(
                        "Sirkulasi / total / maksimum: "
                        f"{verified.get('circulating_supply', 'Tidak tersedia')} / "
                        f"{verified.get('total_supply', 'Tidak tersedia')} / "
                        f"{verified.get('max_supply', 'Tidak tersedia')}"
                    )
                    st.write(
                        "Fully diluted valuation: "
                        f"{verified.get('fully_diluted_valuation', 'Tidak tersedia')}"
                    )
                    st.write(
                        "Perubahan dari ATH: "
                        f"{verified.get('change_from_all_time_high_pct', 'Tidak tersedia')}%"
                    )
                with right:
                    st.write("Indikator historis turunan:")
                    if derived:
                        for name, value in derived.items():
                            st.write(f"- {name}: {value}")
                    else:
                        st.write("Belum cukup riwayat harga.")
                st.caption(asset["fundamental_data_status"])

        comparison_rows = []
        for asset in context["assets"]:
            verified = asset["verified_market_data"]
            derived = asset["derived_historical_indicators"]
            comparison_rows.append({
                "Aset": f"{verified['name']} ({verified['symbol']})",
                f"Harga ({verified['currency']})": verified.get("current_price"),
                "Perubahan 24 jam (%)": verified.get("price_change_24h_pct"),
                "Perubahan periode (%)": derived.get("period_change_pct"),
                "RSI": derived.get("rsi"),
                "Volatilitas observasi (%)": derived.get(
                    "observation_return_volatility_pct"
                ),
            })
        if len(comparison_rows) > 1:
            st.subheader("Perbandingan aset")
            st.dataframe(
                ui.style_dataframe(pd.DataFrame(comparison_rows), dark_mode),
                width="stretch",
                hide_index=True,
            )

        st.markdown("### Headline dari feed")
        if context["news_headlines"]:
            for item in context["news_headlines"]:
                st.markdown(f"- [{item['title']}]({item['url']}) — {item['source']}")
            st.caption(
                "Headline ditampilkan apa adanya; judul bukan verifikasi atas "
                "isi atau dampak peristiwa."
            )
        else:
            st.info("Tidak ada headline yang berhasil dimuat.")

        conditions = context.get("market_conditions")
        st.markdown("### Indikator pasar umum")
        if conditions:
            st.metric(
                "Fear & Greed Index",
                conditions["value"],
                help="Data dari Alternative.me; bukan indikator nilai intrinsik.",
            )
            st.caption(f"Klasifikasi provider: {conditions['classification']}")
        else:
            st.info("Fear & Greed Index tidak tersedia.")

        st.markdown("### Interpretasi yang dihasilkan AI")
        if result["interpretation"]:
            st.write(result["interpretation"])
        else:
            st.info(
                "Interpretasi AI tidak dibuat. Data faktual dan indikator "
                "historis tetap dapat diunduh tanpa memanggil layanan AI."
            )
        st.warning(
            "Indikator dan harga historis tidak memprediksi hasil mendatang; "
            "laporan bukan rekomendasi atau jaminan kinerja."
        )
        st.download_button(
            "Unduh laporan riset",
            data=result["report"].encode("utf-8"),
            file_name=f"chainscope-research-{datetime.now():%Y-%m-%d}.md",
            mime="text/markdown",
            key=ui.user_state_key("download_research_report", user_id),
        )


def render_risk_center(
    trades: list[dict],
    market_data: pd.DataFrame,
    dark_mode: bool,
    language: str,
    user_id: str,
) -> None:
    st.title(config.translate(language, "Risk Center"))
    st.caption(
        "Analisis memakai posisi FIFO dari jurnal akun ini dan harga publik "
        "CoinGecko dalam USD. Ini bukan ekuitas akun lengkap dan bukan nasihat "
        "keuangan."
    )
    current_prices = {
        row["id"]: row["current_price"]
        for _, row in market_data.iterrows()
        if pd.notna(row.get("current_price"))
    }
    coach = performance_coach.analyze_trades(trades, current_prices)
    positions = coach["positions"]
    exposure = risk.summarize_exposure(positions)
    labels = dict(zip(market_data.get("id", []), market_data.get("label", [])))

    if not trades:
        st.info("Belum ada transaksi jurnal untuk analisis risiko portofolio.")
    elif positions.empty:
        st.info("Tidak ada posisi terbuka yang cocok dengan pembelian jurnal.")
    else:
        metric_columns = st.columns(4)
        total_value = exposure["total_market_value_usd"]
        metric_columns[0].metric(
            "Nilai posisi terharga (USD)",
            formatting.format_money(total_value, "USD")
            if total_value is not None else "Tidak lengkap",
        )
        metric_columns[1].metric(
            "Aset terbuka",
            f"{positions['coin_id'].nunique():,}",
        )
        metric_columns[2].metric(
            "Strategi terbuka",
            f"{positions['strategy_tag'].nunique():,}",
        )
        metric_columns[3].metric(
            "Drawdown realized jurnal",
            formatting.format_money(coach["max_drawdown_usd"], "USD"),
            help="Drawdown absolut pada akumulasi realized P/L, bukan drawdown ekuitas akun.",
        )
        if not exposure["complete"]:
            st.warning(
                "Harga pasar tidak tersedia untuk seluruh posisi. Persentase "
                "konsentrasi tidak ditampilkan agar tidak memberi total yang menyesatkan."
            )
        else:
            chart_column, table_column = st.columns(2)
            for column, title, breakdown, key in (
                (chart_column, "Konsentrasi aset", exposure["by_asset"], "coin_id"),
                (
                    table_column,
                    "Konsentrasi strategi",
                    exposure["by_strategy"],
                    "strategy_tag",
                ),
            ):
                with column:
                    st.subheader(title)
                    if breakdown.empty:
                        st.info("Belum ada eksposur terharga.")
                    else:
                        chart_data = breakdown.copy()
                        if key == "coin_id":
                            chart_data[key] = chart_data[key].map(labels).fillna(
                                chart_data[key]
                            )
                        figure = px.pie(
                            chart_data,
                            names=key,
                            values="market_value_usd",
                            hole=0.4,
                            title=title,
                        )
                        ui.apply_plotly_theme(figure, dark_mode)
                        st.plotly_chart(figure, width="stretch")
                        display = breakdown.rename(columns={
                            key: "Kelompok",
                            "market_value_usd": "Nilai (USD)",
                            "allocation_pct": "Alokasi (%)",
                        })
                        st.dataframe(
                            ui.style_dataframe(display, dark_mode),
                            width="stretch",
                            hide_index=True,
                        )

        position_display = positions.copy()
        position_display["asset"] = position_display["coin_id"].map(labels).fillna(
            position_display["coin_id"]
        )
        st.subheader("Eksposur per posisi")
        st.dataframe(
            ui.style_dataframe(
                position_display[[
                    "asset",
                    "strategy_tag",
                    "amount",
                    "allocated_capital_usd",
                    "market_value_usd",
                    "unrealized_pnl_usd",
                ]].rename(columns={
                    "asset": "Aset",
                    "strategy_tag": "Strategi",
                    "amount": "Jumlah",
                    "allocated_capital_usd": "Modal terbuka (USD)",
                    "market_value_usd": "Nilai pasar (USD)",
                    "unrealized_pnl_usd": "P/L belum terealisasi (USD)",
                }),
                dark_mode,
            ),
            width="stretch",
            hide_index=True,
        )

    st.subheader("Position sizing dan reward-to-risk")
    st.caption(
        "Kalkulator skenario saja. Masukkan ekuitas, risiko, entry, stop, dan "
        "target secara manual; tidak membaca atau mengubah saldo akun."
    )
    with st.form(ui.user_state_key("risk_position_size", user_id)):
        side = st.selectbox(
            "Arah",
            ["long", "short"],
            key=ui.user_state_key("risk_trade_direction", user_id),
        )
        equity = st.number_input(
            "Ekuitas acuan (USD)",
            min_value=0.0,
            value=0.0,
            key=ui.user_state_key("risk_equity", user_id),
        )
        risk_percent = st.number_input(
            "Risiko maksimum (%)", min_value=0.0, max_value=100.0,
            value=0.0,
            key=ui.user_state_key("risk_percent", user_id),
        )
        entry = st.number_input(
            "Harga entry (USD)",
            min_value=0.0,
            value=0.0,
            key=ui.user_state_key("risk_entry", user_id),
        )
        stop = st.number_input(
            "Harga stop-loss (USD)",
            min_value=0.0,
            value=0.0,
            key=ui.user_state_key("risk_stop", user_id),
        )
        target = st.number_input(
            "Target (USD, opsional; 0 untuk kosong)",
            min_value=0.0,
            value=0.0,
            key=ui.user_state_key("risk_target", user_id),
        )
        submitted = st.form_submit_button("Hitung ukuran posisi")
    if submitted:
        try:
            result = risk.calculate_position_size(
                equity,
                risk_percent,
                entry,
                stop,
                target if target > 0 else None,
                direction=side,
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state[
                ui.user_state_key("risk_position_result", user_id)
            ] = result
    position_result = st.session_state.get(
        ui.user_state_key("risk_position_result", user_id)
    )
    if position_result:
        columns = st.columns(5)
        columns[0].metric(
            "Risiko nominal",
            formatting.format_money(position_result["risk_amount"], "USD"),
        )
        columns[1].metric("Unit posisi", f"{position_result['quantity']:.8g}")
        columns[2].metric(
            "Notional indikatif",
            formatting.format_money(position_result["notional"], "USD"),
        )
        columns[3].metric(
            "Notional / ekuitas",
            f"{position_result['notional_to_equity_pct']:.1f}%",
        )
        columns[4].metric(
            "Reward / risk",
            f"{position_result['reward_to_risk']:.2f}"
            if position_result["reward_to_risk"] is not None else "—",
        )
        st.caption(
            "Perhitungan mengabaikan fee, slippage, gap, likuidasi, dan perubahan "
            "harga; ukuran aktual dapat berbeda."
        )
        if position_result["notional_to_equity_pct"] > 100:
            st.warning(
                "Notional indikatif melebihi ekuitas acuan dan dapat memerlukan "
                "leverage; kalkulator tidak memeriksa margin atau likuidasi."
            )

    st.subheader("Volatilitas dan korelasi historis")
    st.caption(
        "Riwayat crypto publik 30 hari, diambil hanya setelah tombol ditekan. "
        "Volatilitas tahunan adalah estimasi dari volatilitas return harian "
        "(akar 365). Sharpe memakai asumsi suku bebas risiko nol dan return "
        "harian aset, bukan return portofolio akun. Data historis terbatas."
    )
    history_ids = list(dict.fromkeys(
        positions["coin_id"].astype(str).tolist()
        if not positions.empty else []
    ))
    selected_history_ids = history_ids[:10]
    if len(history_ids) > 10:
        st.info("Riwayat dibatasi pada 10 aset pertama untuk membatasi API requests.")
    if len(selected_history_ids) < 1:
        st.info("Diperlukan setidaknya satu posisi terbuka.")
    elif st.button(
        "Hitung volatilitas dan korelasi",
        key=ui.user_state_key("risk_history_calculate", user_id),
        icon=":material/query_stats:",
    ):
        histories = {}
        history_error = None
        for asset_id in selected_history_ids:
            try:
                histories[asset_id] = cached_price_history(
                    asset_id, "usd", days=30
                )
            except api.ChainScopeAPIError as exc:
                history_error = str(exc)
                break
        if history_error:
            st.error(f"Riwayat harga tidak lengkap: {history_error}")
        else:
            volatilities = {
                asset_id: risk.analyze_price_history(history)
                for asset_id, history in histories.items()
            }
            correlation = risk.calculate_return_correlation(histories)
            st.session_state[
                ui.user_state_key("risk_history_result", user_id)
            ] = (
                tuple(selected_history_ids),
                volatilities,
                correlation,
            )

    history_result = st.session_state.get(
        ui.user_state_key("risk_history_result", user_id)
    )
    if history_result and history_result[0] == tuple(selected_history_ids):
        _, volatilities, correlation = history_result
        volatility_df = pd.DataFrame([
            {"Aset": labels.get(asset_id, asset_id), **values}
            for asset_id, values in volatilities.items()
        ])
        st.dataframe(
            ui.style_dataframe(volatility_df, dark_mode),
            width="stretch",
            hide_index=True,
        )
        if correlation.empty:
            st.info(
                "Korelasi memerlukan minimal dua aset dan lima return harian "
                "yang selaras."
            )
        else:
            correlation.index = [
                labels.get(asset_id, asset_id) for asset_id in correlation.index
            ]
            correlation.columns = [
                labels.get(asset_id, asset_id) for asset_id in correlation.columns
            ]
            st.markdown("**Korelasi return harian**")
            st.dataframe(
                ui.style_dataframe(correlation, dark_mode),
                width="stretch",
            )
    st.info(
        "Risk-adjusted return terhadap ekuitas akun tidak dapat dihitung karena "
        "saldo, deposit/withdrawal, biaya, dan valuasi akun historis belum "
        "tersimpan. Drawdown yang ditampilkan hanya dari realized P/L jurnal."
    )


def render_selected_coin(coin_id: str, name: str, symbol: str) -> None:
    image = coin_image_by_id.get(coin_id, "")
    if not image:
        try:
            logo_market = cached_market_data_for_ids("usd", (coin_id,))
        except api.ChainScopeAPIError as exc:
            st.caption(f"Logo CoinGecko untuk {symbol} tidak tersedia: {exc}")
        else:
            matching_logo = logo_market.loc[logo_market["id"] == coin_id]
            if not matching_logo.empty:
                image = str(matching_logo.iloc[0].get("image") or "")
    st.markdown(
        "<div class='selected-assets'>"
        f"{ui.render_coin_logo(coin_id, image, 24, symbol)}"
        f"<strong>{escape(name)} ({escape(symbol)})</strong></div>",
        unsafe_allow_html=True,
    )


def coin_selector_options(
    catalog: pd.DataFrame,
    query: str,
    selected_ids: list[str] | tuple[str, ...] = (),
) -> tuple[list[str], bool]:
    """Return bounded coin matches and whether a query had no catalog match."""
    has_no_matches = bool(
        str(query).strip()
        and search.filter_coins(catalog, query).empty
    )
    options = search.coin_selector_options(
        catalog,
        query,
        selected_ids=selected_ids,
    )
    if has_no_matches:
        options = search.coin_selector_options(
            catalog,
            "",
            selected_ids=selected_ids,
        )
    return options, has_no_matches


# 4. SIDEBAR & NAVIGASI
if "current_page" not in st.session_state:
    st.session_state.current_page = "market-overview"

with st.sidebar:
    st.markdown("""
        <div class='logo-container'>
            <div class='auth-brand-mark'>C</div>
            <span style='font-size:1.1rem; font-weight:800; color:var(--cs-primary-text);'>ChainScope <span style='color:var(--cs-accent);'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)

    language = st.session_state.language

    menu_groups = [
        (
            "Market",
            {
                "market-overview": ("Market Overview", "dashboard"),
                "market-data": ("Market Data", "candlestick_chart"),
                "technical-analysis": ("Technical Analysis", "show_chart"),
            },
        ),
        (
            "Portfolio",
            {
                "portfolio": ("Portfolio", "account_balance_wallet"),
                "trading-journal": ("Trading Journal", "receipt_long"),
                "watchlist": ("Watchlist", "star"),
                "price-alerts": ("Price Alerts", "notifications_active"),
            },
        ),
        (
            "Insights",
            {
                "performance-coach": ("Performance Coach", "insights"),
                "risk-center": ("Risk Center", "health_and_safety"),
                "relative-strategy": ("Strategi Relatif", "compare_arrows"),
                "ai-research": ("AI Research", "manage_search"),
                "pdf-report": ("Laporan PDF", "description"),
            },
        ),
        (
            "Tools",
            {
                "converter": ("Converter", "currency_exchange"),
                "wallet": ("Personal Wallet", "account_balance"),
            },
        ),
    ]
    if is_dev:
        menu_groups[-1][1]["admin-panel"] = (
            "Admin Panel",
            "admin_panel_settings",
        )

    for group_name, menu_config in menu_groups:
        st.markdown(
            "<div class='sidebar-section-label'>"
            f"{escape(config.translate(language, group_name))}</div>",
            unsafe_allow_html=True,
        )
        for url_key, (display_name, icon_name) in menu_config.items():
            is_active = st.session_state.current_page == url_key
            if st.button(
                config.translate(language, display_name),
                icon=f":material/{icon_name}:",
                width="stretch",
                key=f"btn_{url_key}",
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_page = url_key
                st.rerun()

    st.markdown(
        "<div class='sidebar-section-label'>"
        f"{escape(config.translate(language, 'Preferences'))}</div>",
        unsafe_allow_html=True,
    )
    language = st.segmented_control(
        config.translate(language, "Language"),
        ["ID", "EN"],
        default=language,
        key="language",
        width="stretch",
    ) or language
    dark_mode = st.toggle(
        config.translate(language, "Dark Mode"),
        key="dark_mode",
    )
    currency = st.selectbox(
        config.translate(language, "Display currency"),
        options=list(config.CURRENCY_OPTIONS),
        index=list(config.CURRENCY_OPTIONS).index(config.DEFAULT_CURRENCY),
        format_func=lambda code: config.currency_display_label(code, language),
        key="display_currency",
    )
    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
    safe_email = escape(str(user.email))
    profile_initial = escape(str(user.email)[:1].upper() or "C")
    admin_badge = (
        "<span class='profile-badge admin-badge'>ADMIN</span>" if is_dev else ""
    )
    st.markdown(
        "<div class='sidebar-profile'>"
        f"<div class='sidebar-profile-avatar'>{profile_initial}</div>"
        "<div class='sidebar-profile-copy'>"
        f"<strong>{safe_email}</strong>"
        f"<span class='profile-badge'>{escape(sub_tier.upper())}</span>"
        f"{admin_badge}</div></div>",
        unsafe_allow_html=True,
    )

ui.apply_theme(dark_mode)

current_page = st.session_state.current_page
theme_palette = ui.get_theme_palette(dark_mode)

# 5. AMBIL DATA YANG DIPERLUKAN HALAMAN AKTIF
data_source = "LIVE"
market_df = pd.DataFrame(columns=["id", "symbol", "name", "current_price", "image"])
catalog_df = pd.DataFrame()
watchlist_ids = []
portfolio_trades = []
portfolio_positions = pd.DataFrame()
journal_trades = []
journal_has_more = False
journal_page_size = 100
journal_page_state_key = ui.user_state_key("journal_page", str(user.id))
journal_page = max(0, int(st.session_state.get(journal_page_state_key, 0)))
user_alerts = []
data_error = None

if current_page == "watchlist":
    watchlist_ids = db.get_user_watchlist(user.id)
    try:
        catalog_df = cached_all_coins()
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
    try:
        watchlist_prices = cached_market_data_for_ids(
            currency, tuple(sorted(set(watchlist_ids)))
        )
    except api.ChainScopeAPIError as exc:
        watchlist_prices = pd.DataFrame(columns=["id", "current_price", "image"])
        data_error = str(exc)
    if not catalog_df.empty:
        watched_coins = catalog_df[catalog_df["id"].isin(watchlist_ids)].copy()
        market_df = watched_coins.merge(
            watchlist_prices[["id", "current_price", "image"]]
            if {"id", "current_price", "image"}.issubset(watchlist_prices.columns)
            else pd.DataFrame(columns=["id", "current_price", "image"]),
            on="id",
            how="left",
        )
        market_df["image"] = market_df["image"].fillna("")
    elif not watchlist_prices.empty:
        market_df = watchlist_prices.copy()
elif current_page in {"portfolio", "performance-coach", "risk-center"}:
    portfolio_trades = db.get_all_user_trades(user.id)
    portfolio_positions = journal_calc.calculate_portfolio_from_trades(portfolio_trades)
    strategy_positions = performance_coach.analyze_trades(
        portfolio_trades
    )["positions"]
    position_ids = set(
        portfolio_positions["coin_id"].dropna().astype(str)
        if not portfolio_positions.empty
        else ()
    )
    if not strategy_positions.empty:
        position_ids.update(strategy_positions["coin_id"].dropna().astype(str))
    try:
        price_currency = (
            "usd"
            if current_page in {"performance-coach", "risk-center"}
            else currency
        )
        market_df = cached_market_data_for_ids(
            price_currency, tuple(sorted(position_ids))
        )
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
elif current_page == "trading-journal":
    try:
        journal_trades, journal_has_more = db.get_user_trades_page(
            user.id,
            page_size=journal_page_size,
            offset=journal_page * journal_page_size,
        )
        journal_coin_ids = tuple(sorted({
            str(trade["coin_id"]) for trade in journal_trades if trade.get("coin_id")
        }))
        market_df = cached_market_data_for_ids(currency, journal_coin_ids)
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
    try:
        catalog_df = cached_all_coins()
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
elif current_page == "price-alerts":
    try:
        user_alerts = db.get_user_alerts(user.id)
        alert_coin_ids = tuple(sorted({
            str(alert["coin_id"]) for alert in user_alerts if alert.get("coin_id")
        }))
        market_df = cached_market_data_for_ids(currency, alert_coin_ids)
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
    try:
        catalog_df = cached_all_coins()
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
elif current_page == "converter":
    try:
        market_df = cached_market_data(currency)
    except api.ChainScopeAPIError as exc:
        data_error = str(exc)
elif current_page != "wallet":
    try:
        market_df = cached_market_data(currency)
        all_coins = cached_all_coins()
        if not all_coins.empty:
            market_df = api.merge_market_and_coin_list(market_df, all_coins)
        if current_page == "ai-research":
            watchlist_ids = db.get_user_watchlist(user.id, limit=5)
            research_watchlist_ids = tuple(sorted(set(watchlist_ids))[:5])
            existing_market_ids = set(market_df["id"])
            missing_watchlist_ids = tuple(
                coin_id for coin_id in research_watchlist_ids
                if coin_id not in existing_market_ids
            )
            if missing_watchlist_ids:
                try:
                    watchlist_market = cached_market_data_for_ids(
                        currency, missing_watchlist_ids
                    )
                except api.ChainScopeAPIError as exc:
                    data_error = str(exc)
                else:
                    market_df = pd.concat(
                        [market_df, watchlist_market],
                        ignore_index=True,
                    )
    except api.ChainScopeAPIError as exc:
        st.error(f"Gagal mengambil data dari CoinGecko: {exc}")
        st.stop()

if data_error:
    st.warning(f"Sebagian data eksternal tidak tersedia: {data_error}")

market_df = api.prepare_coin_catalog(market_df)

coin_image_by_id = (
    dict(zip(market_df["id"], market_df["image"].fillna("")))
    if "image" in market_df.columns and "id" in market_df.columns
    else {}
)

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
        st.markdown(
            "<p class='page-subtitle'>LIVE MARKET DATA · PRICES AND INSIGHTS</p>",
            unsafe_allow_html=True,
        )
    with col_search:
        search_query = st.text_input("Search", placeholder="🔍 Search coins...", label_visibility="collapsed")
    with col_profile:
        with st.popover("👤"):
            st.markdown(f"### 👤 {user.email}")
            st.markdown(f"**Plan:** {sub_tier}")
            if end_date: st.markdown(f"**Aktif s/d:** {end_date[:10]}")
            if st.button("🚪 Logout", width='stretch', type="primary"): auth.logout_user()

    st.markdown("<br>", unsafe_allow_html=True)

    tracked_market_cap = pd.to_numeric(
        market_df.get("market_cap", pd.Series(dtype=float)), errors="coerce"
    ).sum()
    tracked_volume = pd.to_numeric(
        market_df.get("total_volume", pd.Series(dtype=float)), errors="coerce"
    ).sum()
    bitcoin_market_cap = pd.to_numeric(
        market_df.loc[market_df["id"] == "bitcoin", "market_cap"], errors="coerce"
    ).sum()
    tracked_btc_share = (
        bitcoin_market_cap / tracked_market_cap * 100 if tracked_market_cap else 0
    )
    overview_metrics = [
        ("Tracked market cap", formatting.format_money(tracked_market_cap, currency), "Top 250 assets"),
        ("Tracked 24h volume", formatting.format_money(tracked_volume, currency), "Top 250 assets"),
        ("BTC share", f"{tracked_btc_share:.1f}%", "Of tracked market cap"),
        ("Assets tracked", f"{len(market_df):,}", "CoinGecko market feed"),
    ]
    cols = st.columns(4)
    for col, (label, value, caption) in zip(cols, overview_metrics):
        with col:
            with st.container(border=True):
                st.caption(label.upper())
                st.markdown(f"<div class='overview-metric'>{value}</div>", unsafe_allow_html=True)
                st.caption(caption)

    st.markdown("### Market watch")
    overview_table = search.filter_coins(market_df, search_query).head(10)
    display_market_df = pd.DataFrame({
        "Logo": overview_table["image"],
        "Asset": overview_table["name"],
        "Symbol": overview_table["symbol_upper"],
        "7d trend": overview_table["sparkline_in_7d"].map(
            lambda value: value.get("price", [])
            if isinstance(value, dict) else []
        ),
        "Price": overview_table["current_price"].map(
            lambda value: "—" if pd.isna(value)
            else formatting.format_money(value, currency)
        ),
        "24h": overview_table["price_change_percentage_24h"].map(
            lambda value: "—" if pd.isna(value) else f"{value:+.2f}%"
        ),
        "Market cap": overview_table["market_cap"].map(
            lambda value: "—" if pd.isna(value)
            else formatting.format_money(value, currency)
        ),
        "24h volume": overview_table["total_volume"].map(
            lambda value: "—" if pd.isna(value)
            else formatting.format_money(value, currency)
        ),
    })
    st.dataframe(
        ui.style_dataframe(display_market_df, dark_mode),
        width="stretch",
        hide_index=True,
        column_config={
            "Logo": st.column_config.ImageColumn("Logo", width="small"),
            "Asset": st.column_config.TextColumn("Asset", width="medium"),
            "7d trend": st.column_config.LineChartColumn("7d trend", width="medium"),
        },
    )

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
                    formatting.clean_html_text(article["title"]),
                    article["url"],
                    help=f"Sumber: {article['source']}",
                )
                st.caption(article["source"])

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart, col_movers = st.columns([2.5, 1])
    with col_chart:
        with st.container(border=True):
            st.markdown(
                "<p style='font-weight:700; color:var(--cs-primary-text); "
                "font-size:1rem; margin-bottom:0.5rem;'>Market Chart</p>",
                unsafe_allow_html=True,
            )
            overview_coins = search.filter_coins(market_df, search_query)
            if overview_coins.empty:
                st.info("Tidak ada koin yang cocok dengan pencarian.")
            else:
                labels_by_id = dict(zip(overview_coins["id"], overview_coins["label"]))
                coin_control, timeframe_control = st.columns(
                    [1.2, 1], gap="small", vertical_alignment="center"
                )
                with coin_control:
                    chart_coin_id = st.selectbox(
                        "Koin:",
                        options=overview_coins["id"].tolist(),
                        format_func=lambda coin_id: labels_by_id[coin_id],
                        label_visibility="collapsed",
                        key="overview_coin_id",
                    )

                with timeframe_control:
                    tf = st.segmented_control(
                        "Timeframe",
                        ["1D", "7D", "1M", "1Y"],
                        default="7D",
                        label_visibility="collapsed",
                        key="overview_timeframe",
                        width="stretch",
                    )
                    if not tf:
                        tf = "7D"

                days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
                coin_row = market_df.loc[market_df["id"] == chart_coin_id].iloc[0]
                render_selected_coin(
                    chart_coin_id,
                    str(coin_row["name"]),
                    str(coin_row["symbol_upper"]),
                )

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
                        color_discrete_sequence=[theme_palette["market_chart"]],
                    )
                    fig_main.update_traces(
                        fillcolor=theme_palette["market_chart_fill"],
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
            html = "<p style='font-weight:700; font-size:0.95rem; color:var(--cs-primary-text); margin-bottom:10px;'>Top Gainers</p>"
            for _, r in gainers.iterrows():
                logo = ui.render_coin_logo(
                    str(r["id"]), r.get("image"), 18, str(r["symbol_upper"])
                )
                html += (
                    "<div class='mover-row'><div class='mover-asset'>"
                    f"{logo}<div><span class='mover-symbol'>"
                    f"{escape(str(r['symbol_upper']))}</span><br>"
                    f"<span class='mover-price'>{formatting.format_money(r['current_price'], currency)}</span>"
                    f"</div></div><span class='text-green'>"
                    f"+{r['price_change_percentage_24h']:.2f}%</span></div>"
                )
            html += "<hr style='margin:8px 0; border-color:var(--cs-border);'><p style='font-weight:700; font-size:0.95rem; color:var(--cs-primary-text); margin-bottom:10px;'>Top Losers</p>"
            for _, r in losers.iterrows():
                logo = ui.render_coin_logo(
                    str(r["id"]), r.get("image"), 18, str(r["symbol_upper"])
                )
                html += (
                    "<div class='mover-row'><div class='mover-asset'>"
                    f"{logo}<div><span class='mover-symbol'>"
                    f"{escape(str(r['symbol_upper']))}</span><br>"
                    f"<span class='mover-price'>{formatting.format_money(r['current_price'], currency)}</span>"
                    f"</div></div><span class='text-red'>"
                    f"{r['price_change_percentage_24h']:.2f}%</span></div>"
                )
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
                market_coin = coin_options.loc[
                    coin_options["id"] == market_coin_id
                ].iloc[0]
                render_selected_coin(
                    market_coin_id,
                    str(market_coin["name"]),
                    str(market_coin["symbol_upper"]),
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
                "Logo": table_source["image"],
                "Coin": table_source["name"],
                "Ticker": table_source["symbol_upper"],
                "7d trend": table_source["sparkline_in_7d"].map(
                    lambda value: value.get("price", [])
                    if isinstance(value, dict) else []
                ),
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
            
            event = st.dataframe(
                ui.style_dataframe(display_df, dark_mode),
                width="stretch",
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Logo": st.column_config.ImageColumn("Logo", width="small"),
                    "Coin": st.column_config.TextColumn("Coin", width="medium"),
                    "24h %": st.column_config.TextColumn("24h %", width="small"),
                    "7d trend": st.column_config.LineChartColumn(
                        "7d trend", width="medium"
                    ),
                },
            )
            
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

    selected_a = coin_options.loc[coin_options["id"] == coin_a_id].iloc[0]
    selected_b = coin_options.loc[coin_options["id"] == coin_b_id].iloc[0]
    st.markdown(
        "<div class='selected-assets'>"
        f"{ui.render_coin_logo(coin_a_id, selected_a.get('image'), 24, selected_a['symbol_upper'])}"
        f"<strong>{escape(str(selected_a['label']))}</strong>"
        "<span class='asset-pair-divider'>/</span>"
        f"{ui.render_coin_logo(coin_b_id, selected_b.get('image'), 24, selected_b['symbol_upper'])}"
        f"<strong>{escape(str(selected_b['label']))}</strong></div>",
        unsafe_allow_html=True,
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
    selected_name = (
        str(selected_rows.iloc[0]["name"]) if not selected_rows.empty else selected_symbol
    )
    selected_image = (
        selected_rows.iloc[0].get("image", "") if not selected_rows.empty else ""
    )
    st.markdown(
        "<div class='selected-assets'>"
        f"{ui.render_coin_logo(selected_coin_id, selected_image, 32, selected_symbol)}"
        f"<strong>{escape(selected_name)}</strong>"
        f"<span class='asset-symbol'>{escape(selected_symbol)}</span></div>",
        unsafe_allow_html=True,
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
        st.caption(
            "Pertanyaan dan snapshot crypto publik dikirim ke Gemini; penggunaan "
            "dapat dikenai biaya pada API key. Jangan masukkan informasi sensitif."
        )
        question = st.text_input(
            "Pertanyaan",
            placeholder="Apakah bagus beli BTC sekarang?",
            key=ui.user_state_key("technical_ai_question", str(user.id)),
        )
        if st.button(
            "Tanya AI",
            key=ui.user_state_key("technical_ai_ask", str(user.id)),
        ):
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

elif current_page == "ai-research":
    render_research_assistant(
        market_df,
        currency,
        dark_mode,
        language,
        str(user.id),
        watchlist_ids,
    )

elif current_page == "trading-journal":
    st.markdown(
        f"<h1>{config.translate(language, 'Trading Journal')}</h1>",
        unsafe_allow_html=True,
    )
    if journal_trades:
        all_journal_trades = db.get_all_user_trades(user.id)
        st.download_button(
            "Unduh seluruh jurnal CSV",
            data=exports.build_csv(
                all_journal_trades,
                [
                    "coin_id",
                    "symbol",
                    "side",
                    "amount",
                    "price_usd",
                    "trade_time",
                    "strategy_tag",
                ],
            ),
            file_name=f"chainscope-journal-{datetime.now():%Y-%m-%d}.csv",
            mime="text/csv",
            key="download_journal_csv",
        )
    
    col_manual, col_csv = st.columns(2)
    with col_manual:
        with st.container(border=True):
            st.markdown("#### Input Manual")
            if catalog_df.empty:
                st.info("Katalog koin tidak tersedia; input transaksi belum dapat digunakan.")
            else:
                coin_labels = dict(zip(catalog_df["id"], catalog_df["label"]))
                coin_symbols = dict(zip(catalog_df["id"], catalog_df["symbol_upper"]))
                coin_names = dict(zip(catalog_df["id"], catalog_df["name"]))
                trade_coin_search = st.text_input(
                    "Cari aset transaksi",
                    placeholder="Ketik nama, simbol, atau ID aset",
                    help="Maksimal 50 hasil ditampilkan; pencarian ini tidak mengubah katalog.",
                    key=ui.user_state_key("journal_coin_search", str(user.id)),
                )
                trade_coin_options, no_trade_coin_matches = coin_selector_options(
                    catalog_df,
                    trade_coin_search,
                    selected_ids=[
                        str(st.session_state.get(
                            ui.user_state_key("journal_coin_id", str(user.id)),
                            "",
                        ))
                    ],
                )
                if no_trade_coin_matches:
                    st.info(
                        "Aset tidak ditemukan. Pilihan aset populer ditampilkan."
                    )
                with st.form(
                    ui.user_state_key("manual_trade", str(user.id)),
                    clear_on_submit=True,
                ):
                    t_coin = st.selectbox(
                        "Koin",
                        trade_coin_options,
                        format_func=lambda coin_id: coin_labels[coin_id],
                        help="Pilih aset yang sama dengan aset pada transaksi Anda.",
                        key=ui.user_state_key("journal_coin_id", str(user.id)),
                    )
                    t_side = st.selectbox("Aksi", ["buy", "sell"])
                    t_date = st.date_input("Tanggal", datetime.now())
                    t_amount = st.number_input(
                        "Jumlah Koin", min_value=0.00000001, format="%.8f"
                    )
                    t_price = st.number_input("Harga (USD)", min_value=0.01)
                    t_strategy = st.text_input(
                        "Strategi",
                        value="Swing",
                        help="Pilih nama strategi yang sudah digunakan atau masukkan nama baru.",
                    )
                    if st.form_submit_button("Simpan Transaksi", width='stretch'):
                        if not t_strategy.strip():
                            st.error("Nama strategi wajib diisi.")
                        else:
                            db.add_trade(
                                user.id,
                                t_coin,
                                coin_symbols[t_coin],
                                t_side,
                                t_amount,
                                t_price,
                                str(t_date),
                                strategy_tag=t_strategy.strip(),
                            )
                            st.session_state[journal_page_state_key] = 0
                            st.success("Transaksi tersimpan!")
                            st.rerun()
                render_selected_coin(
                    t_coin, str(coin_names[t_coin]), str(coin_symbols[t_coin])
                )

    with col_csv:
        with st.container(border=True):
            st.markdown("#### Import CSV")
            uploaded = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                label_visibility="collapsed",
                key=ui.user_state_key("journal_csv_upload", str(user.id)),
            )
            if uploaded and catalog_df.empty:
                st.info("Katalog koin tidak tersedia; CSV belum dapat diproses.")
            elif uploaded:
                try:
                    df_csv = pd.read_csv(uploaded)
                    map_coin = st.selectbox(
                        "Kolom Koin",
                        df_csv.columns,
                        key=ui.user_state_key("journal_csv_coin_column", str(user.id)),
                    )
                    map_side = st.selectbox(
                        "Kolom Aksi",
                        df_csv.columns,
                        key=ui.user_state_key("journal_csv_side_column", str(user.id)),
                    )
                    map_amount = st.selectbox(
                        "Kolom Jumlah",
                        df_csv.columns,
                        key=ui.user_state_key("journal_csv_amount_column", str(user.id)),
                    )
                    map_price = st.selectbox(
                        "Kolom Harga",
                        df_csv.columns,
                        key=ui.user_state_key("journal_csv_price_column", str(user.id)),
                    )
                    map_date = st.selectbox(
                        "Kolom Tanggal",
                        df_csv.columns,
                        key=ui.user_state_key("journal_csv_date_column", str(user.id)),
                    )
                    map_strategy = st.selectbox(
                        "Kolom Strategi",
                        ["(Gunakan default)"] + list(df_csv.columns),
                        key=ui.user_state_key("journal_csv_strategy_column", str(user.id)),
                    )
                    default_strategy = st.text_input(
                        "Strategi default",
                        value="Swing",
                        key=ui.user_state_key("journal_csv_default_strategy", str(user.id)),
                    )
                    if st.button(
                        "Proses CSV",
                        width="stretch",
                        key=ui.user_state_key("journal_csv_process", str(user.id)),
                    ):
                        if not default_strategy.strip():
                            st.error("Nama strategi default wajib diisi.")
                            st.stop()
                        pending_trades = []
                        unresolved_rows = 0
                        for _, row in df_csv.iterrows():
                            resolved_id = api.resolve_coin_identifier(
                                row[map_coin], catalog_df
                            )
                            if resolved_id is not None:
                                coin = catalog_df.loc[
                                    catalog_df["id"] == resolved_id
                                ].iloc[0]
                                pending_trades.append({
                                    "coin_id": coin["id"],
                                    "symbol": coin["symbol_upper"],
                                    "side": str(row[map_side]).lower(),
                                    "amount": float(row[map_amount]),
                                    "price_usd": float(row[map_price]),
                                    "trade_time": str(row[map_date]),
                                    "source": "csv",
                                    "strategy_tag": (
                                        str(row[map_strategy]).strip()
                                        if map_strategy != "(Gunakan default)"
                                        and pd.notna(row[map_strategy])
                                        and str(row[map_strategy]).strip()
                                        else default_strategy.strip()
                                    ),
                                })
                            else:
                                unresolved_rows += 1
                        db.add_trades(user.id, pending_trades)
                        st.session_state[journal_page_state_key] = 0
                        st.success(
                            f"Import {len(pending_trades)} transaksi. "
                            f"{unresolved_rows} baris tidak diimpor karena aset "
                            "tidak ditemukan atau simbolnya ambigu."
                        )
                        st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Riwayat Transaksi")
        trades = journal_trades
        previous_col, page_col, next_col = st.columns([1, 2, 1])
        if previous_col.button(
            "Transaksi lebih baru",
            disabled=journal_page == 0,
            key=ui.user_state_key("journal_previous_page", str(user.id)),
        ):
            st.session_state[journal_page_state_key] = journal_page - 1
            st.rerun()
        page_col.caption(f"Halaman {journal_page + 1}")
        if next_col.button(
            "Transaksi lebih lama",
            disabled=not journal_has_more,
            key=ui.user_state_key("journal_next_page", str(user.id)),
        ):
            st.session_state[journal_page_state_key] = journal_page + 1
            st.rerun()
        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades["trade_time"] = pd.to_datetime(df_trades["trade_time"]).dt.date
            df_trades["Logo"] = (
                df_trades["coin_id"].map(coin_image_by_id).fillna("")
                if "coin_id" in df_trades
                else ""
            )
            labels_by_id = dict(zip(catalog_df["id"], catalog_df["label"]))
            df_trades["Aset"] = df_trades["coin_id"].map(labels_by_id)
            missing_labels = df_trades["Aset"].isna()
            df_trades.loc[missing_labels, "Aset"] = (
                df_trades.loc[missing_labels, "symbol"].astype(str).str.upper()
                + " ("
                + df_trades.loc[missing_labels, "coin_id"].astype(str)
                + ")"
            )
            st.dataframe(
                ui.style_dataframe(
                    df_trades[
                        ["Logo", "trade_time", "Aset", "side", "amount", "price_usd"]
                    ],
                    dark_mode,
                ),
                width="stretch",
                hide_index=True,
                column_config={"Logo": st.column_config.ImageColumn("Logo", width="small")},
            )
            if st.button("🗑️ Hapus Semua Transaksi", type="secondary"):
                db.delete_all_user_trades(user.id)
                st.session_state[journal_page_state_key] = 0
                st.rerun()
        else:
            st.info("Belum ada transaksi.")

elif current_page == "price-alerts":
    st.markdown(
        f"<h1>{config.translate(language, 'Price Alerts')}</h1>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("Notifikasi Telegram")
        st.caption(
            "Simpan chat ID Telegram pada profil akun Anda agar alert terjadwal "
            "dapat mengirim pesan. Nilai ini hanya digunakan oleh integrasi "
            "Telegram; bot token harus disediakan sebagai secret server."
        )
        with st.form(ui.user_state_key("telegram_chat_setup", str(user.id))):
            telegram_chat_id = st.text_input(
                "Telegram chat ID",
                value=str(user_profile.get("telegram_chat_id") or ""),
                max_chars=128,
                help="Masukkan chat ID tujuan pesan. Kosongkan untuk menghapusnya.",
                key=ui.user_state_key("telegram_chat_id", str(user.id)),
            )
            save_chat = st.form_submit_button("Simpan chat ID")
        if save_chat:
            db.update_telegram_chat_id(
                user.id,
                telegram_chat_id.strip() or None,
            )
            st.success("Pengaturan chat Telegram diperbarui.")
            st.rerun()
        if st.button(
            "Kirim pesan uji",
            key=ui.user_state_key("telegram_test_message", str(user.id)),
            icon=":material/send:",
        ):
            bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
            saved_chat_id = user_profile.get("telegram_chat_id")
            if not bot_token:
                st.warning(
                    "TELEGRAM_BOT_TOKEN belum dikonfigurasi sebagai server secret."
                )
            elif not saved_chat_id:
                st.warning("Simpan chat ID sebelum mengirim pesan uji.")
            else:
                try:
                    telegram.send_message(
                        bot_token,
                        str(saved_chat_id),
                        "ChainScope ID Telegram test message.",
                    )
                except (ValueError, telegram.TelegramAPIError) as exc:
                    st.error(f"Pesan uji Telegram gagal: {exc}")
                else:
                    st.success("Pesan uji Telegram berhasil dikirim.")

    alerts = user_alerts
    active_alert_count = (
        sum(bool(alert.get("is_active", True)) for alert in alerts)
        if sub_tier == "Free"
        else 0
    )
    if sub_tier == "Free" and active_alert_count >= 1:
        st.info(
            "Fitur Alert dibatasi 1 untuk user Free. "
            "Upgrade ke Premium untuk alert tanpa batas."
        )
    elif catalog_df.empty:
        st.info("Katalog koin tidak tersedia; alert baru belum dapat dibuat.")
    else:
        coin_labels = dict(zip(catalog_df["id"], catalog_df["label"]))
        coin_symbols = dict(zip(catalog_df["id"], catalog_df["symbol_upper"]))
        coin_names = dict(zip(catalog_df["id"], catalog_df["name"]))
        alert_coin_search = st.text_input(
            "Cari aset untuk alert",
            placeholder="Ketik nama, simbol, atau ID aset",
            help="Maksimal 50 hasil ditampilkan.",
            key=ui.user_state_key("alert_coin_search", str(user.id)),
        )
        alert_coin_options, no_alert_coin_matches = coin_selector_options(
            catalog_df,
            alert_coin_search,
            selected_ids=[
                str(st.session_state.get(
                    ui.user_state_key("alert_coin_id", str(user.id)),
                    "",
                ))
            ],
        )
        if no_alert_coin_matches:
            st.info("Aset tidak ditemukan. Pilihan aset populer ditampilkan.")
        with st.container(border=True):
            st.markdown("#### Buat Alert Baru")
            with st.form(
                ui.user_state_key("new_alert", str(user.id)),
                clear_on_submit=True,
            ):
                c1, c2, c3 = st.columns(3)
                a_coin = c1.selectbox(
                    "Koin",
                    alert_coin_options,
                    format_func=lambda coin_id: coin_labels[coin_id],
                    help="Pilih aset yang ingin Anda pantau.",
                    key=ui.user_state_key("alert_coin_id", str(user.id)),
                )
                a_cond = c2.selectbox("Kondisi", ["above", "below"])
                a_price = c3.number_input("Target Harga", min_value=0.01)
                if st.form_submit_button("Tambah Alert", width='stretch'):
                    if sub_tier == "Free" and active_alert_count >= 1:
                        st.info(
                            "Fitur Alert dibatasi 1 untuk user Free. "
                            "Upgrade ke Premium untuk alert tanpa batas."
                        )
                    else:
                        sym = coin_symbols[a_coin]
                        db.add_alert(user.id, a_coin, sym, a_cond, a_price, currency)
                        st.success("Alert dibuat!")
                        st.rerun()
            render_selected_coin(
                a_coin, str(coin_names[a_coin]), str(coin_symbols[a_coin])
            )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### Daftar Alert")
        if alerts:
            alert_coin_labels = (
                dict(zip(catalog_df["id"], catalog_df["label"]))
                if not catalog_df.empty
                else {}
            )
            alert_df = pd.DataFrame([
                {
                    "Logo": coin_image_by_id.get(alert.get("coin_id"), ""),
                    "Koin": (
                        alert_coin_labels.get(
                            alert.get("coin_id"),
                            f"{str(alert['symbol']).upper()} ({alert.get('coin_id', '')})",
                        )
                    ),
                    "Kondisi": "Di atas" if alert["condition"] == "above" else "Di bawah",
                    "Target": formatting.format_money(alert["target_price"], alert["currency"]),
                    "Status": "Menunggu" if alert.get("is_active", True) else "Terpicu",
                    "Dibuat": alert.get("created_at", "—"),
                }
                for alert in alerts
            ])
            st.dataframe(
                ui.style_dataframe(alert_df, dark_mode),
                width="stretch",
                hide_index=True,
                column_config={"Logo": st.column_config.ImageColumn("Logo", width="small")},
            )
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
    trades = portfolio_trades
    
    if not trades:
        st.info("Belum ada transaksi di Trading Journal.")
    else:
        export_rate = 1.0
        if currency != "USD":
            try:
                export_rate, _ = cached_usd_currency_rate(currency)
            except api.ChainScopeAPIError:
                st.warning(
                    "Kurs USD tidak tersedia; ekspor posisi tetap berisi modal "
                    "jurnal, tetapi nilai pasar dan P/L belum terealisasi kosong."
                )
                export_rate = None
        export_prices_usd = {}
        if export_rate:
            export_prices_usd = {
                row["id"]: float(row["current_price"]) / export_rate
                for _, row in market_df.iterrows()
                if pd.notna(row.get("current_price"))
            }
        export_analysis = performance_coach.analyze_trades(
            trades, export_prices_usd
        )
        export_columns = st.columns(2)
        export_columns[0].download_button(
            "Unduh posisi terbuka CSV",
            data=exports.build_csv(
                export_analysis["positions"].to_dict("records"),
                [
                    "coin_id",
                    "symbol",
                    "strategy_tag",
                    "amount",
                    "avg_buy_price_usd",
                    "allocated_capital_usd",
                    "current_price_usd",
                    "market_value_usd",
                    "unrealized_pnl_usd",
                ],
            ),
            file_name=f"chainscope-open-positions-{datetime.now():%Y-%m-%d}.csv",
            mime="text/csv",
            key=ui.user_state_key("download_portfolio_positions", str(user.id)),
        )
        export_columns[1].download_button(
            "Unduh hasil terealisasi CSV",
            data=exports.build_csv(
                export_analysis["outcomes"].to_dict("records"),
                [
                    "trade_time",
                    "strategy_tag",
                    "coin_id",
                    "symbol",
                    "realized_pnl_usd",
                    "closed_amount",
                    "session",
                ],
            ),
            file_name=f"chainscope-realized-results-{datetime.now():%Y-%m-%d}.csv",
            mime="text/csv",
            key=ui.user_state_key("download_portfolio_results", str(user.id)),
        )
        pf_df = portfolio_positions.copy()
        if pf_df.empty:
            strategy_analysis = performance_coach.analyze_trades(trades)
            if strategy_analysis["positions"].empty:
                st.warning("Semua aset sudah terjual.")
            else:
                st.info(
                    "Posisi agregat lintas strategi terlihat tertutup, tetapi "
                    "sebagian strategi masih memiliki posisi terbuka."
                )
                try:
                    rate, _ = cached_usd_currency_rate(currency)
                except api.ChainScopeAPIError as exc:
                    st.error(f"Gagal mengambil kurs mata uang dari CoinGecko: {exc}")
                    rate = None
                if rate is not None:
                    current_prices_usd = {
                        row["id"]: (
                            float(row["current_price"]) / rate
                            if pd.notna(row["current_price"])
                            else None
                        )
                        for _, row in market_df.iterrows()
                    }
                    strategy_analysis = performance_coach.analyze_trades(
                        trades, current_prices_usd
                    )
                st.markdown("### Portofolio per strategi")
                st.caption(
                    "Posisi dihitung terpisah berdasarkan aset dan tag strategi. "
                    "Nilai pasar tidak ditampilkan bila harga tidak tersedia."
                )
                strategy_display = strategy_analysis["positions"].copy()
                market_labels = dict(zip(market_df["id"], market_df["label"]))
                strategy_display["asset"] = strategy_display.apply(
                    lambda row: market_labels.get(
                        row["coin_id"],
                        f"{str(row['symbol']).upper()} ({row['coin_id']})",
                    ),
                    axis=1,
                )
                st.dataframe(
                    ui.style_dataframe(
                        strategy_display[[
                            "strategy_tag",
                            "asset",
                            "amount",
                            "allocated_capital_usd",
                            "market_value_usd",
                            "unrealized_pnl_usd",
                        ]].rename(columns={
                            "strategy_tag": "Strategi",
                            "asset": "Aset",
                            "amount": "Jumlah",
                            "allocated_capital_usd": "Modal terbuka (USD)",
                            "market_value_usd": "Nilai kini (USD)",
                            "unrealized_pnl_usd": "Unrealized P/L (USD)",
                        }),
                        dark_mode,
                    ),
                    width="stretch",
                    hide_index=True,
                )
        else:
            market_metadata = market_df[[
                "id", "name", "symbol_upper", "label", "current_price"
            ]].rename(columns={
                "name": "market_name",
                "symbol_upper": "market_symbol",
                "label": "market_label",
            })
            pf_df = pf_df.merge(
                market_metadata,
                left_on="coin_id",
                right_on="id",
                how="left",
            )
            pf_df["symbol"] = (
                pf_df["market_symbol"].fillna(pf_df["symbol"]).astype(str).str.upper()
            )
            pf_df["asset_label"] = pf_df["market_label"].fillna(
                pf_df["symbol"] + " (" + pf_df["coin_id"].astype(str) + ")"
            )
            pf_df["image"] = pf_df["coin_id"].map(coin_image_by_id).fillna("")
            try:
                rate, _ = cached_usd_currency_rate(currency)
            except api.ChainScopeAPIError as exc:
                st.error(f"Gagal mengambil kurs mata uang dari CoinGecko: {exc}")
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
                    "Logo": pf_df["image"],
                    "Koin": pf_df["asset_label"],
                    "Jumlah": pf_df["amount"].map(lambda x: f"{x:.4f}"),
                    "Harga Rata2": pf_df["avg_buy_price"].map(lambda v: formatting.format_money(v, currency)),
                    "Nilai Kini": pf_df["current_value"].map(lambda v: formatting.format_money(v, currency)),
                    "P&L": pf_df["pnl"].map(lambda v: formatting.format_money(v, currency)),
                })
                st.dataframe(
                    ui.style_dataframe(display_df, dark_mode),
                    width="stretch",
                    hide_index=True,
                    column_config={"Logo": st.column_config.ImageColumn("Logo", width="small")},
                )

            current_prices_usd = {
                row["id"]: (
                    float(row["current_price"]) / rate
                    if pd.notna(row["current_price"])
                    else None
                )
                for _, row in market_df.iterrows()
            }
            strategy_analysis = performance_coach.analyze_trades(
                trades, current_prices_usd
            )
            st.markdown("### Portofolio per strategi")
            st.caption(
                "Nama strategi berasal dari tag transaksi jurnal. Modal dialokasikan "
                "ke posisi terbuka dengan metode FIFO; P/L terealisasi hanya berasal "
                "dari penjualan yang cocok dengan pembelian pada strategi yang sama."
            )
            strategy_positions = strategy_analysis["positions"]
            strategy_stats = strategy_analysis["strategy_stats"]
            if strategy_positions.empty:
                st.info("Tidak ada posisi terbuka yang dapat dialokasikan per strategi.")
            else:
                strategy_display = strategy_positions.copy()
                market_labels = dict(zip(market_df["id"], market_df["label"]))
                strategy_display["asset"] = strategy_display.apply(
                    lambda row: market_labels.get(
                        row["coin_id"],
                        f"{str(row['symbol']).upper()} ({row['coin_id']})",
                    ),
                    axis=1,
                )
                market_values = pd.to_numeric(
                    strategy_display["market_value_usd"], errors="coerce"
                )
                total_market_value = market_values.sum(min_count=1)
                strategy_display["allocation_pct"] = (
                    market_values / total_market_value * 100
                    if strategy_analysis["market_data_complete"]
                    and pd.notna(total_market_value)
                    and total_market_value > 0
                    else None
                )
                strategy_display_df = pd.DataFrame({
                    "Strategy": strategy_display["strategy_tag"],
                    "Asset": strategy_display["asset"],
                    "Quantity": strategy_display["amount"],
                    "Allocated capital (USD)": strategy_display["allocated_capital_usd"],
                    "Market value (USD)": strategy_display["market_value_usd"],
                    "Unrealized P/L (USD)": strategy_display["unrealized_pnl_usd"],
                    "Allocation": strategy_display["allocation_pct"].map(
                        lambda value: f"{value:.2f}%"
                        if pd.notna(value) else "—"
                    ),
                })
                st.dataframe(
                    ui.style_dataframe(strategy_display_df, dark_mode),
                    width="stretch",
                    hide_index=True,
                )

                if not strategy_stats.empty:
                    chart_values = (
                        "current_value_usd"
                        if strategy_analysis["market_data_complete"]
                        and strategy_stats["current_value_usd"].sum() > 0
                        else "allocated_capital_usd"
                    )
                    chart_title = (
                        "Nilai posisi saat ini per strategi"
                        if chart_values == "current_value_usd"
                        else "Modal terbuka berdasarkan harga beli (harga pasar tidak lengkap)"
                    )
                    fig = px.pie(
                        strategy_stats,
                        values=chart_values,
                        names="strategy_tag",
                        color_discrete_sequence=[
                            theme_palette["accent"],
                            theme_palette["accent_secondary"],
                            theme_palette["accent_tertiary"],
                        ],
                        title=chart_title,
                    )
                    ui.apply_plotly_theme(fig, dark_mode)
                    st.plotly_chart(fig, width="stretch")
                    strategy_performance = px.bar(
                        strategy_stats,
                        x="strategy_tag",
                        y=["realized_pnl_usd", "unrealized_pnl_usd"],
                        barmode="group",
                        title="P/L terealisasi dan belum terealisasi per strategi (USD)",
                        labels={
                            "strategy_tag": "Strategi",
                            "value": "P/L (USD)",
                            "variable": "Jenis P/L",
                        },
                    )
                    ui.apply_plotly_theme(strategy_performance, dark_mode)
                    st.plotly_chart(strategy_performance, width="stretch")

    if user_profile.get("subscription_tier", "free").lower() != "premium":
        payment_order_key = ui.user_state_key(
            "premium_payment_order_id", str(user.id)
        )
        payment_url_key = ui.user_state_key(
            "premium_payment_url", str(user.id)
        )
        if st.button("🚀 Upgrade ke Premium (Rp 50.000)"):
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            order_id = (
                f"PREMIUM-{sha256(user.id.encode()).hexdigest()[:12]}-{timestamp}"
            )
            st.session_state[payment_order_key] = order_id
            try:
                st.session_state[payment_url_key] = payment.create_snap_transaction(
                    user.id, user.email, 50000, order_id=order_id
                )
            except (ValueError, payment.SnapPaymentError) as error:
                st.session_state.pop(payment_url_key, None)
                st.error(str(error))

        payment_url = st.session_state.get(payment_url_key)
        if payment_url:
            st.link_button("Bayar Sekarang", url=payment_url)

        order_id = st.session_state.get(payment_order_key)
        if order_id and st.button("Cek Status Pembayaran"):
            try:
                transaction_status = payment.check_transaction_status(order_id)
            except (ValueError, payment.SnapPaymentError) as error:
                st.error(str(error))
            else:
                if transaction_status in {"settlement", "capture"}:
                    db.upgrade_to_premium(user.id)
                    st.session_state.pop(payment_order_key, None)
                    st.session_state.pop(payment_url_key, None)
                    st.success("Pembayaran terverifikasi. Akun Premium aktif selama 30 hari.")
                elif transaction_status == "pending":
                    st.info("Pembayaran masih tertunda. Silakan selesaikan pembayaran di Midtrans.")
                elif transaction_status in {"expire", "deny"}:
                    st.error(f"Pembayaran gagal dengan status: {transaction_status}.")
                else:
                    st.warning(f"Status pembayaran saat ini: {transaction_status}.")

elif current_page == "performance-coach":
    render_performance_coach(portfolio_trades, market_df, dark_mode)

elif current_page == "risk-center":
    render_risk_center(
        portfolio_trades, market_df, dark_mode, language, str(user.id)
    )

elif current_page == "converter":
    st.markdown(
        f"<h1>{config.translate(language, 'Converter')}</h1>",
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        try:
            rate, rate_fetched_at = cached_usd_currency_rate(currency)
        except api.ChainScopeAPIError as exc:
            st.error(f"Gagal mengambil kurs mata uang dari CoinGecko: {exc}")
            st.stop()
        priced_coins = market_df.loc[
            pd.to_numeric(market_df["current_price"], errors="coerce") > 0
        ].copy()
        price_map = converter.build_price_map(priced_coins, currency, rate)
        fetched_local = datetime.fromisoformat(rate_fetched_at).astimezone()
        st.caption(
            "Kurs fiat di-cache hingga 90 detik; terakhir diperbarui "
            f"{fetched_local:%Y-%m-%d %H:%M:%S %Z}."
        )
        col1, col2 = st.columns(2)
        fiat_assets = list(dict.fromkeys(["USD", currency]))
        asset_options = fiat_assets + priced_coins["id"].tolist()
        selected_currency_index = fiat_assets.index(currency)
        coin_labels = dict(zip(priced_coins["id"], priced_coins["label"]))

        def display_asset_label(asset_id: str) -> str:
            if asset_id in config.CURRENCY_OPTIONS:
                return config.currency_display_label(asset_id, language)
            return coin_labels.get(asset_id, asset_id)

        from_asset = col1.selectbox(
            "Dari:",
            asset_options,
            format_func=display_asset_label,
            key="converter_from_asset",
        )
        to_asset = col2.selectbox(
            "Ke:",
            asset_options,
            index=selected_currency_index,
            format_func=display_asset_label,
            key="converter_to_asset",
        )
        for asset_column, asset_id in ((col1, from_asset), (col2, to_asset)):
            if asset_id in coin_image_by_id:
                asset_row = priced_coins.loc[priced_coins["id"] == asset_id].iloc[0]
                asset_column.markdown(
                    "<div class='selected-assets'>"
                    f"{ui.render_coin_logo(asset_id, asset_row.get('image'), 24, asset_row['symbol_upper'])}"
                    f"<strong>{escape(str(asset_row['label']))}</strong></div>",
                    unsafe_allow_html=True,
                )
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
        current_watchlist = watchlist_ids
        if catalog_df.empty:
            st.info("Katalog koin tidak tersedia; daftar tersimpan tetap dapat dilihat.")
        else:
            catalog_ids = set(catalog_df["id"].astype(str))
            valid_default = [
                cid for cid in current_watchlist if cid in catalog_ids
            ]
            coin_query = st.text_input(
                "Cari aset untuk watchlist",
                placeholder="Ketik nama, simbol, atau ID, misalnya bitcoin, BTC, atau bitcoin",
                help="Pencarian menampilkan maksimal 50 aset sekaligus.",
                key=ui.user_state_key("watchlist_coin_search", str(user.id)),
            )
            available_ids, no_coin_matches = coin_selector_options(
                catalog_df,
                coin_query,
                selected_ids=valid_default,
            )
            if no_coin_matches:
                st.info(
                    "Tidak ada aset yang cocok. Aset populer ditampilkan agar "
                    "Anda tetap dapat memilih."
                )
            coin_labels = dict(zip(catalog_df["id"], catalog_df["label"]))
            selected_ids = st.multiselect(
                "Aset watchlist",
                options=available_ids,
                default=valid_default,
                format_func=lambda coin_id: coin_labels.get(coin_id, coin_id),
                help="Aset yang sudah dipilih tetap dipertahankan saat pencarian berubah.",
                key=ui.user_state_key("watchlist_coin_ids", str(user.id)),
            )
            if set(selected_ids) != set(current_watchlist):
                db.sync_user_watchlist(user.id, current_watchlist, selected_ids)
                st.rerun()

        if current_watchlist:
            wl_df = market_df[market_df["id"].isin(current_watchlist)].copy()
            if not wl_df.empty:
                wl_display_df = pd.DataFrame({
                    "Logo": wl_df["image"],
                    "Nama": wl_df["name"],
                    "Simbol": wl_df["symbol_upper"],
                    "Harga": wl_df["current_price"],
                })
                st.dataframe(
                    ui.style_dataframe(wl_display_df, dark_mode),
                    width="stretch",
                    hide_index=True,
                    column_config={"Logo": st.column_config.ImageColumn("Logo", width="small")},
                )
                st.download_button(
                    "Unduh Watchlist CSV",
                    data=exports.build_csv(
                        [
                            {
                                "coin_id": row["id"],
                                "name": row["name"],
                                "symbol": row["symbol_upper"],
                                "price": row.get("current_price"),
                                "currency": currency,
                            }
                            for _, row in wl_df.iterrows()
                        ],
                        ["coin_id", "name", "symbol", "price", "currency"],
                    ),
                    file_name=f"chainscope-watchlist-{datetime.now():%Y-%m-%d}.csv",
                    mime="text/csv",
                    key="download_watchlist_csv",
                )
            else:
                st.info("Koin tersimpan belum memiliki metadata yang tersedia.")
        else:
            st.info("Belum ada koin di Watchlist.")

elif current_page == "wallet":
    from chainscope.wallet_component import render_personal_wallet

    render_personal_wallet(dark_mode=dark_mode, user_id=user.id)

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