"""Modul UI Premium (Ultimate Sidebar Redesign)."""
import streamlit as st

def apply_premium_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { background-color: #F8F7FC !important; font-family: 'Inter', sans-serif !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E9E6F0 !important; }
    
    /* CSS Fallback (Jika JS terlambat jalan) */
    [data-testid="stSidebar"] input[type="radio"] { display: none !important; }
    [data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-child { display: none !important; }
    
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
    // SCRIPT SAKTI UNTUK MENGHANCURKAN RADIO BUTTON
    function hackSidebar() {
        const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;

        // Cari semua label di dalam radio group
        const labels = sidebar.querySelectorAll('div[role="radiogroup"] > label');
        
        labels.forEach(label => {
            // Hapus div pertama (yang berisi lingkaran radio)
            const firstDiv = label.querySelector('div:first-child');
            if (firstDiv) firstDiv.style.display = 'none';
            
            // Ubah gaya label menjadi tombol kotak
            label.style.padding = '10px 16px';
            label.style.borderRadius = '8px';
            label.style.marginBottom = '4px';
            label.style.transition = 'all 0.2s';
            label.style.cursor = 'pointer';
            label.style.display = 'flex';
            label.style.alignItems = 'center';
            
            // Cek apakah radio ini sedang terpilih
            const input = label.querySelector('input');
            const isChecked = input && input.checked;
            
            // Ambil teks aslinya
            const textDiv = label.querySelector('div[data-testid="stMarkdownContainer"] p');
            const text = textDiv ? textDiv.innerText : '';
            
            if (isChecked) {
                label.style.backgroundColor = '#F0E9FF'; // Warna ungu muda
                if (textDiv) textDiv.style.color = '#6C35D9'; // Teks ungu
                if (textDiv) textDiv.style.fontWeight = '700';
            } else {
                label.style.backgroundColor = 'transparent';
                if (textDiv) textDiv.style.color = '#77788A'; // Teks abu-abu
                if (textDiv) textDiv.style.fontWeight = '500';
            }

            // Efek Hover
            label.onmouseenter = () => { if (!isChecked) label.style.backgroundColor = '#F8F7FC'; };
            label.onmouseleave = () => { if (!isChecked) label.style.backgroundColor = 'transparent'; };
        });
    }
    
    // Jalankan terus-menerus untuk mengantisipasi re-render Streamlit
    setInterval(hackSidebar, 300);
    </script>
    """, unsafe_allow_html=True)