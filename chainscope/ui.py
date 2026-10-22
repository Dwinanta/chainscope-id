"""Modul untuk kustomisasi UI/UX Premium (Light Mode)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    /* 1. Font & Background Utama */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #F8F7FC;
        font-family: 'Inter', sans-serif;
        color: #171827;
    }

    /* 2. Sidebar Styling (Putih & Ungu) */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E9E6F0;
    }
    
    /* Logo Container */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 10px;
        margin-bottom: 10px;
    }
    .logo-icon {
        background: #6C35D9;
        color: white;
        padding: 6px 10px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 1.2rem;
    }
    .logo-text {
        font-size: 1.3rem;
        font-weight: 700;
        color: #171827;
    }
    .logo-text span {
        color: #6C35D9;
    }

    /* Sembunyikan Radio Button Bawaan */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* Menu Navigasi (Menggunakan Radio) */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        padding: 12px 16px;
        background-color: transparent;
        border-radius: 8px;
        margin-bottom: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #77788A;
        font-weight: 500;
    }
    
    /* Hover Effect */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background-color: #F0E9FF;
        color: #6C35D9;
    }
    
    /* Menu Aktif */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #F0E9FF;
        color: #6C35D9;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        font-weight: 600;
    }

    /* 3. Container & Kartu */
    .block-container { 
        padding-top: 2rem !important; 
        max-width: 95% !important; 
    }
    
    /* Kartu Putih Bersih */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid #E9E6F0 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
    }

    /* Table Styling */
    div[data-testid="stDataFrame"] { 
        background-color: #FFFFFF; 
        border-radius: 16px; 
        border: 1px solid #E9E6F0;
        padding: 10px;
    }
    
    h1, h2, h3, h4 { color: #171827 !important; font-weight: 700 !important; }
    p, span, div { color: #77788A; }
    .text-green { color: #16834A !important; font-weight: 600; }
    .text-red { color: #D83D50 !important; font-weight: 600; }
    
    .stButton > button {
        background-color: #6C35D9; 
        color: white; 
        border-radius: 8px; 
        border: none; 
        font-weight: 600; 
        width: 100%;
    }
    .stButton > button:hover { background-color: #5424B8; color: white; }
    </style>
    """, unsafe_allow_html=True)