"""Fundamental analysis engine for equity valuation, profitability, and health metrics."""

import pandas as pd


# Reliable fundamental benchmarks and ratios for tracked universe
EQUITY_FUNDAMENTALS_DATABASE = {
    # Indonesian Blue Chips (IDX)
    "BBCA.JK": {
        "name": "Bank Central Asia Tbk",
        "sector": "Financials",
        "market_cap_idr": 1250e12,
        "pe_ratio": 24.2,
        "pbv_ratio": 4.6,
        "eps_idr": 415.0,
        "dividend_yield_pct": 2.65,
        "roe_pct": 21.4,
        "roa_pct": 3.6,
        "net_profit_margin_pct": 48.2,
        "debt_to_equity": 0.15,
        "description": "Leading private commercial bank in Indonesia with dominant CASA deposit franchise and robust credit quality.",
    },
    "BBRI.JK": {
        "name": "Bank Rakyat Indonesia Tbk",
        "sector": "Financials",
        "market_cap_idr": 720e12,
        "pe_ratio": 12.8,
        "pbv_ratio": 2.3,
        "eps_idr": 380.0,
        "dividend_yield_pct": 6.8,
        "roe_pct": 18.5,
        "roa_pct": 2.9,
        "net_profit_margin_pct": 32.1,
        "debt_to_equity": 0.22,
        "description": "State-owned microfinance giant with massive nationwide footprint and high dividend payout ratio.",
    },
    "BMRI.JK": {
        "name": "Bank Mandiri Tbk",
        "sector": "Financials",
        "market_cap_idr": 610e12,
        "pe_ratio": 10.9,
        "pbv_ratio": 2.1,
        "eps_idr": 585.0,
        "dividend_yield_pct": 5.4,
        "roe_pct": 20.1,
        "roa_pct": 2.7,
        "net_profit_margin_pct": 36.8,
        "debt_to_equity": 0.18,
        "description": "Indonesia's largest wholesale and corporate lender with rapid digital banking growth (Livin').",
    },
    "TLKM.JK": {
        "name": "Telkom Indonesia Tbk",
        "sector": "Telecommunications",
        "market_cap_idr": 290e12,
        "pe_ratio": 12.1,
        "pbv_ratio": 2.0,
        "eps_idr": 245.0,
        "dividend_yield_pct": 5.8,
        "roe_pct": 16.7,
        "roa_pct": 8.4,
        "net_profit_margin_pct": 16.2,
        "debt_to_equity": 0.45,
        "description": "Leading telecommunication provider in Indonesia offering mobile, fixed broadband (IndiHome), and data centers.",
    },
    "ASII.JK": {
        "name": "Astra International Tbk",
        "sector": "Consumer / Industrial",
        "market_cap_idr": 205e12,
        "pe_ratio": 6.2,
        "pbv_ratio": 1.05,
        "eps_idr": 810.0,
        "dividend_yield_pct": 7.9,
        "roe_pct": 17.2,
        "roa_pct": 8.1,
        "net_profit_margin_pct": 10.5,
        "debt_to_equity": 0.42,
        "description": "Diversified conglomerate spanning automotive distribution, heavy equipment (United Tractors), mining, and agribusiness.",
    },
    # Global Tech Giants (US)
    "AAPL": {
        "name": "Apple Inc.",
        "sector": "Technology",
        "market_cap_idr": 53000e12, # in USD: ~$3.4T
        "pe_ratio": 33.5,
        "pbv_ratio": 48.0,
        "eps_idr": 6.08, # USD EPS
        "dividend_yield_pct": 0.45,
        "roe_pct": 147.2,
        "roa_pct": 28.5,
        "net_profit_margin_pct": 25.3,
        "debt_to_equity": 1.45,
        "description": "Global consumer electronics and services ecosystem powerhouse.",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "market_cap_idr": 48000e12, # in USD: ~$3.1T
        "pe_ratio": 34.2,
        "pbv_ratio": 11.2,
        "eps_idr": 11.80, # USD EPS
        "dividend_yield_pct": 0.72,
        "roe_pct": 38.6,
        "roa_pct": 19.8,
        "net_profit_margin_pct": 36.1,
        "debt_to_equity": 0.38,
        "description": "Enterprise cloud computing, software, productivity, and AI pioneer (Azure, Windows, Office 365).",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "market_cap_idr": 52000e12, # in USD: ~$3.3T
        "pe_ratio": 48.6,
        "pbv_ratio": 38.0,
        "eps_idr": 2.85, # USD EPS
        "dividend_yield_pct": 0.08,
        "roe_pct": 115.0,
        "roa_pct": 55.0,
        "net_profit_margin_pct": 55.4,
        "debt_to_equity": 0.18,
        "description": "World-leading accelerated computing architecture and AI GPU infrastructure designer.",
    },
}


def get_stock_fundamentals(symbol: str) -> dict:
    """Return fundamental metrics, valuation ratios, and business overview for a stock."""
    cleaned = symbol.strip().upper()
    if cleaned in EQUITY_FUNDAMENTALS_DATABASE:
        data = EQUITY_FUNDAMENTALS_DATABASE[cleaned].copy()
        data["symbol"] = cleaned
        data["valuation_grade"] = assess_valuation(data.get("pe_ratio", 20.0), data.get("sector", "General"))
        return data

    # Default model for symbols outside pre-curated dictionary
    is_idx = cleaned.endswith(".JK")
    return {
        "symbol": cleaned,
        "name": cleaned,
        "sector": "General Equities",
        "market_cap_idr": 50e12 if is_idx else 500e9,
        "pe_ratio": 15.0,
        "pbv_ratio": 1.8,
        "eps_idr": 100.0 if is_idx else 2.5,
        "dividend_yield_pct": 2.5,
        "roe_pct": 14.0,
        "roa_pct": 5.0,
        "net_profit_margin_pct": 15.0,
        "debt_to_equity": 0.5,
        "description": f"Publicly traded equity listed on {'IDX' if is_idx else 'international exchange'}.",
        "valuation_grade": "Fair Value",
    }


def assess_valuation(pe_ratio: float, sector: str) -> str:
    """Classify valuation level based on historical sector P/E medians."""
    if pe_ratio <= 0:
        return "Negative Earnings"
    if sector == "Financials":
        if pe_ratio < 11.0:
            return "Undervalued / Attractive"
        elif pe_ratio < 18.0:
            return "Fair Value"
        else:
            return "Premium Valuation"
    elif sector == "Technology":
        if pe_ratio < 25.0:
            return "Attractive for Tech"
        elif pe_ratio < 40.0:
            return "Fair Growth Value"
        else:
            return "High Premium / High Growth"
    else:
        if pe_ratio < 12.0:
            return "Undervalued"
        elif pe_ratio < 22.0:
            return "Fair Value"
        else:
            return "Premium"


def get_sector_comparison_table() -> pd.DataFrame:
    """Generate sector comparison table across all tracked companies."""
    records = []
    for sym, item in EQUITY_FUNDAMENTALS_DATABASE.items():
        records.append({
            "Symbol": sym,
            "Name": item["name"],
            "Sector": item["sector"],
            "P/E": item["pe_ratio"],
            "P/B": item["pbv_ratio"],
            "ROE (%)": item["roe_pct"],
            "Div Yield (%)": item["dividend_yield_pct"],
            "Net Margin (%)": item["net_profit_margin_pct"],
            "Valuation": assess_valuation(item["pe_ratio"], item["sector"]),
        })
    return pd.DataFrame(records)
