# 5. SIDEBAR
with st.sidebar:
    # LOGO
    st.markdown("""
        <div class='logo-container'>
            <div style='background: #6C35D9; padding: 6px 10px; border-radius: 8px;'>
                <span style='color:white; font-size:1.2rem;'>⚡</span>
            </div>
            <span style='font-size:1.2rem; font-weight:800; color:#171827;'>ChainScope <span style='color:#6C35D9;'>ID</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    # Garis pemisah
    st.markdown("<hr style='margin: 0px 0px 10px 0px; border-color: #E9E6F0;'>", unsafe_allow_html=True)

    # TOMBOL MENU
    if "current_page" not in st.session_state:
        st.session_state.current_page = "market-overview"

    menu_config = {
        "market-overview": "🏠 Market Overview",
        "market-data": "📊 Market Data",
        "trading-journal": "📒 Trading Journal",
        "price-alerts": "🔔 Price Alerts",
        "technical-analysis": "📉 Technical Analysis",
        "portfolio": "💼 Portfolio",
        "converter": "💱 Converter",
        "watchlist": "⭐ Watchlist"
    }
    if is_dev:
        menu_config["admin-panel"] = "👑 Admin Panel"

    for url_key, display_name in menu_config.items():
        is_active = (st.session_state.current_page == url_key)
        if st.button(display_name, use_container_width=True, key=f"btn_{url_key}", type="primary" if is_active else "secondary"):
            st.session_state.current_page = url_key
            st.rerun()

    # PENGATURAN (Mata Uang, dll)
    st.markdown("---")
    currency = st.radio("Mata uang:", options=["IDR", "USD"], horizontal=True)
    coin_count = st.selectbox("Tampilkan Koin:", options=[50, 100, 250], index=0)
    demo_mode = st.checkbox("Mode Demo", value=False)