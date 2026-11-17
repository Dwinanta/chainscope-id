"""Institutional Landing Page, SEO Headers, AI Research Team, and Global Footer for ChainScope ID."""

from datetime import datetime
from html import escape
import json
import streamlit as st

from chainscope import ui, config


def render_seo_headers(is_authenticated: bool = False) -> None:
    """Inject semantic metadata, Open Graph tags, Twitter cards, and Schema.org structured data."""
    if is_authenticated:
        # Strict user privacy: Never allow search engine crawlers to index authenticated dashboard data
        st.markdown(
            """
            <head>
              <meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
            </head>
            """,
            unsafe_allow_html=True,
        )
        return

    # Public landing page technical SEO metadata
    schema_org_json = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "SoftwareApplication",
                "name": "ChainScope ID",
                "applicationCategory": "FinanceApplication",
                "operatingSystem": "All Web Browsers",
                "description": "Platform intelijen keuangan, terminal charting kuantitatif, analisis pasar crypto, saham BEI & US, forex, dan manajemen portofolio FIFO.",
                "url": "https://chainscope.id",
                "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "IDR",
                },
            },
            {
                "@type": "Organization",
                "name": "ChainScope ID",
                "url": "https://chainscope.id",
                "logo": "https://chainscope.id/logo.png",
                "parentOrganization": {
                    "@type": "Organization",
                    "name": "Dwinanta Capital",
                },
            },
            {
                "@type": "WebSite",
                "name": "ChainScope ID",
                "url": "https://chainscope.id",
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "Apa itu ChainScope ID?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "ChainScope ID adalah platform intelijen finansial terpadu yang menyajikan analitik multi-pasar (crypto, saham, forex), terminal charting profesional, jurnal transaksi FIFO, dan manajemen risiko non-custodial.",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Apakah ChainScope ID menyimpan private key wallet saya?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Tidak. ChainScope ID beroperasi dengan prinsip 100% non-custodial. Private key dan seed phrase tidak pernah dikirim atau disimpan di server kami.",
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Apakah tersedia paket gratis di ChainScope ID?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Ya, ChainScope ID menyediakan akun gratis dengan akses pemantauan pasar, charting teknikal, jurnal transaksi, dan konverter mata uang.",
                        },
                    },
                ],
            },
        ],
    })

    seo_html = f"""
    <head>
      <title>ChainScope ID | Platform Intelijen Keuangan & Analisis Pasar</title>
      <meta name="description" content="Platform intelijen pasar terpadu: pantau crypto, saham BEI & US, forex, terminal charting kuantitatif, jurnal trading FIFO, dan manajemen risiko non-custodial.">
      <meta name="keywords" content="crypto indonesia, saham idx, analisa forex, trading journal, charting kuantitatif, portfolio fifo, chainscope">
      <meta name="robots" content="index, follow">
      <link rel="canonical" href="https://chainscope.id">
      
      <!-- Open Graph / Facebook / LinkedIn -->
      <meta property="og:type" content="website">
      <meta property="og:site_name" content="ChainScope ID">
      <meta property="og:url" content="https://chainscope.id">
      <meta property="og:title" content="ChainScope ID | Institutional Financial Intelligence">
      <meta property="og:description" content="Platform analitik multi-pasar terpadu, terminal charting teknikal, dan evaluasi portofolio FIFO non-custodial.">
      <meta property="og:locale" content="id_ID">
      
      <!-- Twitter Cards -->
      <meta name="twitter:card" content="summary_large_image">
      <meta name="twitter:title" content="ChainScope ID | Institutional Financial Intelligence">
      <meta name="twitter:description" content="Platform analitik multi-pasar terpadu, terminal charting teknikal, dan evaluasi portofolio FIFO.">
      
      <!-- JSON-LD Structured Data -->
      <script type="application/ld+json">
      {schema_org_json}
      </script>
    </head>
    """
    st.markdown(seo_html, unsafe_allow_html=True)


def render_institutional_landing_page(dark_mode: bool = False) -> None:
    """Render high-fidelity institutional landing page with AI Team and Verified Ecosystem."""
    render_seo_headers(is_authenticated=False)

    # 1. HERO SECTION
    st.markdown(
        """
        <div class="landing-shell">
            <div class="landing-hero-panel">
                <span class="landing-eyebrow">
                    <span class="auth-brand-mark">C</span> ChainScope ID · Institutional Financial Intelligence
                </span>
                <div class="landing-hero">
                    <h1>Kenali Pasar. Kuasai Analisis. Kelola Investasi Anda.</h1>
                    <p>
                        Platform intelijen pasar terpadu yang menyatukan data crypto, saham BEI/IDX & pasar global, forex,
                        terminal charting teknikal profesional, jurnal transaksi FIFO otomatis, evaluasi risiko, dan Web3 non-custodial.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ACTION BUTTONS
    c_btn1, c_btn2, _ = st.columns([1.2, 1.2, 2.6], gap="small")
    with c_btn1:
        if st.button("Mulai Gratis Sekarang", type="primary", width="stretch", key="landing_get_started"):
            st.session_state.show_landing = False
            st.rerun()
    with c_btn2:
        if st.button("Masuk ke Akun", width="stretch", key="landing_sign_in"):
            st.session_state.show_landing = False
            st.rerun()

    # HIGHLIGHT PILLS
    st.markdown(
        """
        <div style="display:flex; flex-wrap:wrap; gap:10px; margin: 1.5rem 0 2rem;">
            <span style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; font-size:0.8rem; font-weight:600; background:var(--cs-card-surface); border:1px solid var(--cs-card-border);">
                🔒 100% Non-Custodial
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; font-size:0.8rem; font-weight:600; background:var(--cs-card-surface); border:1px solid var(--cs-card-border);">
                📊 Analisis Multi-Pasar (Crypto, Saham, Forex)
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; font-size:0.8rem; font-weight:600; background:var(--cs-card-surface); border:1px solid var(--cs-card-border);">
                📈 Jurnal & Evaluasi Portofolio FIFO
            </span>
            <span style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:20px; font-size:0.8rem; font-weight:600; background:var(--cs-card-surface); border:1px solid var(--cs-card-border);">
                🛡️ Audit Kontrak Pintar On-Chain
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. CAPABILITIES GRID
    st.markdown(
        """
        <div class="landing-section-title">Kapabilitas Platform Finansial Terpadu</div>
        <p style="color:var(--cs-secondary-text); margin-top:0; font-size:0.95rem;">
            Dirancang dari dasar dengan standar institusional untuk kebutuhan trader aktif dan investor jangka panjang.
        </p>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    capabilities = [
        ("Multi-Market Intelligence", "Pantau harga real-time crypto CoinGecko & Indodax, saham BEI & bursa AS, kurs valuta asing utama, serta anomali arbitrase antar-bursa global."),
        ("Terminal Charting Profesional", "Grafik candlestick, line, dan area dengan multiple timeframes (1m-1d), indikator teknikal komprehensif, multi-panel, dan zoom interaktif."),
        ("Jurnal Trading & Evaluasi FIFO", "Catat transaksi dengan tag strategi. Sistem menghitung posisi terbuka, alokasi modal, dan P/L terealisasi secara akurat dengan ekspor CSV aman formula."),
        ("Performance Coach & Analisis Sesi", "Tinjau win rate, profit factor, average win/loss, dan distribusi hasil berdasarkan sesi perdagangan UTC tanpa bias retrospektif."),
        ("Risk Management Center", "Kalkulator ukuran posisi (position sizing), simulasi stop-loss & risk-to-reward ratio, matriks korelasi aset, serta estimasi volatilitas historis."),
        ("Web3 Non-Custodial & Swap Aggregator", "Koneksi wallet browser (MetaMask, Phantom) multi-chain, agregator rute swap DEX optimal, dan audit keamanan smart contract dari jebakan honeypot."),
    ]
    cols = [col1, col2, col3, col1, col2, col3]
    for c, (title, desc) in zip(cols, capabilities):
        with c:
            st.markdown(
                f"""
                <div class="landing-card" style="margin-bottom:1rem;">
                    <h3>{escape(title)}</h3>
                    <p>{escape(desc)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 3. AI RESEARCH & ANALYTICS TEAM SECTION
    st.markdown(
        """
        <div class="landing-section-title">AI Research & Analytics Ecosystem</div>
        <p style="color:var(--cs-secondary-text); margin-top:0; font-size:0.95rem;">
            Tujuh peran kecerdasan buatan komputasional yang dirancang untuk mendukung riset dan analisis keputusan Anda.
        </p>
        <div style="background:var(--cs-card-surface); border:1px solid var(--cs-card-border); border-left:4px solid var(--cs-accent); padding:10px 16px; border-radius:10px; margin-bottom:1.5rem; font-size:0.83rem; color:var(--cs-secondary-text);">
            ℹ️ <strong>Transparansi AI:</strong> Semua peran di bawah ini adalah asisten analisis data komputasional (AI Agents), bukan penasihat keuangan berlisensi atau staf manusia. Tidak melakukan eksekusi perdagangan otomatis.
        </div>
        """,
        unsafe_allow_html=True,
    )

    ai_roles = [
        ("AI Market Research Analyst", "Analisis Regime Pasar & Makro", "Memonitor sentimen pasar global, Fear & Greed index, siklus likuiditas makro, dan narasi sektor yang sedang bertumbuh."),
        ("AI Technical Analyst", "Price Action & Struktur Indikator", "Mendeteksi level support & resistance kunci, zona order block institusional, deviasi momentum RSI, dan golden/death cross MA."),
        ("AI Fundamental Analyst", "Valuasi Saham & Tokenomics", "Mengevaluasi rasio keuangan (P/E, P/B, ROE, Debt-to-Equity), inflasi sirkulasi token crypto, dan dinamika jadwal vesting."),
        ("AI Risk Analyst", "Kalkulasi Risiko & Stress-Testing", "Menghitung Value at Risk (VaR), simulasi skenario drawdown maksimum, dan kalkulasi batas risiko modal per trade sebelum eksekusi."),
        ("AI Portfolio Analyst", "Evaluasi Kinerja FIFO & Alokasi", "Meninjau efisiensi portofolio berdasarkan catatan jurnal, konsentrasi aset, profit factor strategi, dan rasio Sharpe estimasi."),
        ("AI Financial Assistant", "Neraca Finansial & Arus Kas", "Membantu pelacakan kekayaan bersih (Net Worth), rekonsiliasi aset agar tidak terhitung ganda, dan peringatan batas anggaran bulanan."),
        ("AI Research Coordinator", "Sintesis Riset Terpadu", "Mengkonsolidasikan temuan teknikal, fundamental, dan risiko ke dalam format ringkasan eksekutif yang mudah dipahami."),
    ]

    r_cols = st.columns(2)
    for i, (name, role, desc) in enumerate(ai_roles):
        with r_cols[i % 2]:
            st.markdown(
                f"""
                <div class="landing-card" style="margin-bottom:1rem; border-left: 3px solid var(--cs-accent);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:700; color:var(--cs-primary-text); font-size:0.95rem;">🤖 {escape(name)}</span>
                        <span style="font-size:0.75rem; color:var(--cs-accent); font-weight:600;">AI Specialist</span>
                    </div>
                    <div style="font-size:0.8rem; font-weight:600; color:var(--cs-secondary-text); margin-bottom:6px;">{escape(role)}</div>
                    <p style="font-size:0.85rem; line-height:1.5;">{escape(desc)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. POWERED BY OUR ECOSYSTEM
    st.markdown(
        """
        <div class="landing-section-title">POWERED BY OUR ECOSYSTEM</div>
        <p style="color:var(--cs-secondary-text); margin-top:0; font-size:0.95rem;">
            Sinergi inovasi teknologi finansial dan portofolio strategis di bawah ekosistem verified.
        </p>
        """,
        unsafe_allow_html=True,
    )

    eco_col1, eco_col2, eco_col3 = st.columns(3)
    with eco_col1:
        st.markdown(
            """
            <div class="landing-card" style="height:100%; border-top: 3px solid var(--cs-accent);">
                <div style="font-size:1.15rem; font-weight:800; color:var(--cs-primary-text); margin-bottom:6px;">
                    📈 ChainScope <span style="color:var(--cs-accent);">ID</span>
                </div>
                <div style="font-size:0.8rem; font-weight:700; color:var(--cs-accent); margin-bottom:8px;">Financial Intelligence Platform</div>
                <p>Platform riset pasar terintegrasi, charting teknikal tingkat lanjut, manajemen risiko kuantitatif, dan jurnal portofolio non-custodial untuk investor cerdas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with eco_col2:
        st.markdown(
            """
            <div class="landing-card" style="height:100%; border-top: 3px solid var(--cs-blue-secondary);">
                <div style="font-size:1.15rem; font-weight:800; color:var(--cs-primary-text); margin-bottom:6px;">
                    🏛️ Dwinanta <span style="color:var(--cs-blue-secondary);">Capital</span>
                </div>
                <div style="font-size:0.8rem; font-weight:700; color:var(--cs-blue-secondary); margin-bottom:8px;">Strategic Investment Management</div>
                <p>Manajemen investasi strategis, alokasi private equity, riset modal ventura pada pasar keuangan digital, dan pengembangan teknologi finansial generasi baru.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with eco_col3:
        st.markdown(
            """
            <div class="landing-card" style="height:100%; border-top: 3px solid var(--cs-purple-soft);">
                <div style="font-size:1.15rem; font-weight:800; color:var(--cs-primary-text); margin-bottom:6px;">
                    💎 DX <span style="color:var(--cs-purple-soft);">Luxury</span>
                </div>
                <div style="font-size:0.8rem; font-weight:700; color:var(--cs-purple-soft); margin-bottom:8px;">Luxury Lifestyle & Digital Commerce</div>
                <p>Kurasi gaya hidup bernilai tinggi, perdagangan aset eksklusif, instrumen horologi presisi, dan pengalaman digital berkelas institusional.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 5. SECURITY & PRIVACY EXPLANATION
    st.markdown(
        """
        <div class="landing-section-title">Keamanan & Privasi Data Tingkat Lanjut</div>
        """,
        unsafe_allow_html=True,
    )
    sec_col1, sec_col2, sec_col3 = st.columns(3)
    with sec_col1:
        st.markdown(
            """
            <div class="landing-card">
                <h3>Non-Custodial Architecture</h3>
                <p>Kami tidak pernah memegang kendali atas dana, seed phrase, atau private key Anda. Semua interaksi Web3 diverifikasi langsung di dompet browser Anda.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with sec_col2:
        st.markdown(
            """
            <div class="landing-card">
                <h3>Isolasi Data Pengguna</h3>
                <p>Setiap akun dilindungi oleh Row Level Security (RLS) PostgreSQL dan pemisahan namespace browser storage untuk menjaga catatan jurnal Anda tetap privat.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with sec_col3:
        st.markdown(
            """
            <div class="landing-card">
                <h3>Tanpa Eksekusi Bot Otomatis</h3>
                <p>ChainScope ID murni merupakan platform analitik dan intelijen informasi. Kami tidak melakukan eksekusi order otomatis di bursa pengguna tanpa persetujuan.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 6. FAQ SECTION
    st.markdown(
        """
        <div class="landing-section-title">Pertanyaan yang Sering Diajukan (FAQ)</div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Apakah ChainScope ID dapat digunakan secara gratis?", expanded=False):
        st.write("Ya. ChainScope ID menyediakan tier gratis yang mencakup pemantauan pasar crypto, charting teknikal interaktif, pencatatan transaksi jurnal, kalkulator risiko posisi, dan konverter mata uang.")

    with st.expander("Bagaimana cara kerja metode akuntansi FIFO pada portofolio?", expanded=False):
        st.write("Sistem mencocokkan setiap transaksi penjualan (Sell) dengan lot pembelian (Buy) paling awal yang masih terbuka untuk aset dan strategi yang sama. Ini memberikan perhitungan P/L terealisasi yang akurat dan mencegah distorsi akibat percampuran strategi.")

    with st.expander("Apakah data transaksi dan portofolio saya aman?", expanded=False):
        st.write("Sangat aman. Data transaksi disimpan dengan Row Level Security (RLS) di database terenkripsi yang hanya dapat diakses oleh identitas login Anda. Selain itu, fitur Personal Wallet bekerja secara lokal di browser Anda tanpa disinkronkan ke server.")

    with st.expander("Bursa dan pasar apa saja yang didukung?", expanded=False):
        st.write("Data pasar crypto diperoleh melalui CoinGecko dan Indodax publik; saham mencakup emiten Bursa Efek Indonesia (BEI/IDX) dan pasar global; forex mencakup pasangan valuta asing utama dunia termasuk USD/IDR.")

    with st.expander("Apakah ChainScope ID memberikan nasihat investasi?", expanded=False):
        st.write("Tidak. Semua data, indikator, kalkulator, dan observasi AI di ChainScope ID disajikan murni untuk tujuan informasi, riset, dan edukasi analitik finansial, bukan rekomendasi atau jaminan keuntungan investasi.")

    # 7. GLOBAL FOOTER
    render_institutional_footer(dark_mode=dark_mode, is_authenticated=False)


def render_institutional_footer(dark_mode: bool = False, is_authenticated: bool = False) -> None:
    """Render a comprehensive 5-column institutional footer with legal disclosures."""
    palette = ui.get_theme_palette(dark_mode)
    year = datetime.now().year

    footer_html = f"""
    <footer style="margin-top: 3.5rem; padding-top: 2rem; border-top: 1px solid var(--cs-card-border); color: var(--cs-secondary-text); font-size: 0.85rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 2rem; margin-bottom: 2rem;">
            
            <!-- COLUMN 1: BRAND -->
            <div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom: 12px;">
                    <div class="auth-brand-mark" style="width:28px; height:28px; font-size:0.8rem;">C</div>
                    <span style="font-weight:800; font-size:1.05rem; color:var(--cs-primary-text);">
                        ChainScope <span style="color:var(--cs-accent);">ID</span>
                    </span>
                </div>
                <p style="font-size:0.82rem; line-height:1.6; margin:0 0 10px; color:var(--cs-secondary-text);">
                    Platform intelijen finansial terpadu, terminal charting teknikal, dan evaluasi portofolio non-custodial untuk investor dan trader modern.
                </p>
                <div style="font-size:0.75rem; color:var(--cs-secondary-text);">
                    Institutional Quality · Built in Indonesia
                </div>
            </div>

            <!-- COLUMN 2: PRODUCTS -->
            <div>
                <div style="font-weight:700; color:var(--cs-primary-text); margin-bottom:12px; font-size:0.9rem; letter-spacing:0.02em;">
                    PRODUK
                </div>
                <ul style="list-style:none; padding:0; margin:0; line-height:2;">
                    <li><span style="color:var(--cs-secondary-text);">Pasar Crypto & Ticker</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Pasar Saham (BEI & US)</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Pasar Forex & USD/IDR</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Terminal Advanced Charting</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Jurnal & Portofolio FIFO</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Kekayaan Bersih & Keuangan</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Web3 & Agregator DEX</span></li>
                </ul>
            </div>

            <!-- COLUMN 3: ECOSYSTEM -->
            <div>
                <div style="font-weight:700; color:var(--cs-primary-text); margin-bottom:12px; font-size:0.9rem; letter-spacing:0.02em;">
                    EKOSISTEM
                </div>
                <ul style="list-style:none; padding:0; margin:0; line-height:2;">
                    <li><strong style="color:var(--cs-primary-text);">ChainScope ID</strong></li>
                    <li><span style="color:var(--cs-secondary-text);">Dwinanta Capital</span></li>
                    <li><span style="color:var(--cs-secondary-text);">DX Luxury</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Strategic Digital Ventures</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Private Investment Hub</span></li>
                </ul>
            </div>

            <!-- COLUMN 4: RESOURCES -->
            <div>
                <div style="font-weight:700; color:var(--cs-primary-text); margin-bottom:12px; font-size:0.9rem; letter-spacing:0.02em;">
                    SUMBER DAYA
                </div>
                <ul style="list-style:none; padding:0; margin:0; line-height:2;">
                    <li><span style="color:var(--cs-secondary-text);">Dokumentasi Platform</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Pusat Edukasi Finansial</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Metodologi FIFO & Risiko</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Status Layanan & API</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Tanya Jawab (FAQ)</span></li>
                </ul>
            </div>

            <!-- COLUMN 5: LEGAL & RISK -->
            <div>
                <div style="font-weight:700; color:var(--cs-primary-text); margin-bottom:12px; font-size:0.9rem; letter-spacing:0.02em;">
                    LEGAL
                </div>
                <ul style="list-style:none; padding:0; margin:0; line-height:2;">
                    <li><span style="color:var(--cs-secondary-text);">Kebijakan Privasi</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Ketentuan Layanan</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Pengungkapan Risiko</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Transparansi Non-Custodial</span></li>
                    <li><span style="color:var(--cs-secondary-text);">Etika & Batasan AI</span></li>
                </ul>
            </div>

        </div>

        <!-- RISK DISCLOSURE & COPYRIGHT -->
        <div style="padding: 16px; border-radius: 12px; background: var(--cs-card-surface); border: 1px solid var(--cs-card-border); margin-bottom: 1.5rem; font-size: 0.78rem; line-height: 1.6;">
            <strong>⚠️ PENGUNGKAPAN RISIKO INVESTASI:</strong> Perdagangan aset crypto, saham, instrumen derivatif, dan valuta asing melibatkan risiko volatilitas tinggi dan potensi kehilangan modal sebagian atau seluruhnya.
            Seluruh data, analisis teknikal, indikator kuantitatif, kalkulasi risiko, dan konten AI yang disajikan pada platform ChainScope ID bersifat semata-mata informasional dan edukatif, serta tidak boleh ditafsirkan sebagai rekomendasi, tawaran, atau nasihat keuangan, hukum, atau perpajakan.
        </div>

        <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; padding-bottom:1rem; font-size:0.78rem;">
            <div>
                © {year} ChainScope ID · Seluruh Hak Cipta Dilindungi.
            </div>
            <div style="display:flex; gap:16px;">
                <span>Didukung oleh Dwinanta Capital</span>
                <span>•</span>
                <span>Bagian dari Ekosistem DX Luxury</span>
            </div>
        </div>
    </footer>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
