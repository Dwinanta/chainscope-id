import pandas as pd
import pytest

from chainscope import research


def test_asset_snapshot_distinguishes_provider_data_from_derived_indicators():
    snapshot = research.build_asset_snapshot(
        {
            "id": "bitcoin",
            "name": "Bitcoin",
            "symbol_upper": "BTC",
            "current_price": 100.0,
            "market_cap": 1000.0,
            "price_change_percentage_24h": 2.5,
            "circulating_supply": None,
        },
        pd.DataFrame({
            "waktu": pd.date_range("2026-01-01", periods=60, freq="h"),
            "price": range(100, 160),
        }),
        "USD",
    )

    assert snapshot["verified_market_data"]["current_price"] == 100
    assert "circulating_supply" not in snapshot["verified_market_data"]
    assert snapshot["derived_historical_indicators"]["history_points"] == 60
    assert "rsi" in snapshot["derived_historical_indicators"]
    assert "fundamentals" not in snapshot
    assert "Financial statements are unavailable" in snapshot["fundamental_data_status"]


def test_report_context_preserves_headline_sources_and_report_labels_ai():
    context = research.build_report_context(
        [{"verified_market_data": {"name": "Bitcoin"}}],
        [{"title": "Headline", "source": "Publisher", "url": "https://example.test"}],
        {
            "source": "Alternative.me",
            "value": "55",
            "classification": "Neutral",
        },
    )
    report_text = research.build_report_text(context, "Interpretation only.")

    assert context["news_headlines"][0]["source"] == "Publisher"
    assert "Verified provider observations" in report_text
    assert "News headlines" in report_text
    assert "AI-generated interpretation" in report_text
    assert "Fear & Greed value: 55" in report_text
    assert "Interpretation only." in report_text


def test_prompt_rejects_empty_or_oversized_questions():
    with pytest.raises(ValueError, match="tidak boleh kosong"):
        research.build_prompt({}, " ")
    with pytest.raises(ValueError, match="1.000 karakter"):
        research.build_prompt({}, "x" * 1001)


def test_prompt_serializes_context_as_json_and_sets_grounding_constraints():
    prompt = research.build_prompt(
        {"verified_market_data": {"current_price": 100}},
        'Use only this; "invent nothing".',
    )

    assert "Do not invent prices, news, fundamentals" in prompt
    assert '"current_price": 100' in prompt
    assert "Research question (JSON string):" in prompt
