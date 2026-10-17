"""Modul untuk kustomisasi UI/UX Premium."""
import streamlit as st

def apply_premium_theme():
    """Menyuntikkan CSS kustom untuk tampilan Terminal Trading Premium."""
    st.markdown("""
    <style>
    /* 1. Import Font Premium (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 2. Menghilangkan Padding Berlebih di Atas */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* 3. Styling Kartu Metrik (st.metric) */
    div[data-testid="metric-container"] {
        background-color: #131722;
        border: 1px solid #2A2E39;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        border-color: #2962FF;
    }

    /* Warna khusus untuk Delta (P&L) */
    div[data-testid="metric-container"] div[data-testid="stMetricDelta"] > div {
        font-weight: 600;
    }

    /* 4. Styling Tab (Menu Navigasi) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #131722;
        padding: 5px 10px;
        border-radius: 8px;
        border: 1px solid #2A2E39;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        color: #868B96;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2962FF !important;
        color: #FFFFFF !important;
    }

    /* 5. Styling Tombol (Buttons) */
    .stButton > button {
        background-color: #2962FF;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #1E4BD8;
        box-shadow: 0 0 10px rgba(41, 98, 255, 0.5);
        color: white;
    }

    /* Tombol Secondary (seperti Hapus) */
    .stButton > button[kind="secondary"] {
        background-color: transparent;
        border: 1px solid #ef5350;
        color: #ef5350;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #ef5350;
        color: white;
    }

    /* 6. Styling Tabel / Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        border: 1px solid #2A2E39;
        overflow: hidden;
    }

    /* 7. Sidebar Styling */
    [data-testid="stSidebar"] {
        border-right: 1px solid #2A2E39;
    }
    
    /* 8. Menghilangkan garis merah bawaan Streamlit */
    hr {
        margin: 1rem 0;
        border-color: #2A2E39 !important;
    }
    </style>
    """, unsafe_allow_html=True)