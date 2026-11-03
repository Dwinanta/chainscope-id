import pandas as pd
import pytest

from chainscope import ai_assistant, indicators


def test_build_indicator_snapshot_uses_latest_price_and_indicators():
    history = pd.DataFrame({"price": range(1, 61)})

    snapshot = ai_assistant.build_indicator_snapshot(history)

    assert snapshot["harga_terakhir"] == 60.0
    assert snapshot["RSI"] == pytest.approx(indicators.rsi(history["price"]).iloc[-1])
    assert snapshot["MA20"] == pytest.approx(50.5)
    assert snapshot["MA50"] == pytest.approx(35.5)


@pytest.mark.parametrize(
    "history",
    [pd.DataFrame(), pd.DataFrame({"other": [1.0]})],
)
def test_build_indicator_snapshot_rejects_missing_price_history(history):
    with pytest.raises(ValueError, match="Riwayat harga"):
        ai_assistant.build_indicator_snapshot(history)


def test_build_prompt_includes_data_question_and_risk_disclaimer():
    prompt = ai_assistant.build_prompt(
        {"harga_terakhir": 100.0, "RSI": 55.0, "MA20": 98.0, "MA50": 90.0},
        "Apakah bagus beli BTC sekarang?",
        "Bitcoin (BTC)",
    )

    assert "Kamu adalah analis crypto profesional." in prompt
    assert "Bitcoin (BTC)" in prompt
    assert "'mata_uang': 'USD'" in prompt
    assert "harga_terakhir" in prompt
    assert "jawab pertanyaan user: Apakah bagus beli BTC sekarang?" in prompt
    assert "sertakan disclaimer risiko" in prompt


def test_ask_gemini_uses_configured_api_key(monkeypatch):
    from google import generativeai as genai

    calls = {}

    class FakeModel:
        def __init__(self, model_name, api_key):
            calls["model_name"] = model_name
            calls["api_key"] = api_key

        def generate_content(self, prompt):
            calls["prompt"] = prompt
            return type("Response", (), {"text": "Analisis dengan risiko."})()

    monkeypatch.setattr(genai, "GenerativeModel", FakeModel)

    answer = ai_assistant.ask_gemini("test-key", "prompt")

    assert answer == "Analisis dengan risiko."
    assert calls == {
        "model_name": "gemini-2.5-flash",
        "api_key": "test-key",
        "prompt": "prompt",
    }
