"""Sistem Autentikasi Streamlit dengan Supabase."""
import streamlit as st
from chainscope import db

def login_user(email, password):
    supabase = db.get_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.session_state.session = res.session
        
        # SIMPAN TOKEN KE URL AGAR TIDAK HILANG SAAT REFRESH
        st.query_params["access_token"] = res.session.access_token
        st.query_params["refresh_token"] = res.session.refresh_token
        return True, "Login berhasil"
    except Exception as e:
        return False, str(e)

def check_session():
    """Cek apakah ada sesi login di memori atau di URL."""
    if "user" in st.session_state and st.session_state.user is not None:
        return

    access_token = st.query_params.get("access_token")
    refresh_token = st.query_params.get("refresh_token")

    if access_token and refresh_token:
        supabase = db.get_supabase()
        try:
            session = supabase.auth.set_session(access_token, refresh_token)
            st.session_state.user = session.user
            st.session_state.session = session.session
        except Exception:
            # Jika token kadaluarsa, bersihkan URL
            st.query_params.clear()

def register_user(email, password):
    supabase = db.get_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return True, "Registrasi berhasil. Silakan login."
    except Exception as e:
        return False, str(e)

def request_password_reset(email: str) -> tuple[bool, str]:
    """Request a password reset email through Supabase Auth."""
    supabase = db.get_supabase()
    try:
        supabase.auth.reset_password_for_email(email)
        return (
            True,
            "Jika email terdaftar, link reset password telah dikirim. Cek inbox Anda.",
        )
    except Exception as e:
        return False, str(e)

def logout_user():
    supabase = db.get_supabase()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    # Bersihkan memori dan URL
    st.session_state.user = None
    st.session_state.session = None
    st.query_params.clear()
    st.rerun()

def show_auth_page():
    """Menampilkan UI Login/Register jika user belum login."""
    form_column, promo_column = st.columns([1.08, 0.92], gap="large")
    with form_column:
        with st.container(border=True):
            st.markdown(
                "<div class='auth-brand'><span class='auth-brand-mark'>C</span>"
                "<span>ChainScope <span style='color:var(--cs-accent)'>ID</span>"
                "</span></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<h1 style='margin-bottom:.25rem'>Selamat datang</h1>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Masuk untuk melihat pasar, mencatat transaksi, dan mengelola "
                "portofolio Anda."
            )

            tab1, tab2 = st.tabs(["Masuk", "Buat akun"])

            with tab1:
                with st.form("login_form"):
                    email = st.text_input(
                        "Email",
                        placeholder="nama@email.com",
                        help="Gunakan email yang terdaftar pada akun Anda.",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Masukkan password",
                    )
                    submit = st.form_submit_button(
                        "Masuk ke akun",
                        type="primary",
                        width="stretch",
                    )
                    if submit:
                        success, msg = login_user(email, password)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(f"Gagal login: {msg}")

                if st.button(
                    "Lupa Password?", key="forgot_password", type="secondary"
                ):
                    st.session_state.show_password_reset = True

                if st.session_state.get("show_password_reset", False):
                    with st.form("reset_password_form"):
                        reset_email = st.text_input(
                            "Email untuk reset password",
                            placeholder="nama@email.com",
                        )
                        reset_submit = st.form_submit_button(
                            "Kirim link reset password",
                            type="primary",
                            width="stretch",
                        )
                        if reset_submit:
                            if not reset_email.strip():
                                st.error("Email wajib diisi.")
                            else:
                                success, msg = request_password_reset(reset_email.strip())
                                if success:
                                    st.success(msg)
                                else:
                                    st.error(f"Gagal mengirim link reset password: {msg}")

            with tab2:
                with st.form("register_form"):
                    email = st.text_input(
                        "Email Baru",
                        placeholder="nama@email.com",
                        help="Gunakan alamat email yang dapat Anda akses.",
                    )
                    password = st.text_input(
                        "Password Baru",
                        type="password",
                        placeholder="Buat password",
                    )
                    st.caption(
                        "Jika konfirmasi email diaktifkan, buka email Anda "
                        "setelah formulir dikirim."
                    )
                    submit = st.form_submit_button(
                        "Buat akun",
                        type="primary",
                        width="stretch",
                    )
                    if submit:
                        success, msg = register_user(email, password)
                        if success:
                            st.success(msg)
                        else:
                            st.error(f"Gagal daftar: {msg}")

    with promo_column:
        st.markdown(
            "<div class='auth-promo'>"
            "<div class='landing-eyebrow'>Platform investasi yang lebih terarah</div>"
            "<h2>Mulai dengan langkah kecil, pahami keputusan Anda.</h2>"
            "<p>ChainScope ID menyatukan informasi pasar dan pencatatan pribadi "
            "dalam satu ruang yang mudah digunakan.</p>"
            "<ul>"
            "<li>Pantau harga dan aset pilihan Anda.</li>"
            "<li>Catat transaksi untuk meninjau kinerja.</li>"
            "<li>Gunakan ringkasan risiko sebagai bahan evaluasi.</li>"
            "</ul>"
            "<p><strong>Catatan:</strong> data pasar dapat berubah dan bukan "
            "jaminan hasil investasi.</p>"
            "</div>",
            unsafe_allow_html=True,
        )