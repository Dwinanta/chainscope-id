"""Modul UI Premium (Light Mode - Pixel Perfect)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    /* 1. Font & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { background-color: #F8F7FC; font-family: 'Inter', sans-serif; }
    
    /* Sembunyikan Header Streamlit */
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 2rem !important; max-width: 95% !important; }

    /* 2. Sidebar & Menu */
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E9E6F0; }
    
    /* HAPUS BULATAN RADIO BUTTON */
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    
    /* Style Menu Sidebar */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 12px 16px; border-radius: 8px; margin-bottom: 4px;
        cursor: pointer; transition: all 0.2s; color: #77788A; font-weight: 500;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: #F8F7FC; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: #F0E9FF; color: #6C35D9;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        font-weight: 700; color: #6C35D9;
    }

    /* 3. Typography & Colors */
    h1 { color: #171827 !important; font-weight: 800 !important; font-size: 2rem !important; }
    h2 { color: #171827 !important; font-weight: 700 !important; font-size: 1.6rem !important; }
    p, span, div { color: #77788A; }
    .text-green { color: #16834A !important; font-weight: 600; }
    .text-red { color: #D83D50 !important; font-weight: 600; }

    /* 4. Clean Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; border-radius: 16px !important;
        border: 1px solid #E9E6F0 !important; box-shadow: 0 2px 10px rgba(0,0,0,0.02) !important;
        padding: 5px !important;
    }

    /* 5. Segmented Control (1D 7D 1M 1Y) */
    div[data-testid="stSegmentedControl"] button { background-color: transparent !important; color: #77788A !important; border: none !important; }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #F0E9FF !important; color: #6C35D9 !important; border-radius: 8px !important; font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)