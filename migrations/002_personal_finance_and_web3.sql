-- ChainScope ID: Personal Finance & Web3 Multi-Chain Schema
-- Migration: 002_personal_finance_and_web3.sql
-- Enables isolated multi-user storage with strict Row Level Security (RLS)

-- 1. PERSONAL INCOMES
CREATE TABLE IF NOT EXISTS public.personal_incomes (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    category TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount > 0),
    is_recurring BOOLEAN DEFAULT FALSE,
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.personal_incomes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own incomes"
    ON public.personal_incomes FOR ALL
    USING (auth.uid() = user_id);

-- 2. PERSONAL EXPENSES
CREATE TABLE IF NOT EXISTS public.personal_expenses (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    category TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL CHECK (amount > 0),
    is_recurring BOOLEAN DEFAULT FALSE,
    note TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.personal_expenses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own expenses"
    ON public.personal_expenses FOR ALL
    USING (auth.uid() = user_id);

-- 3. PERSONAL BUDGETS
CREATE TABLE IF NOT EXISTS public.personal_budgets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    monthly_limit NUMERIC(18, 2) NOT NULL CHECK (monthly_limit > 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, category)
);

ALTER TABLE public.personal_budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own budgets"
    ON public.personal_budgets FOR ALL
    USING (auth.uid() = user_id);

-- 4. SAVINGS GOALS
CREATE TABLE IF NOT EXISTS public.savings_goals (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    target_amount NUMERIC(18, 2) NOT NULL CHECK (target_amount > 0),
    current_amount NUMERIC(18, 2) DEFAULT 0.0 CHECK (current_amount >= 0),
    monthly_contribution NUMERIC(18, 2) DEFAULT 0.0,
    target_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.savings_goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own savings goals"
    ON public.savings_goals FOR ALL
    USING (auth.uid() = user_id);

-- 5. ASSETS & LIABILITIES
CREATE TABLE IF NOT EXISTS public.user_assets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    value_idr NUMERIC(18, 2) NOT NULL,
    symbol TEXT DEFAULT 'IDR',
    is_synced_from_wallet BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_assets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own assets"
    ON public.user_assets FOR ALL
    USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.user_liabilities (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    amount_idr NUMERIC(18, 2) NOT NULL CHECK (amount_idr >= 0),
    monthly_installment NUMERIC(18, 2) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_liabilities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own liabilities"
    ON public.user_liabilities FOR ALL
    USING (auth.uid() = user_id);

-- 6. CONNECTED WEB3 WALLETS
CREATE TABLE IF NOT EXISTS public.connected_wallets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    address TEXT NOT NULL,
    network_type TEXT NOT NULL CHECK (network_type IN ('evm', 'solana')),
    chain_id TEXT NOT NULL,
    label TEXT DEFAULT 'Primary Wallet',
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, address, chain_id)
);

ALTER TABLE public.connected_wallets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own connected wallets"
    ON public.connected_wallets FOR ALL
    USING (auth.uid() = user_id);

-- 7. STRATEGY BUDGETS
CREATE TABLE IF NOT EXISTS public.strategy_budgets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    strategy_tag TEXT NOT NULL,
    target_budget_usd NUMERIC(18, 2) NOT NULL CHECK (target_budget_usd >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, strategy_tag)
);

ALTER TABLE public.strategy_budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own strategy budgets"
    ON public.strategy_budgets FOR ALL
    USING (auth.uid() = user_id);
