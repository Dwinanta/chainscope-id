"""Modul UI Premium (Light Mode - Tight Layout & No Radio Circles)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. Background & Font */
    .stApp { background-color: #F8F7FC !important; font-family: 'Inter', sans-serif !important; }
    header[data-testid="stHeader"] { display: none !important; }
    
    /* Sempitkan Margin Utama */
    .block-container { 
        padding-top: 1.5rem !important; 
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important; 
    }

    /* 2. Sidebar (Hilangkan Bulatan Radio & Rapatkan) */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF !important; 
        border-right: 1px solid #E9E6F0 !important; 
        padding-top: 0rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem !important; /* Logo lebih ke atas */
    }
    
    /* KILL RADIO BUTTON CIRCLES (Target semua kemungkinan class) */
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[data-baseweb="radio"] > div[role="radio"] > div:first-child { display: none !important; }
    [data-testid="stSidebar"] input[type="radio"] { display: none !important; }

    /* Style Label Menu */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 10px 12px !important;
        border-radius: 8px !important;
        margin-bottom: 2px !important;
        transition: all 0.2s !important;
        color: #77788A !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover { background-color: #F8F7FC !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #F0E9FF !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #6C35D9 !important;
        font-weight: 700 !important;
    }

    /* 3. Input & Segmented Control */
    div[data-baseweb="input"] { background-color: #FFFFFF !important; border-radius: 20px !important; border: 1px solid #E9E6F0 !important; padding: 2px 10px !important; }
    div[data-baseweb="input"] input { color: #171827 !important; }
    
    div[data-testid="stSegmentedControl"] { background-color: #F8F7FC !important; padding: 4px; border-radius: 8px; }
    div[data-testid="stSegmentedControl"] button { color: #77788A !important; border: none !important; }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background-color: #FFFFFF !important; color: #6C35D9 !important; border-radius: 6px !important; font-weight: 700 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    /* 4. Kartu / Container */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; border-radius: 16px !important;
        border: 1px solid #E9E6F0 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
        padding: 15px !important;
    }

    /* 5. Typography */
    h1 { color: #171827 !important; font-weight: 800 !important; font-size: 2rem !important; letter-spacing: -0.5px; }
    h2 { color: #171827 !important; font-weight: 800 !important; font-size: 1.6rem !important; }
    p, span, div { color: #77788A; }
    .text-green { color: #16834A !important; font-weight: 700; }
    .text-red { color: #D83D50 !important; font-weight: 700; }

    /* 6. Popover Profile Menu */
    div[data-testid="stPopover"] button {
        background-color: #FFFFFF !important; border: 1px solid #E9E6F0 !important; border-radius: 50% !important;
        width: 45px !important; height: 45px !important; padding: 0 !important;
        display: flex !important; justify-content: center !important; align-items: center !important;
        font-size: 1.2rem !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)