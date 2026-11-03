"""Modul UI Premium (Logo ke Atas, Tombol Panah Tetap)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. Reset Dasar */
    .stApp { background-color: #F8F7FC !important; font-family: 'Inter', sans-serif !important; }
    
    header[data-testid="stHeader"] { display: none !important; }
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        margin-top: 0rem !important;
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    ::-webkit-scrollbar { display: none !important; }

    /* 2. SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E9E6F0 !important;
    }
    
    /* TOMBOL PANAH (HIDE/SHOW) */
    [data-testid="stSidebarCollapseButton"] { display: flex !important; opacity: 1 !important; }
    [data-testid="collapsedControl"] { 
        display: flex !important; visibility: visible !important; opacity: 1 !important; 
        z-index: 9999 !important; background-color: #FFFFFF !important; 
        border: 1px solid #E9E6F0 !important; border-radius: 8px !important; 
        padding: 5px !important; top: 20px !important; left: 20px !important; 
    }
    
    /* JANGAN TARIK SIDEBAR, TARIK LOGONYA SAJA */
    [data-testid="stSidebar"] > div:first-child { 
        padding-top: 0rem !important; 
        margin-top: 0rem !important; 
    }
    
    /* Hilangkan Scrollbar Sidebar */
    [data-testid="stSidebar"]::-webkit-scrollbar { display: none !important; }
    [data-testid="stSidebar"] { -ms-overflow-style: none !important; scrollbar-width: none !important; }
    
    /* Jarak antar tombol menu */
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: 0 !important; }

    /* 3. LOGO & MENU */
    .logo-container {
        display: flex; align-items: center; gap: 8px; 
        /* TARIK LOGO KE ATAS MELEWATI HEADER */
        margin-top: -3.5rem !important; 
        margin-bottom: 1.5rem !important; /* Jarak bawah ke menu */
        padding-left: 10px;
        position: relative;
        z-index: 10;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important; border: none !important;
        color: #77788A !important; font-weight: 500 !important;
        text-align: left !important; justify-content: flex-start !important;
        padding: 6px 12px !important; border-radius: 6px !important;
        font-size: 0.9rem !important; box-shadow: none !important;
        min-height: 34px !important; margin-bottom: 4px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #F8F7FC !important; color: #171827 !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #f0e9ff !important; color: #7c3aed !important;
        font-weight: 600 !important; border: none !important; box-shadow: none !important;
    }

    /* 4. KONTEN UTAMA */
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

    @media (max-width: 768px) {
        .block-container {
            width: 100% !important;
            max-width: 100vw !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            box-sizing: border-box !important;
        }
        [data-testid="stMain"] {
            max-width: 100vw !important;
            overflow-x: hidden !important;
        }
        [data-testid="stSidebar"] {
            max-width: 85vw !important;
            box-sizing: border-box !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding: 2.5rem 0.75rem 0.75rem !important;
        }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            z-index: 9999 !important;
        }
        .logo-container { margin-top: 0.5rem !important; }
    }

    </style>
    """, unsafe_allow_html=True)