"""Midtrans Snap payment helpers."""
from hashlib import sha256
from uuid import uuid4
from urllib.parse import quote

import midtransclient
import requests
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


def create_snap_transaction(
    user_id: str, email: str, amount: int, order_id: str | None = None
) -> str:
    """Create a Midtrans Snap transaction and return its redirect URL."""
    if not user_id:
        raise ValueError("ID pengguna wajib diisi.")
    if not email:
        raise ValueError("Email pengguna wajib diisi.")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("Jumlah pembayaran harus berupa bilangan bulat positif.")

    if order_id is None:
        order_id = f"cs-{sha256(user_id.encode()).hexdigest()[:8]}-{uuid4().hex}"
    if not isinstance(order_id, str) or not order_id or len(order_id) > 50:
        raise ValueError("ID pesanan Midtrans wajib diisi dan maksimal 50 karakter.")

    server_key = st.secrets.get("MIDTRANS_SERVER_KEY")
    if not server_key:
        raise ValueError("MIDTRANS_SERVER_KEY belum diatur di secrets.toml.")

    snap = midtransclient.Snap(
        server_key=server_key,
        is_production=is_midtrans_production(),
    )
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


def check_transaction_status(order_id: str) -> str:
    """Fetch the authoritative transaction status from Midtrans."""
    if not isinstance(order_id, str) or not order_id or len(order_id) > 50:
        raise ValueError("ID pesanan Midtrans tidak valid.")

    server_key = st.secrets.get("MIDTRANS_SERVER_KEY")
    if not server_key:
        raise ValueError("MIDTRANS_SERVER_KEY belum diatur di secrets.toml.")

    environment = (
        "api.midtrans.com"
        if is_midtrans_production()
        else "api.sandbox.midtrans.com"
    )
    url = f"https://{environment}/v2/{quote(order_id, safe='')}/status"
    try:
        response = requests.get(url, auth=(server_key, ""), timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SnapPaymentError("Midtrans gagal memeriksa status pembayaran.") from exc

    try:
        transaction = response.json()
    except ValueError as exc:
        raise SnapPaymentError("Midtrans mengembalikan respons status yang tidak valid.") from exc

    transaction_status = (
        transaction.get("transaction_status")
        if isinstance(transaction, dict)
        else None
    )
    if not isinstance(transaction_status, str) or not transaction_status:
        raise SnapPaymentError("Status transaksi tidak ditemukan pada respons Midtrans.")
    return transaction_status
