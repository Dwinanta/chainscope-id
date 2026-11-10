"""Personal finance management engine covering Net Worth, Income, Expenses, Budgets, Savings, and Liabilities."""

from datetime import datetime, timezone
import pandas as pd


EXPENSE_CATEGORIES = [
    "Makanan & Minuman",
    "Tempat Tinggal & Kos/Sewa",
    "Transportasi",
    "Utilitas & Tagihan (Listrik, Air, Internet)",
    "Kesehatan & Asuransi",
    "Pendidikan & Kursus",
    "Belanja & Hiburan",
    "Keluarga & Donasi",
    "Cicilan / Utang",
    "Lain-lain",
]

INCOME_CATEGORIES = [
    "Gaji Pokok",
    "Bisnis / Usaha",
    "Freelance / Pekerjaan Sampingan",
    "Dividen Saham",
    "Trading Crypto / Saham",
    "Bunga Deposito / Tabungan",
    "Sewa Properti",
    "Pendapatan Lainnya",
]

ASSET_TYPES = [
    "Kas / Tabungan Bank",
    "Deposito Berjangka",
    "Portofolio Saham",
    "Portofolio Crypto (Manual)",
    "Emas / Logam Mulia",
    "Properti / Real Estate",
    "Reksa Dana",
    "Aset Lainnya",
]

LIABILITY_TYPES = [
    "Kartu Kredit",
    "KPR (Kredit Pemilikan Rumah)",
    "KKB (Kredit Kendaraan Bermotor)",
    "Pinjaman Bank / KTA",
    "Paylater",
    "Utang Keluarga / Teman",
    "Kewajiban Lainnya",
]


def calculate_net_worth(
    cash_and_bank: float,
    investments_manual: float,
    portfolio_crypto_val: float,
    connected_wallet_val: float,
    other_assets: float,
    total_liabilities: float,
    deduplicated_overlap: float = 0.0,
) -> dict:
    """Calculate Net Worth using strict deduplication accounting rules.
    
    Net Worth = Total Assets - Total Liabilities.
    Ensures connected wallet assets and portfolio holdings are not counted twice.
    """
    gross_assets = (
        max(0.0, cash_and_bank)
        + max(0.0, investments_manual)
        + max(0.0, portfolio_crypto_val)
        + max(0.0, connected_wallet_val)
        + max(0.0, other_assets)
    )
    
    # Deduct any overlap identified by reconciliation
    total_assets = max(0.0, gross_assets - max(0.0, deduplicated_overlap))
    total_liab = max(0.0, total_liabilities)
    net_worth = total_assets - total_liab
    
    return {
        "cash_and_bank": cash_and_bank,
        "investments_manual": investments_manual,
        "portfolio_crypto_val": portfolio_crypto_val,
        "connected_wallet_val": connected_wallet_val,
        "other_assets": other_assets,
        "deduplicated_overlap": deduplicated_overlap,
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(total_liab, 2),
        "net_worth": round(net_worth, 2),
        "debt_to_asset_ratio_pct": round((total_liab / total_assets * 100.0), 2) if total_assets > 0 else 0.0,
    }


def calculate_cash_flow(incomes: list[dict], expenses: list[dict]) -> dict:
    """Calculate total monthly income, expenses, net cash flow, and savings rate."""
    total_income = sum(float(inc.get("amount", 0.0)) for inc in incomes)
    total_expense = sum(float(exp.get("amount", 0.0)) for exp in expenses)
    net_cash_flow = total_income - total_expense
    savings_rate_pct = (net_cash_flow / total_income * 100.0) if total_income > 0 else 0.0
    
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_cash_flow": round(net_cash_flow, 2),
        "savings_rate_pct": round(savings_rate_pct, 1),
    }


def evaluate_budget_utilization(expenses: list[dict], budgets: list[dict]) -> list[dict]:
    """Compare category spending against monthly budget limits and compute remaining allowance and alert status."""
    spending_by_category = {}
    for exp in expenses:
        cat = exp.get("category", "Lain-lain")
        spending_by_category[cat] = spending_by_category.get(cat, 0.0) + float(exp.get("amount", 0.0))
        
    results = []
    for b in budgets:
        cat = b.get("category", "")
        limit = float(b.get("monthly_limit", 0.0))
        spent = spending_by_category.get(cat, 0.0)
        remaining = limit - spent
        pct = (spent / limit * 100.0) if limit > 0 else 0.0
        
        status = "Safe"
        if pct >= 100.0:
            status = "Over Budget"
        elif pct >= 80.0:
            status = "Warning (>=80%)"
            
        results.append({
            "category": cat,
            "monthly_limit": limit,
            "spent": spent,
            "remaining": remaining,
            "utilization_pct": round(pct, 1),
            "status": status,
        })
    return results


def track_savings_goal_progress(goal: dict, total_saved: float) -> dict:
    """Calculate progress toward a target financial goal (Emergency fund, major purchase, etc.)."""
    target = float(goal.get("target_amount", 1.0))
    monthly_contrib = float(goal.get("monthly_contribution", 0.0))
    current_amount = max(0.0, total_saved)
    
    progress_pct = min(100.0, (current_amount / target * 100.0)) if target > 0 else 100.0
    remaining_amount = max(0.0, target - current_amount)
    
    months_left = None
    if monthly_contrib > 0 and remaining_amount > 0:
        months_left = int((remaining_amount + monthly_contrib - 1) // monthly_contrib)
        
    return {
        "name": goal.get("name", "Target Tabungan"),
        "target_amount": target,
        "current_amount": current_amount,
        "progress_pct": round(progress_pct, 1),
        "remaining_amount": round(remaining_amount, 2),
        "months_to_target": months_left,
        "is_completed": current_amount >= target,
    }
