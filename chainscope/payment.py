"""Midtrans Snap payment helpers."""
from hashlib import sha256
from uuid import uuid4

import midtransclient
import streamlit as st


class SnapPaymentError(Exception):
    """Raised when Midtrans cannot create a Snap transaction."""


def is_midtrans_production() -> bool:
    """Return whether Midtrans is configured for production mode."""
    value = st.secrets.get("MIDTRANS_IS_PRODUCTION")
    if value is None:
        raise ValueError("MIDTRANS_IS_PRODUCTION belum diatur di secrets.toml.")
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no", ""}:
            return False
    raise ValueError("MIDTRANS_IS_PRODUCTION harus berupa boolean.")


def create_snap_transaction(user_id: str, email: str, amount: int) -> str:
    """Create a Midtrans Snap transaction and return its redirect URL."""
    if not user_id:
        raise ValueError("ID pengguna wajib diisi.")
    if not email:
        raise ValueError("Email pengguna wajib diisi.")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("Jumlah pembayaran harus berupa bilangan bulat positif.")

    server_key = st.secrets.get("MIDTRANS_SERVER_KEY")
    if not server_key:
        raise ValueError("MIDTRANS_SERVER_KEY belum diatur di secrets.toml.")

    snap = midtransclient.Snap(
        server_key=server_key,
        is_production=is_midtrans_production(),
    )
    order_id = f"cs-{sha256(user_id.encode()).hexdigest()[:8]}-{uuid4().hex}"
    try:
        transaction = snap.create_transaction({
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": amount,
            },
            "customer_details": {"email": email},
        })
    except midtransclient.MidtransAPIError as exc:
        raise SnapPaymentError("Midtrans gagal membuat transaksi pembayaran.") from exc

    redirect_url = transaction.get("redirect_url")
    if not redirect_url:
        raise ValueError("Midtrans tidak mengembalikan URL pembayaran.")
    return redirect_url
