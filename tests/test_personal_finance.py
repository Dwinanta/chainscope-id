from chainscope import personal_finance


def test_calculate_net_worth_basic_math():
    res = personal_finance.calculate_net_worth(
        cash_and_bank=50000000.0,
        investments_manual=30000000.0,
        portfolio_crypto_val=20000000.0,
        connected_wallet_val=10000000.0,
        other_assets=0.0,
        total_liabilities=20000000.0,
        deduplicated_overlap=5000000.0,
    )
    # Gross assets = 50 + 30 + 20 + 10 = 110M
    # Net assets = 110M - 5M overlap = 105M
    # Net worth = 105M - 20M liab = 85M
    assert res["total_assets"] == 105000000.0
    assert res["total_liabilities"] == 20000000.0
    assert res["net_worth"] == 85000000.0


def test_calculate_cash_flow_and_savings_rate():
    incomes = [{"amount": 10000000.0}, {"amount": 2000000.0}]
    expenses = [{"amount": 7200000.0}]
    cf = personal_finance.calculate_cash_flow(incomes, expenses)
    assert cf["total_income"] == 12000000.0
    assert cf["total_expense"] == 7200000.0
    assert cf["net_cash_flow"] == 4800000.0
    assert cf["savings_rate_pct"] == 40.0


def test_evaluate_budget_utilization_warning_and_overbudget():
    expenses = [
        {"category": "Makanan & Minuman", "amount": 2500000.0},
        {"category": "Transportasi", "amount": 850000.0},
    ]
    budgets = [
        {"category": "Makanan & Minuman", "monthly_limit": 2000000.0},
        {"category": "Transportasi", "monthly_limit": 1000000.0},
    ]
    util = personal_finance.evaluate_budget_utilization(expenses, budgets)
    food_stat = next(u for u in util if u["category"] == "Makanan & Minuman")
    trans_stat = next(u for u in util if u["category"] == "Transportasi")
    
    assert food_stat["status"] == "Over Budget"
    assert trans_stat["status"] == "Warning (>=80%)"


def test_track_savings_goal_progress():
    goal = {"name": "Dana Darurat", "target_amount": 30000000.0, "monthly_contribution": 3000000.0}
    res = personal_finance.track_savings_goal_progress(goal, 15000000.0)
    assert res["progress_pct"] == 50.0
    assert res["remaining_amount"] == 15000000.0
    assert res["months_to_target"] == 5
    assert res["is_completed"] is False
