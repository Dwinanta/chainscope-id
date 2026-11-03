"""Gemini-backed trading assistance using recent market indicators."""

import pandas as pd

from . import indicators


def build_indicator_snapshot(history: pd.DataFrame) -> dict[str, float]:
    """Calculate the latest price, RSI, and moving averages from price history."""
    if history.empty or "price" not in history:
        raise ValueError("Riwayat harga tidak tersedia untuk menghitung indikator.")

    prices = pd.to_numeric(history["price"], errors="coerce").dropna()
    if prices.empty:
        raise ValueError("Riwayat harga tidak berisi nilai yang valid.")

    return {
        "harga_terakhir": float(prices.iloc[-1]),
        "RSI": float(indicators.rsi(prices).iloc[-1]),
        "MA20": float(indicators.sma(prices, 20).iloc[-1]),
        "MA50": float(indicators.sma(prices, 50).iloc[-1]),
    }


def build_prompt(
    snapshot: dict[str, float],
    question: str,
    coin_name: str,
) -> str:
    """Build the risk-aware prompt sent to Gemini."""
    return (
        "Kamu adalah analis crypto profesional. "
        f"Berdasarkan data ini: {{'koin': {coin_name!r}, 'mata_uang': 'USD', "
        f"'indikator': {snapshot}}}, "
        f"jawab pertanyaan user: {question}. "
        "Berikan jawaban singkat, padat, dan sertakan disclaimer risiko."
    )


def ask_gemini(api_key: str, prompt: str) -> str:
    """Generate an answer with Gemini; import the SDK only when requested."""
    import google.generativeai as genai

    model = genai.GenerativeModel("gemini-2.5-flash", api_key=api_key)
    response = model.generate_content(prompt)
    answer = response.text
    if not answer or not answer.strip():
        raise ValueError("Gemini tidak mengembalikan jawaban.")
    return answer.strip()
