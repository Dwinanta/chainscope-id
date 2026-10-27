"""Modul UI Premium (Light Mode - Ultimate Fix)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { background-color: #F8F7FC !important; font-family: 'Inter', sans-serif !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }

    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E9E6F0 !important; }
    
    /* HANCURKAN BULATAN RADIO SECARA TOTAL */
    [data-testid="stSidebar"] input[type="radio"] { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 10px 16px !important; border-radius: 8px !important; margin-bottom: 2px !important;
        transition: all 0.2s !important; color: #77788A !important; cursor: pointer !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: #F8F7FC !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background-color: #F0E9FF !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #6C35D9 !important; font-weight: 700 !important; }

    div[data-baseweb="input"] { background-color: #FFFFFF !important; border-radius: 20px !important; border: 1px solid #E9E6F0 !important; padding: 2px 10px !important; }
    div[data-baseweb="input"] input { color: #171827 !important; }
    
    div[data-testid="stSegmentedControl"] { background-color: #F8F7FC !important; padding: 4px; border-radius: 8px; }
    div[data-testid="stSegmentedControl"] button { color: #77788A !important; border: none !important; }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] { background-color: #FFFFFF !important; color: #6C35D9 !important; border-radius: 6px !important; font-weight: 700 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important; border-radius: 16px !important;
        border: 1px solid #E9E6F0 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
        padding: 15px !important;
    }

    h1 { color: #171827 !important; font-weight: 800 !important; font-size: 1.8rem !important; }
    h2 { color: #171827 !important; font-weight: 800 !important; font-size: 1.4rem !important; }
    p, span, div { color: #77788A; }
    .text-green { color: #16834A !important; font-weight: 700; }
    .text-red { color: #D83D50 !important; font-weight: 700; }

    div[data-testid="stPopover"] button { background-color: #FFFFFF !important; border: 1px solid #E9E6F0 !important; border-radius: 50% !important; width: 40px !important; height: 40px !important; padding: 0 !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; }
    </style>
    """, unsafe_allow_html=True)