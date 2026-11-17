# ChainScope ID — Error Inventory & Remediation Checklist

**Audit Date:** 2026-11-16  
**Status Key:**
- `[ ] OPEN` — Identified, audited, awaiting repair
- `[-] IN_PROGRESS` — Currently being addressed
- `[x] RESOLVED` — Repaired, verified with tests
- `[~] BLOCKED` — Dependent on external credentials/approval

---

## Error Inventory

### P0 / P1 — Runtime, Authentication, Security & Data Integrity

- [x] **ERR-SEC-01: JWT Token Exposure in URL Query Parameters**
  - **Location:** `chainscope/auth.py` (lines 12–14, 24–36, 66)
  - **Description:** Raw JWT access/refresh tokens are stored in the browser's URL query string, leaking tokens to history, HTTP Referer headers, screenshots, and logs.
  - **Target Fix:** Secure session management via session state; strip tokens from the URL immediately after initial authentication.
  - **Status:** `[x] RESOLVED` (Scrubbed tokens from query_params on login and cleared on session check; regression tests added in tests/test_auth.py)

- [x] **ERR-RT-01: Package Initializer Naming Defects (`_init_.py` instead of `__init__.py`)**
  - **Location:** `chainscope/_init_.py`, `tests/init_.py`
  - **Description:** Standard Python packages require `__init__.py` for reliable packaging, imports, and toolchain discovery.
  - **Target Fix:** Ensure standard `__init__.py` files exist in both `chainscope/` and `tests/`.
  - **Status:** `[x] RESOLVED` (`chainscope/__init__.py` and `tests/__init__.py` created, preserved `_init_.py`)

- [x] **ERR-DAT-01: Personal Finance Ephemeral Session State Gaps**
  - **Location:** `chainscope/views_finance.py`, `chainscope/db.py`
  - **Description:** Personal finance transactions, budgets, and savings goals reset upon session reload because they are stored only in `st.session_state` without a Supabase data access layer.
  - **Target Fix:** Add non-destructive Supabase read/write helpers in `chainscope/db.py` for migration 002 tables, falling back gracefully to session state if database tables are uninitialized.
  - **Status:** `[x] RESOLVED` (`get_user_personal_finance`, `add_personal_income`, `add_personal_expense` implemented and integrated)

- [x] **ERR-SEC-02: Incomplete Cascade Cleanup in `db.delete_user`**
  - **Location:** `chainscope/db.py` (lines 52–56)
  - **Description:** `delete_user` deletes rows from `trades`, `alerts`, `watchlists`, and `profiles`, but omits personal finance and connected wallet records.
  - **Target Fix:** Clean up all user-scoped tables during user deletion.
  - **Status:** `[x] RESOLVED` (Cleaned all migration 002 tables in `delete_user` with tests in `tests/test_db_delete_user.py`)

---

### P2 / P3 — Navigation, Routing, and Quantitative Calculations

- [x] **ERR-ROU-01: Missing Page Routing Fallback & Unhandled Non-Dev `admin-panel`**
  - **Location:** `app.py` (lines 2804, 2932)
  - **Description:** An unrecognized `current_page` or unauthorized attempt to load `admin-panel` results in a completely blank page without feedback or redirect.
  - **Target Fix:** Add an explicit fallback handler in `app.py` that redirects to `market-overview` and informs the user.
  - **Status:** `[x] RESOLVED` (Added non-dev gate with return button and terminating fallback `else:` block in app.py)

- [x] **ERR-APP-01: Hedge Fund Strategy Lab Data Disconnect**
  - **Location:** `app.py` (lines 1238, 2902), `chainscope/views_market.py` (line 154)
  - **Description:** `hedge-fund-lab` is excluded from the market data fetch and ignores the passed `market_data`, hardcoding `bitcoin` with no asset selector.
  - **Target Fix:** Wire the asset selector to fetch historical OHLCV data for any selected cryptocurrency.
  - **Status:** `[x] RESOLVED` (Removed exclusion in app.py and wired interactive asset selector in `render_hedge_fund_lab_page`)

---

### P4 / P5 — Professional Charting & UI/UX

- [ ] **ERR-CHT-01: Professional Charting Terminal Upgrade**
  - **Location:** `chainscope/chart_component.py`
  - **Description:** Missing institutional trading terminal capabilities: interactive drawing tools (trendlines, rays, horizontal levels, rectangles, Fibonacci retracement), multi-indicator suite (VWAP, MACD, ATR, Stochastic, OBV), adjustable parameters/colors, and fullscreen mode.
  - **Target Fix:** Implement advanced technical charting terminal features with custom drawing tools and indicator panels.
  - **Status:** `[ ] OPEN`

- [ ] **ERR-CHT-02: Pine Script-Inspired "ChainScope Script Lab"**
  - **Location:** `chainscope/scripting_engine.py` (new), `app.py`
  - **Description:** Missing custom indicator script compilation and chart plotting engine.
  - **Target Fix:** Build an AST-restricted, memory-bounded, safe script compiler supporting indicator declarations, parameters, price series, technical functions (SMA, EMA, RSI, MACD, Crossover), and interactive chart rendering without `eval()` or `exec()`.
  - **Status:** `[ ] OPEN`

---

### P6 — Technical SEO, Brand Identity & Institutional Footer

- [x] **ERR-SEO-01: Technical SEO Implementation & Static Assets**
  - **Location:** Root directory (`robots.txt`, `sitemap.xml`), `app.py`, `chainscope/landing_page.py`
  - **Description:** Missing search engine crawl directives, canonical URLs, meta descriptions, Open Graph cards, and JSON-LD structured data.
  - **Target Fix:** Create `robots.txt`, `sitemap.xml`, and inject structured schema tags for public landing pages with `noindex` protection on authenticated dashboards.
  - **Status:** `[x] RESOLVED` (`robots.txt`, `sitemap.xml`, `SEO_REPORT.md`, and dynamic meta/schema injection in `chainscope/landing_page.py` verified with tests in `tests/test_landing_and_seo.py`)

- [x] **ERR-UI-01: Institutional Landing Page, AI Team & Ecosystem Showcase**
  - **Location:** `app.py`, `chainscope/ui.py`, `chainscope/landing_page.py`
  - **Description:** Public landing page is minimal and lacks institutional presentation, AI Team showcase, verified Product Ecosystem (*ChainScope ID*, *Dwinanta Capital*, *DX Luxury*), and 5-column institutional footer with risk disclosures.
  - **Target Fix:** Build high-fidelity institutional landing page, AI research ecosystem presentation, verified brand showcase, and multi-column footer.
  - **Status:** `[x] RESOLVED` (Designed institutional landing page with 7 AI Team roles, verified ecosystem showcase, FAQ accordion, and 5-column institutional footer)

- [ ] **ERR-PRF-01: Redundant Full Catalog Merging Optimization**
  - **Location:** `app.py`, `chainscope/api.py`
  - **Description:** Merging 22,000+ catalog rows on repeated page navigations causes unnecessary CPU cycles.
  - **Target Fix:** Memoize catalog merge lookups and optimize dataframe transformations.
  - **Status:** `[ ] OPEN`
