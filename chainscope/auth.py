"""Sistem Autentikasi Streamlit dengan Supabase."""
import streamlit as st
from chainscope import db

def login_user(email, password):
    supabase = db.get_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.session_state.session = res.session
        return True, "Login berhasil"
    except Exception as e:
        return False, str(e)

def register_user(email, password):
    supabase = db.get_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return True, "Registrasi berhasil. Silakan login."
    except Exception as e:
        return False, str(e)

def logout_user():
    supabase = db.get_supabase()
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.session = None
    st.rerun()

def show_auth_page():
    """Menampilkan UI Login/Register jika user belum login."""
    st.title("🔒 ChainScope ID - Akses Terbatas")
    st.caption("Silakan login atau daftar untuk mengakses dashboard dan trading journal.")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk", type="primary")
            if submit:
                success, msg = login_user(email, password)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(f"Gagal login: {msg}")
                    
    with tab2:
        with st.form("register_form"):
            email = st.text_input("Email Baru")
            password = st.text_input("Password Baru", type="password")
            submit = st.form_submit_button("Daftar")
            if submit:
                success, msg = register_user(email, password)
                if success:
                    st.success(msg)
                else:
                    st.error(f"Gagal daftar: {msg}")