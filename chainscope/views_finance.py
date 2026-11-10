"""View components for Personal Finance (Net Worth, Income, Expense, Budget, Savings, Assets, Reconciliation, Education)."""

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chainscope import (
    personal_finance, reconciliation, education, formatting, ui,
)


def _get_finance_session_state(user_id: str) -> dict:
    key = f"finance_data_{user_id}"
    if key not in st.session_state:
        st.session_state[key] = {
            "incomes": [
                {"date": "2026-11-01", "category": "Gaji Pokok", "amount": 15000000.0, "note": "Gaji Bulanan"},
                {"date": "2026-11-05", "category": "Trading Crypto / Saham", "amount": 2500000.0, "note": "Profit Realized"},
            ],
            "expenses": [
                {"date": "2026-11-02", "category": "Tempat Tinggal & Kos/Sewa", "amount": 3500000.0, "note": "Sewa Apartemen"},
                {"date": "2026-11-03", "category": "Makanan & Minuman", "amount": 2800000.0, "note": "Kebutuhan Pokok"},
                {"date": "2026-11-04", "category": "Transportasi", "amount": 950000.0, "note": "Bensin & Tol"},
                {"date": "2026-11-06", "category": "Utilitas & Tagihan (Listrik, Air, Internet)", "amount": 800000.0, "note": "Listrik & Wi-Fi"},
            ],
            "budgets": [
                {"category": "Makanan & Minuman", "monthly_limit": 3500000.0},
                {"category": "Transportasi", "monthly_limit": 1200000.0},
                {"category": "Belanja & Hiburan", "monthly_limit": 1500000.0},
                {"category": "Tempat Tinggal & Kos/Sewa", "monthly_limit": 4000000.0},
            ],
            "savings_goals": [
                {"name": "Dana Darurat (6 Bulan)", "target_amount": 45000000.0, "current_amount": 25000000.0, "monthly_contribution": 3000000.0},
                {"name": "Uang Muka Rumah", "target_amount": 150000000.0, "current_amount": 40000000.0, "monthly_contribution": 5000000.0},
            ],
            "manual_assets": [
                {"name": "BCA Tabungan Payroll", "type": "Kas / Tabungan Bank", "value_idr": 25000000.0, "symbol": "IDR"},
                {"name": "Bibit Reksadana Obligasi", "type": "Reksa Dana", "value_idr": 40000000.0, "symbol": "IDR"},
                {"name": "Tether USDT (Cold Storage)", "type": "Portofolio Crypto (Manual)", "value_idr": 16000000.0, "symbol": "USDT"},
            ],
            "liabilities": [
                {"name": "Kartu Kredit BCA", "type": "Kartu Kredit", "amount_idr": 3500000.0, "monthly_installment": 3500000.0},
                {"name": "KKB Kredit Mobil", "type": "KKB (Kredit Kendaraan Bermotor)", "amount_idr": 85000000.0, "monthly_installment": 2800000.0},
            ],
        }
    return st.session_state[key]


def render_financial_overview_page(user_id: str, currency: str = "IDR", dark_mode: bool = False) -> None:
    st.markdown("<h1>Ringkasan Keuangan & Kekayaan Bersih (Net Worth)</h1>", unsafe_allow_html=True)
    st.caption("Kelola seluruh aset, utang, pemasukan, pengeluaran, dan arus kas dalam satu neraca terpadu.")

    data = _get_finance_session_state(user_id)
    
    # Calculate totals
    cash_and_bank = sum(a["value_idr"] for a in data["manual_assets"] if "Tabungan" in a["type"] or "Kas" in a["type"])
    investments = sum(a["value_idr"] for a in data["manual_assets"] if "Tabungan" not in a["type"] and "Kas" not in a["type"])
    total_liabilities = sum(l["amount_idr"] for l in data["liabilities"])
    
    nw = personal_finance.calculate_net_worth(
        cash_and_bank=cash_and_bank,
        investments_manual=investments,
        portfolio_crypto_val=0.0,
        connected_wallet_val=0.0,
        other_assets=0.0,
        total_liabilities=total_liabilities,
    )
    cf = personal_finance.calculate_cash_flow(data["incomes"], data["expenses"])

    # Top KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kekayaan Bersih (Net Worth)", f"Rp {nw['net_worth']:,.0f}")
    m2.metric("Total Seluruh Aset", f"Rp {nw['total_assets']:,.0f}")
    m3.metric("Total Kewajiban (Utang)", f"Rp {nw['total_liabilities']:,.0f}")
    m4.metric("Rasio Utang terhadap Aset", f"{nw['debt_to_asset_ratio_pct']:.1f}%")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pemasukan Bulan Ini", f"Rp {cf['total_income']:,.0f}")
    c2.metric("Pengeluaran Bulan Ini", f"Rp {cf['total_expense']:,.0f}")
    c3.metric("Arus Kas Bersih (Net Cash Flow)", f"Rp {cf['net_cash_flow']:,.0f}", f"{cf['savings_rate_pct']:.1f}% Savings Rate")
    c4.metric("Savings Rate", f"{cf['savings_rate_pct']:.1f}%", help="Persentase penghasilan yang berhasil ditabung/diinvestasikan.")

    # Charts
    st.markdown("### Komposisi Neraca Keuangan")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        df_assets = pd.DataFrame(data["manual_assets"])
        if not df_assets.empty:
            fig1 = px.pie(df_assets, values="value_idr", names="name", title="Alokasi Portofolio Aset", hole=0.45)
            ui.apply_plotly_theme(fig1, dark_mode)
            st.plotly_chart(fig1, width="stretch")
    with col_chart2:
        df_exp = pd.DataFrame(data["expenses"])
        if not df_exp.empty:
            fig2 = px.pie(df_exp, values="amount", names="category", title="Rincian Pengeluaran Berdasarkan Kategori", hole=0.45)
            ui.apply_plotly_theme(fig2, dark_mode)
            st.plotly_chart(fig2, width="stretch")


def render_income_expense_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Pemasukan & Pengeluaran</h1>", unsafe_allow_html=True)
    st.caption("Catat arus kas harian dan tinjau riwayat transaksi Anda.")

    data = _get_finance_session_state(user_id)

    with st.expander("➕ Tambah Catatan Transaksi Baru", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            tx_type = st.radio("Tipe Transaksi:", ["Pengeluaran", "Pemasukan"], horizontal=True)
        with c2:
            cats = personal_finance.EXPENSE_CATEGORIES if tx_type == "Pengeluaran" else personal_finance.INCOME_CATEGORIES
            cat = st.selectbox("Kategori:", cats)
        with c3:
            amount = st.number_input("Nominal (IDR):", min_value=1000.0, step=50000.0, value=100000.0)
        
        n1, n2 = st.columns([2, 1])
        with n1:
            note = st.text_input("Keterangan:", placeholder="Contoh: Makan siang, Gaji bulanan")
        with n2:
            tx_date = st.date_input("Tanggal Transaksi:", value=datetime.now().date())

        if st.button("Simpan Transaksi", type="primary"):
            entry = {"date": str(tx_date), "category": cat, "amount": float(amount), "note": note}
            if tx_type == "Pemasukan":
                data["incomes"].append(entry)
            else:
                data["expenses"].append(entry)
            st.success("Transaksi berhasil dicatat!")
            st.rerun()

    # Tables
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("### Riwayat Pemasukan")
        df_in = pd.DataFrame(data["incomes"])
        if not df_in.empty:
            st.dataframe(ui.style_dataframe(df_in, dark_mode), width="stretch", hide_index=True)
        else:
            st.info("Belum ada catatan pemasukan.")
            
    with col_t2:
        st.markdown("### Riwayat Pengeluaran")
        df_out = pd.DataFrame(data["expenses"])
        if not df_out.empty:
            st.dataframe(ui.style_dataframe(df_out, dark_mode), width="stretch", hide_index=True)
        else:
            st.info("Belum ada catatan pengeluaran.")


def render_budget_management_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Manajemen Anggaran (Budgeting)</h1>", unsafe_allow_html=True)
    st.caption("Tetapkan batas pengeluaran bulanan per kategori dan pantau peringatan utilisasi anggaran.")

    data = _get_finance_session_state(user_id)
    budgets = data["budgets"]
    expenses = data["expenses"]

    util_list = personal_finance.evaluate_budget_utilization(expenses, budgets)
    
    st.markdown("### Status Utilisasi Anggaran Bulan Ini")
    for b in util_list:
        pct = b["utilization_pct"]
        bar_val = min(1.0, pct / 100.0)
        color = "🟢" if pct < 80 else "🟡" if pct < 100 else "🔴"
        
        st.write(f"**{color} {b['category']}** — Terpakai: Rp {b['spent']:,.0f} / Batas: Rp {b['monthly_limit']:,.0f} ({pct:.1f}%) · Sisa: Rp {b['remaining']:,.0f}")
        st.progress(bar_val)


def render_savings_goals_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Target Tabungan (Savings Goals)</h1>", unsafe_allow_html=True)
    st.caption("Rencanakan dana darurat, pembelian aset, dan target finansial masa depan.")

    data = _get_finance_session_state(user_id)
    goals = data["savings_goals"]

    for g in goals:
        progress = personal_finance.track_savings_goal_progress(g, g.get("current_amount", 0.0))
        st.markdown(f"### {progress['name']}")
        st.write(f"Terkumpul: **Rp {progress['current_amount']:,.0f}** dari target **Rp {progress['target_amount']:,.0f}** ({progress['progress_pct']:.1f}%)")
        st.progress(min(1.0, progress["progress_pct"] / 100.0))
        if progress["months_to_target"]:
            st.caption(f"Estimasi selesai dalam **{progress['months_to_target']} bulan** dengan setoran Rp {g['monthly_contribution']:,.0f}/bulan.")
        st.markdown("---")


def render_assets_liabilities_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Daftar Aset & Kewajiban (Utang)</h1>", unsafe_allow_html=True)
    st.caption("Pencatatan aset riil, tabungan perbankan, portofolio manual, dan kewajiban cicilan.")

    data = _get_finance_session_state(user_id)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Daftar Aset")
        st.dataframe(ui.style_dataframe(pd.DataFrame(data["manual_assets"]), dark_mode), width="stretch", hide_index=True)
    with col2:
        st.markdown("### Daftar Kewajiban & Utang")
        st.dataframe(ui.style_dataframe(pd.DataFrame(data["liabilities"]), dark_mode), width="stretch", hide_index=True)


def render_portfolio_reconciliation_page(user_id: str, dark_mode: bool = False) -> None:
    st.markdown("<h1>Rekonsiliasi Portofolio & Pencegahan Duplikasi</h1>", unsafe_allow_html=True)
    st.caption("Memastikan aset yang terhubung di Web3 wallet atau jurnal tidak terhitung ganda dalam Kekayaan Bersih.")

    data = _get_finance_session_state(user_id)
    manual_assets = data["manual_assets"]
    
    # Mock connected wallet tokens
    wallet_tokens = [
        {"symbol": "USDT", "balance": 1000.0, "value_usd": 1000.0, "network": "Polygon PoS"}
    ]
    
    rec = reconciliation.reconcile_assets(manual_assets, [], wallet_tokens)
    
    if rec["has_duplicates"]:
        st.warning(f"Terdeteksi {rec['duplicate_count']} potensi duplikasi aset! Nilai yang dideduplikasi: ${rec['total_deducted_overlap_usd']:,.2f}")
        for o in rec["overlaps"]:
            st.info(f"**{o['asset_name']} ({o['symbol']})**: {o['reason']} ({o['source_a']} vs {o['source_b']}).")
    else:
        st.success("Semua aset terdata unik! Tidak ada tumpang tindih antara wallet Web3 dan aset manual.")


def render_financial_education_page(dark_mode: bool = False) -> None:
    st.markdown("<h1>Pusat Edukasi Keuangan & Investasi</h1>", unsafe_allow_html=True)
    st.caption("Panduan ramah pemula untuk memahami konsep keuangan pribadi, pengelolaan risiko, dan arus kas.")

    topics = education.get_all_educational_topics()
    for t in topics:
        with st.expander(f"📚 {t['title']}", expanded=True if t["id"] == "net_worth" else False):
            st.markdown(f"**Ringkasan:** {t['summary']}")
            st.write(t["explanation"])
            st.info(f"**Rumus:** `{t['formula']}`")
            st.success(f"💡 **Tips Aksi:** {t['action_tip']}")
