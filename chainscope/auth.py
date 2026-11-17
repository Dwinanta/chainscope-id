"""Sistem Autentikasi Streamlit dengan Supabase."""
import logging
import socket

import httpx
import streamlit as st
from chainscope import db

logger = logging.getLogger(__name__)

_DNS_ERROR_MARKERS = (
    "Name or service not known",
    "getaddrinfo failed",
    "Temporary failure in name resolution",
    "nodename nor servname provided",
    "No address associated with hostname",
)


def _is_dns_error(exc: BaseException) -> bool:
    """Periksa apakah exception berasal dari kegagalan resolusi DNS."""
    current: BaseException | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, socket.gaierror):
            return True
        text = str(current)
        if any(marker in text for marker in _DNS_ERROR_MARKERS):
            return True
        current = current.__cause__ or current.__context__
    return False


def format_auth_error(exc: Exception) -> str:
    """Format error autentikasi agar masalah DNS, konfigurasi, dan auth terbedakan jelas."""
    if isinstance(exc, db.SupabaseConfigError):
        return f"Konfigurasi Supabase bermasalah: {exc}"
    if _is_dns_error(exc):
        host = db.get_configured_supabase_host()
        return (
            f"Gagal terhubung ke server Supabase (DNS Error pada host '{host}'): {exc}. "
            "Periksa SUPABASE_URL pada konfigurasi Secrets (pastikan bernilai "
            "https://tllnodujibcrkffmtseb.supabase.co tanpa tanda kutip ganda atau spasi)."
        )
    if isinstance(exc, httpx.HTTPError):
        return f"Gagal menghubungi layanan Supabase (Network/HTTPS Error): {exc}"
    return str(exc)


def login_user(email, password):
    clean_email = email.strip() if isinstance(email, str) else ""
    if not clean_email or not password:
        return False, "Email dan password wajib diisi."
    try:
        supabase = db.get_supabase()
        res = supabase.auth.sign_in_with_password({"email": clean_email, "password": password})
        st.session_state.user = res.user
        st.session_state.session = res.session
        return True, "Login berhasil"
    except Exception as e:
        return False, format_auth_error(e)


def check_session():
    """Cek apakah ada sesi login di memori atau di parameter URL."""
    if "user" in st.session_state and st.session_state.user is not None:
        return

    access_token = st.query_params.get("access_token")
    refresh_token = st.query_params.get("refresh_token")

    if access_token and refresh_token:
        try:
            supabase = db.get_supabase()
            session = supabase.auth.set_session(access_token, refresh_token)
            st.session_state.user = session.user
            st.session_state.session = session.session
        except Exception as exc:
            logger.warning("Gagal memulihkan sesi dari parameter URL: %s", exc)
        finally:
            # Segera bersihkan token dari URL untuk mencegah kebocoran via history atau header referer
            st.query_params.clear()


def register_user(email, password):
    clean_email = email.strip() if isinstance(email, str) else ""
    if not clean_email or not password:
        return False, "Email dan password wajib diisi."
    try:
        supabase = db.get_supabase()
        supabase.auth.sign_up({"email": clean_email, "password": password})
        return True, "Registrasi berhasil. Silakan login."
    except Exception as e:
        return False, format_auth_error(e)


def request_password_reset(email: str) -> tuple[bool, str]:
    """Request a password reset email through Supabase Auth."""
    try:
        supabase = db.get_supabase()
        supabase.auth.reset_password_for_email(email)
        return (
            True,
            "Jika email terdaftar, link reset password telah dikirim. Cek inbox Anda.",
        )
    except Exception as e:
        return False, format_auth_error(e)


def logout_user():
    try:
        supabase = db.get_supabase()
        supabase.auth.sign_out()
    except Exception as exc:
        logger.warning("Gagal sign_out dari Supabase: %s", exc)
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