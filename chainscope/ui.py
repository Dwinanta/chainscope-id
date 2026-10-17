"""Modul untuk kustomisasi UI/UX Premium (Dark Terminal Style)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
 
    <style>
           /* Styling Logo Sidebar */
        .sidebar-logo {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 0px 20px 0px;
            border-bottom: 1px solid #1E222D;
            margin-bottom: 20px;
        }
        .sidebar-logo h2 {
            margin: 0;
            font-size: 1.4rem;
            font-weight: 700;
            color: #2962FF;
        }
        .sidebar-logo span {
            color: #FFFFFF;
        }
    /* 1. Font & Background Utama */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #0B0E14; /* Warna background utama */
        font-family: 'Inter', sans-serif;
    }

    /* 2. Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #131722;
        border-right: 1px solid #1E222D;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }
    
    /* Menyembunyikan label bawaan radio agar terlihat seperti menu */
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }
    
    /* Styling tombol menu (Radio) di Sidebar */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 2px;
        transition: all 0.2s;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background-color: #1E222D;
    }
    /* Menu yang aktif */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #1E3A8A;
        border-left: 4px solid #2962FF;
    }

    /* 3. Menghilangkan Padding Berlebih & Margin di Atas */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 95% !important;
    }
    
    /* 4. Styling Judul & Teks */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    p, span, div {
        color: #D1D4DC;
    }

    /* 5. Styling Kartu Metrik (Top 4 Cards) */
    div[data-testid="metric-container"] {
        background-color: #131722;
        border: 1px solid #1E222D;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    
    /* 6. Styling Tabel (Dataframe) */
    div[data-testid="stDataFrame"] {
        background-color: #131722;
        border-radius: 12px;
        border: 1px solid #1E222D;
        padding: 10px;
    }

    /* 7. Tombol Utama */
    .stButton > button {
        background-color: #2962FF;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 500;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #1E4BD8;
        color: white;
    }
    
    /* Warna Font Custom */
    .text-green { color: #00E676 !important; }
    .text-red { color: #FF5252 !important; }
    .text-muted { color: #868B96 !important; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)