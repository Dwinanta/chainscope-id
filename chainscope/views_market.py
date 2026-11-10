"""View components for Market Intelligence (Stocks, Forex, Multi-Exchange, Fundamentals, Backtesting Lab)."""

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chainscope import (
    stocks, forex, fundamentals, exchanges, backtesting,
    indicators, formatting, ui, config,
)


def render_stock_market_page(currency: str = "USD", dark_mode: bool = False) -> None:
    st.markdown("<h1>Pasar Saham (IHSG & Global Equities)</h1>", unsafe_allow_html=True)
    st.caption("Pantau harga pasar saham Indonesia (BEI/IDX) dan bursa internasional secara real-time.")

    universe = stocks.get_stock_universe()
    options_map = {f"{s['symbol']} - {s['name']} ({s['sector']})": s["symbol"] for s in universe}
    
    col_sel, col_period = st.columns([2.5, 1])
    with col_sel:
        selected_label = st.selectbox("Pilih Saham:", list(options_map.keys()), index=0)
        selected_sym = options_map[selected_label]
    with col_period:
        selected_period = st.selectbox("Rentang Riwayat:", ["5d", "1mo", "6mo", "1y", "5y"], index=1)

    quote = stocks.fetch_stock_quote(selected_sym)
    
    # Summary Metrics
    m1, m2, m3, m4 = st.columns(4)
    price_curr = quote.get("currency", "IDR")
    m1.metric("Harga Terakhir", formatting.format_money(quote["price"], price_curr), f"{quote['change_pct']:+.2f}%")
    m2.metric("Penutupan Sebelumnya", formatting.format_money(quote["previous_close"], price_curr))
    m3.metric("Perubahan Nominal", formatting.format_money(quote["change"], price_curr))
    m4.metric("Bursa / Status", f"{quote['exchange']} · {quote['status']}")

    # Interactive Chart
    df_hist = stocks.fetch_stock_history(selected_sym, period=selected_period)
    if not df_hist.empty:
        fig = go.Figure(data=[
            go.Candlestick(
                x=df_hist["timestamp"],
                open=df_hist["open"],
                high=df_hist["high"],
                low=df_hist["low"],
                close=df_hist["close"],
                name=selected_sym,
            )
        ])
        fig.update_layout(
            title=f"Grafik Harga {selected_sym} ({selected_period})",
            xaxis_rangeslider_visible=False,
            height=450,
        )
        ui.apply_plotly_theme(fig, dark_mode)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Riwayat grafik saham belum tersedia untuk periode yang dipilih.")

    # Sector Comparison Table
    st.markdown("### Perbandingan Saham Unggulan")
    df_sector = fundamentals.get_sector_comparison_table()
    st.dataframe(ui.style_dataframe(df_sector, dark_mode), width="stretch", hide_index=True)


def render_forex_market_page(dark_mode: bool = False) -> None:
    st.markdown("<h1>Pasar Forex & Kekuatan Mata Uang</h1>", unsafe_allow_html=True)
    st.caption("Pantau kurs valuta asing utama dunia, pergerakan USD/IDR, dan currency strength meter.")

    pairs = forex.get_forex_pairs()
    pair_labels = {f"{p['pair']} ({p['name']})": p["symbol"] for p in pairs}
    
    col_p, col_r = st.columns([2.5, 1])
    with col_p:
        sel_label = st.selectbox("Pilih Pasangan Mata Uang:", list(pair_labels.keys()), index=0)
        sel_sym = pair_labels[sel_label]
    with col_r:
        sel_range = st.selectbox("Rentang Waktu:", ["5d", "1mo", "3mo", "1y"], index=1, key="forex_range")

    q = forex.fetch_forex_quote(sel_sym)
    
    m1, m2, m3 = st.columns(3)
    m1.metric(q["pair"], f"{q['rate']:,.2f}", f"{q['change_pct']:+.2f}%")
    m2.metric("Penutupan Kemarin", f"{q['previous_close']:,.2f}")
    m3.metric("Status Data", q["status"])

    df_hist = forex.fetch_forex_history(sel_sym, period=sel_range)
    if not df_hist.empty:
        fig = px.line(df_hist, x="timestamp", y="price", title=f"Riwayat Kurs {q['pair']}")
        ui.apply_plotly_theme(fig, dark_mode)
        st.plotly_chart(fig, width="stretch")

    # Currency Strength Meter
    st.markdown("### Currency Strength Meter (Indeks Kekuatan Relatif)")
    df_strength = forex.calculate_currency_strength()
    st.dataframe(ui.style_dataframe(df_strength, dark_mode), width="stretch", hide_index=True)


def render_multi_exchange_page(dark_mode: bool = False) -> None:
    st.markdown("<h1>Analisis Multi-Bursa & Arbitrase Harga</h1>", unsafe_allow_html=True)
    st.caption("Bandingkan harga dan volume aset crypto di berbagai bursa global dan lokal (Indodax, Binance, Bybit, OKX, Coinbase).")

    coins = [("bitcoin", "Bitcoin (BTC)"), ("ethereum", "Ethereum (ETH)"), ("solana", "Solana (SOL)")]
    coin_id = st.selectbox("Pilih Aset:", options=[c[0] for c in coins], format_func=lambda cid: next(c[1] for c in coins if c[0] == cid))

    df_tickers = exchanges.fetch_cross_exchange_tickers(coin_id)
    arb = exchanges.calculate_arbitrage_opportunities(df_tickers)

    if arb["has_arbitrage"]:
        st.success(f"Peluang Arbitrase Terdeteksi! Gross Spread: {arb['spread_pct']:.2f}% (${arb['spread_usd']:,.2f})")
        st.info(arb["potential_profit_note"])
    else:
        st.info("Selisih harga antar bursa saat ini efisien (< 0.5%). Tidak ditemukan anomali harga signifikan.")

    st.markdown("### Daftar Harga Antar Bursa")
    if not df_tickers.empty:
        st.dataframe(ui.style_dataframe(df_tickers, dark_mode), width="stretch", hide_index=True)
    else:
        st.warning("Data bursa eksternal sedang dalam pembaruan.")


def render_fundamental_analysis_page(dark_mode: bool = False) -> None:
    st.markdown("<h1>Analisis Fundamental Saham</h1>", unsafe_allow_html=True)
    st.caption("Evaluasi valuasi rasio keuangan (P/E, P/B, EPS, ROE, Dividend Yield, dan Debt-to-Equity).")

    symbols = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK", "AAPL", "MSFT", "NVDA"]
    selected = st.selectbox("Pilih Emiten / Perusahaan:", symbols, index=0)

    fdata = fundamentals.get_stock_fundamentals(selected)
    
    col_v, col_d = st.columns([1, 2])
    with col_v:
        st.markdown(f"### {fdata['name']}")
        st.markdown(f"**Sektor:** {fdata['sector']}")
        st.markdown(f"**Status Valuasi:** `{fdata['valuation_grade']}`")
    with col_d:
        st.caption(fdata.get("description", ""))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("P/E Ratio", f"{fdata['pe_ratio']:.1f}x")
    m2.metric("P/B Ratio", f"{fdata['pbv_ratio']:.2f}x")
    m3.metric("ROE (%)", f"{fdata['roe_pct']:.1f}%")
    m4.metric("Dividend Yield", f"{fdata['dividend_yield_pct']:.2f}%")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Net Margin", f"{fdata['net_profit_margin_pct']:.1f}%")
    d2.metric("Debt-to-Equity", f"{fdata['debt_to_equity']:.2f}x")
    d3.metric("ROA (%)", f"{fdata['roa_pct']:.1f}%")
    d4.metric("EPS", f"{fdata['eps_idr']:,.1f}")


def render_hedge_fund_lab_page(market_data: pd.DataFrame, dark_mode: bool = False) -> None:
    st.markdown("<h1>Hedge Fund Strategy Lab (Backtesting)</h1>", unsafe_allow_html=True)
    st.caption("Simulasikan strategi kuantitatif secara historis tanpa lookahead bias dan bandingkan dengan benchmark Buy & Hold.")

    c1, c2, c3 = st.columns(3)
    with c1:
        strategy = st.selectbox("Pilih Strategi Algoritmik:", [
            ("sma_cross", "SMA Trend Following (Golden/Death Cross)"),
            ("rsi_mean_reversion", "RSI Mean Reversion (Oversold/Overbought)"),
            ("momentum_breakout", "Momentum 20-Bar Channel Breakout"),
        ], format_func=lambda x: x[1])[0]
    with c2:
        capital = st.number_input("Modal Awal (USD):", min_value=100.0, value=10000.0, step=1000.0)
    with c3:
        fee_pct = st.number_input("Biaya Transaksi / Slippage per Trade (%):", min_value=0.0, value=0.1, step=0.05)

    # Use Bitcoin or available price history
    from chainscope import api
    try:
        hist_df = api.fetch_price_history("bitcoin", "usd", days=180)
    except Exception:
        hist_df = pd.DataFrame()

    if hist_df.empty or len(hist_df) < 40:
        st.warning("Memerlukan minimal 40 data historis untuk menjalankan simulasi.")
        return

    result = backtesting.run_backtest(hist_df, strategy=strategy, initial_capital=capital, fee_pct=fee_pct)

    # Performance Overview Cards
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Hasil Strategi", f"${result['final_equity']:,.2f}", f"{result['total_return_pct']:+.1f}%")
    r2.metric("Benchmark Buy & Hold", f"${capital * (1 + result['benchmark_return_pct']/100):,.2f}", f"{result['benchmark_return_pct']:+.1f}%")
    r3.metric("Alpha (Kelebihan Return)", f"{result['alpha_pct']:+.1f}%")
    r4.metric("Max Drawdown", f"-{result['max_drawdown_pct']:.1f}%")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
    k2.metric("Sortino Ratio", f"{result['sortino_ratio']:.2f}")
    k3.metric("Win Rate (%)", f"{result['win_rate_pct']:.1f}%")
    k4.metric("Profit Factor", f"{result['profit_factor']:.2f}")

    # Plot Equity Curves
    eq_df = result["equity_curve"].copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq_df.index, y=eq_df["strategy_equity"], mode="lines", name="Strategi Lab", line=dict(color="#10B981", width=2.5)))
    fig.add_trace(go.Scatter(x=eq_df.index, y=eq_df["benchmark_equity"], mode="lines", name="Benchmark (Buy & Hold)", line=dict(color="#3B82F6", dash="dot")))
    fig.update_layout(title="Kurva Pertumbuhan Ekuitas (Equity Curve)", height=420)
    ui.apply_plotly_theme(fig, dark_mode)
    st.plotly_chart(fig, width="stretch")
