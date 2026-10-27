"""Modul UI Premium (Light Mode - JavaScript Force Kill)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { background-color: #F8F7FC !important; font-family: 'Inter', sans-serif !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E9E6F0 !important; }
    
    /* CSS Fallback (Jika JS gagal) */
    [data-testid="stSidebar"] input[type="radio"] { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[data-baseweb="radio"] > div[role="radio"] > div:first-child { display: none !important; }
    
    /* Styling Menu */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 8px 12px !important; border-radius: 8px !important; margin-bottom: 2px !important;
        transition: all 0.2s !important; color: #77788A !important; cursor: pointer !important;
        display: flex !important; align-items: center !important;
    }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background-color: #F8F7FC !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background-color: #F0E9FF !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: #6C35D9 !important; font-weight: 700 !important; }

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
    
    <script>
    // JAVASCRIPT UNTUK MEMAKSA HAPUS BULATAN RADIO
    function killRadios() {
        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            const radios = sidebar.querySelectorAll('input[type="radio"]');
            radios.forEach(r => {
                let parent = r.parentElement;
                while (parent && parent !== sidebar) {
                    if (parent.tagName === 'DIV' && parent.getAttribute('role') === 'radio') {
                        // Sembunyikan semua div anak pertama (yang berisi bulatan)
                        Array.from(parent.children).forEach((child, idx) => {
                            if (idx === 0) child.style.display = 'none';
                        });
                    }
                    parent = parent.parentElement;
                }
            });
        }
    }
    // Jalankan setiap 500ms untuk mengantisipasi perubahan DOM Streamlit
    setInterval(killRadios, 500);
    </script>
    """, unsafe_allow_html=True)