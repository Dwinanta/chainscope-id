"""Modul untuk kustomisasi UI/UX Premium (Dark Terminal Style)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    /* 1. Font & Background Utama */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #0B0E14;
        font-family: 'Inter', sans-serif;
    }

    /* 2. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #131722;
        border-right: 1px solid #1E222D;
    }
    
    /* Logo Container */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid #1E222D;
    }
    .logo-icon {
        background: linear-gradient(135deg, #2962FF, #00E676);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 900;
    }
    .logo-text {
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: 1px;
        color: white;
    }
    .logo-text span {
        color: #2962FF;
    }

    /* Sembunyikan Radio Button Bawaan */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* Ubah Menu Radio menjadi Kotak Elegan */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        padding: 12px 16px;
        background-color: #0B0E14;
        border: 1px solid #1E222D;
        border-radius: 8px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
    }
    
    /* Hover Effect */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background-color: #1E222D;
        border-color: #2962FF;
        transform: translateX(4px);
    }
    
    /* Menu Aktif */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1E3A8A;
        border-color: #2962FF;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        font-weight: 700;
        color: #FFFFFF;
    }

    /* 3. Container & Tabel */
    .block-container { padding-top: 1.5rem !important; max-width: 95% !important; }
    div[data-testid="stDataFrame"] { background-color: #131722; border-radius: 12px; border: 1px solid #1E222D; }
    
    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 600 !important; }
    p, span, div { color: #D1D4DC; }
    .text-green { color: #00E676 !important; }
    .text-red { color: #FF5252 !important; }
    .text-muted { color: #868B96 !important; font-size: 0.85rem; }
    
    .stButton > button {
        background-color: #2962FF; color: white; border-radius: 6px; border: none; font-weight: 500; width: 100%;
    }
    .stButton > button:hover { background-color: #1E4BD8; color: white; }
    </style>
    """, unsafe_allow_html=True)