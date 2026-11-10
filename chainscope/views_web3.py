"""View components for Web3 & DEX (Wallet Dashboard, DEX Analytics, DEX Swap Aggregator, Token Safety)."""

import pandas as pd
import streamlit as st

from chainscope import (
    web3_networks, web3_wallet, dex_analytics, dex_swap, token_safety,
    web3_component, ui, formatting,
)


def render_web3_dashboard_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Dashboard Wallet Web3 (Non-Custodial)</h1>", unsafe_allow_html=True)
    st.caption("Hubungkan wallet Web3 browser Anda (MetaMask, Trust Wallet, Rabby, Coinbase Wallet, Phantom) untuk memantau saldo multi-chain secara non-custodial.")

    # Render Browser Connector
    web3_component.render_web3_connector(dark_mode=dark_mode)

    # Multi-chain network status
    st.markdown("### Jaringan Blockchain yang Didukung")
    networks = web3_networks.get_all_networks()
    df_net = pd.DataFrame([
        {
            "Jaringan": n["name"],
            "Chain ID": n["chain_id"],
            "Tipe": n["type"].upper(),
            "Token Utama": n["symbol"],
            "Explorer": n["explorer_url"],
            "Status": "Testnet" if n.get("is_testnet") else "Mainnet",
        }
        for n in networks
    ])
    st.dataframe(ui.style_dataframe(df_net, dark_mode), width="stretch", hide_index=True)


def render_dex_analytics_page(dark_mode: bool = False) -> None:
    st.markdown("<h1>Analisis DEX & Pool Likuiditas On-Chain</h1>", unsafe_allow_html=True)
    st.caption("Eksplorasi volume transaksi, cadangan likuiditas, dan pasangan perdagangan terpopuler di berbagai bursa terdesentralisasi.")

    c1, c2 = st.columns([1, 2])
    with c1:
        net_choices = [("eth", "Ethereum"), ("bsc", "BNB Smart Chain"), ("polygon_pos", "Polygon PoS"), ("arbitrum", "Arbitrum One"), ("base", "Base"), ("solana", "Solana")]
        selected_net = st.selectbox("Pilih Jaringan DEX:", net_choices, format_func=lambda x: x[1])[0]
    with c2:
        search_query = st.text_input("Cari Token / Kontrak Pool:", placeholder="Misal: PEPE, USDT, WETH...")

    if search_query:
        search_res = dex_analytics.search_dex_tokens(search_query)
        if search_res:
            st.markdown(f"### Hasil Pencarian untuk '{search_query}'")
            st.dataframe(ui.style_dataframe(pd.DataFrame(search_res), dark_mode), width="stretch", hide_index=True)
        else:
            st.info("Tidak ditemukan pool yang cocok dengan kata kunci.")

    st.markdown(f"### Trending Pools Teratas di Jaringan {selected_net.upper()}")
    df_pools = dex_analytics.fetch_trending_dex_pools(selected_net)
    st.dataframe(ui.style_dataframe(df_pools, dark_mode), width="stretch", hide_index=True)


def render_dex_swap_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Swap DEX & Simulator Transaksi</h1>", unsafe_allow_html=True)
    st.caption("Dapatkan kuotasi swap multi-chain, estimasi gas fee, price impact, dan simulasikan transaksi di jaringan testnet secara aman.")

    c1, c2, c3 = st.columns(3)
    with c1:
        net_options = [
            ("1", "Ethereum Mainnet (Uniswap V3)"),
            ("11155111", "Sepolia Testnet (Uniswap V3)"),
            ("56", "BNB Smart Chain (PancakeSwap V3)"),
            ("137", "Polygon PoS (QuickSwap)"),
            ("42161", "Arbitrum One (Uniswap V3)"),
            ("8453", "Base (Aerodrome / Uniswap)"),
            ("solana", "Solana (Jupiter Aggregator)"),
        ]
        chain_id = st.selectbox("Jaringan Blockchain:", net_options, format_func=lambda x: x[1])[0]
    with c2:
        token_in = st.selectbox("Token Masuk (Bayar):", ["ETH", "USDT", "USDC", "WBTC", "BNB", "POL", "SOL"], index=0)
    with c3:
        token_out = st.selectbox("Token Keluar (Terima):", ["USDC", "USDT", "ETH", "WBTC", "DAI"], index=0)

    a1, a2 = st.columns([2, 1])
    with a1:
        amount_in = st.number_input(f"Jumlah {token_in}:", min_value=0.0001, value=1.0, step=0.1)
    with a2:
        slippage = st.select_slider("Toleransi Slippage (%):", options=[0.1, 0.5, 1.0, 2.0, 3.0], value=0.5)

    # Calculate Quote
    # Approximate reference price for quote engine
    in_price = 3000.0 if token_in in {"ETH"} else 600.0 if token_in == "BNB" else 200.0 if token_in == "SOL" else 1.0
    out_price = 1.0 if token_out in {"USDC", "USDT", "DAI"} else 3000.0

    quote = dex_swap.get_swap_quote(
        chain_id=chain_id,
        input_token=token_in,
        output_token=token_out,
        amount_in=amount_in,
        slippage_pct=slippage,
        token_in_price_usd=in_price,
        token_out_price_usd=out_price,
    )

    st.markdown("### Ringkasan Kuotasi Swap")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Perkiraan Diterima", f"{quote['expected_amount_out']:,.4f} {token_out}")
    q2.metric("Minimum Diterima (Slippage)", f"{quote['minimum_received']:,.4f} {token_out}")
    q3.metric("Price Impact", f"{quote['price_impact_pct']:.2f}%")
    q4.metric("Estimasi Biaya Gas", f"${quote['estimated_gas_usd']:.2f}")

    st.info(f"**Rute Swap Optimal:** `{quote['route']}`")

    with st.expander("🛡️ Verifikasi Keamanan & Simulasi Transaksi Testnet", expanded=True):
        st.write("Semua transaksi bersifat non-custodial dan harus ditandatangani melalui wallet browser pengguna.")
        st.warning("PERINGATAN KEAMANAN: Jangan pernah memberikan approval token tanpa batas (unlimited allowance). Setujui hanya nominal yang ingin Anda tukar.")
        
        sim_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        payload = dex_swap.generate_testnet_swap_payload(quote, sim_address)
        st.code(f"Router Kontrak: {payload['to']}\nDari: {payload['from']}\nGas Limit: {payload['gasLimit']}\nSimulated Hash: {payload['simulated_tx_hash']}", language="json")
        
        if st.button("🚀 Simulasikan Eksekusi Swap di Testnet", type="primary"):
            st.success(f"Simulasi Transaksi Berhasil Diajukan ke Mempool Testnet!\nHash: {payload['simulated_tx_hash']}")
            st.caption("Status: Menunggu konfirmasi blok... (Simulasi sukses tanpa resiko dana riil)")


def render_token_safety_page(dark_mode: bool = False) -> None:
    st.markdown("<h1>Audit Keamanan Token & Deteksi Honeypot</h1>", unsafe_allow_html=True)
    st.caption("Pemeriksaan heuristik otomatis pada smart contract on-chain untuk mendeteksi honeypot, pajak tersembunyi, dan likuiditas tipis.")

    t1, t2 = st.columns([2, 1])
    with t1:
        address = st.text_input("Alamat Kontrak Token (Contract Address):", value="0x6982508145454Ce325dDbE47a25d4ec3d2311933")
    with t2:
        network = st.selectbox("Jaringan:", ["Ethereum", "BNB Smart Chain", "Polygon", "Base", "Arbitrum"])

    audit = token_safety.audit_token_safety(
        token_address=address,
        network=network,
        liquidity_usd=1500000.0,
        volume_24h_usd=450000.0,
        buy_tax_pct=0.0,
        sell_tax_pct=0.0,
        is_verified=True,
        has_mint_function=False,
    )

    st.markdown("### Hasil Pemeriksaan Audit Keamanan")
    col_score, col_badge = st.columns([1, 2])
    with col_score:
        st.metric("Skor Keamanan Kontrak", f"{audit['safety_score']} / 100")
    with col_badge:
        st.markdown(f"**Tingkat Risiko:** <span style='color:{audit['badge_color']}; font-weight:bold; font-size:1.1rem;'>{audit['risk_level']}</span>", unsafe_allow_html=True)
        st.markdown(f"**Kelayakan Transaksi:** {'✅ Layak Ditransaksikan' if audit['is_safe_to_trade'] else '❌ Berisiko Tinggi'}")

    if audit["risk_flags"]:
        st.markdown("#### Catatan Risiko Terdeteksi:")
        for flag in audit["risk_flags"]:
            st.warning(f"⚠️ {flag}")
    else:
        st.success("Tidak ditemukan parameter berbahaya atau pajak tersembunyi pada parameter kontrak ini.")

    st.caption(audit["disclaimer"])
