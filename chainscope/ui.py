"""Modul UI Premium (No Scroll, No Top Margin, Toggleable)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. Reset Dasar */
    .stApp { background-color: #F8F7FC !important; font-family: 'Inter', sans-serif !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }

    /* ==========================================
       2. SIDEBAR: BEBAS SCROLL & MARGIN ATAS
       ========================================== */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E9E6F0 !important;
    }
    
    /* Tarik konten sidebar ke atas (hilangkan ruang kosong logo) */
    [data-testid="stSidebar"] > div:first-child {
        margin-top: -3.5rem !important; 
        padding-top: 0rem !important;
    }
    
    /* Sembunyikan scrollbar di sidebar */
    [data-testid="stSidebar"]::-webkit-scrollbar { display: none !important; }
    [data-testid="stSidebar"] { -ms-overflow-style: none !important; scrollbar-width: none !important; }
    
    /* Biarkan konten sidebar setinggi aslinya */
    [data-testid="stSidebarUserContent"] { padding-bottom: 2rem !important; }

    /* Jarak antar tombol menu */
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0.3rem !important; }

    /* ==========================================
       3. STYLING LOGO & MENU
       ========================================== */
    .logo-container {
        display: flex; align-items: center; gap: 8px; 
        margin: 1rem 0rem 1.5rem 0rem; 
        padding-left: 10px;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important; border: none !important;
        color: #77788A !important; font-weight: 500 !important;
        text-align: left !important; justify-content: flex-start !important;
        padding: 6px 12px !important; border-radius: 6px !important;
        font-size: 0.9rem !important; box-shadow: none !important;
        min-height: 34px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #F8F7FC !important; color: #171827 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #F0E9FF !important; color: #6C35D9 !important; font-weight: 700 !important;
    }

    /* ==========================================
       4. KONTEN UTAMA
       ========================================== */
    div[data-baseweb="input"] { background-color: #FFFFFF !important; border-radius: 20px !important; border: 1px solid #E9E6F0 !important; padding: 2px 10px !important; }
    div[data-baseweb="input"] input { color: #171827 !important; }
    
    div[data-testid="stSegmentedControl"] { background-color: #F8F7FC !important; padding: 4px; border-radius: 8px; }
    div[data-testid="stSegmentedControl"] button { color: #77788A !important; border: none !important; }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] { background-color: #FFFFFF !important; color: #6C35D9 !important; border-radius: 6px !important; font-weight: 700 !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; border-radius: 16px !important;
        border: 1px solid #E9E6F0 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
        padding: 15px !important;
    }

    h1 { color: #171827 !important; font-weight: 800 !important; font-size: 1.8rem !important; }
    h2 { color: #171827 !important; font-weight: 800 !important; font-size: 1.4rem !important; }
    .text-green { color: #16834A !important; font-weight: 700; }
    .text-red { color: #D83D50 !important; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)