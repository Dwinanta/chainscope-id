# ChainScope ID development progress

## Status

The implementation and local regression pass for the active seven-priority
execution sequence are complete. This does not mean every item in the broader
product vision is complete or end-to-end verified.

## Priority status

1. **Selector and metadata repairs — complete.** Coin IDs remain stable keys;
   CSV asset matching is exact and skips ambiguous matches; currency labels,
   default selection, and logo matching were corrected.
2. **Existing feature completion — partial.** Journal, realized-portfolio, and
   watchlist CSV downloads were added. Scheduled alerts now use authenticated,
   paginated, batched, bounded requests; Telegram setup and delivery checks were
   improved. Persistent strategy budget targets remain blocked pending schema
   and RLS review. RLS itself could not be verified without the Supabase schema
   and a non-production project.
3. **AI research — complete for available crypto data.** The new research flow
   uses existing market/history, news, Fear & Greed, and optional Gemini
   integrations. It distinguishes provider observations, derived values, and
   model interpretation. The UI discloses that the user's question and public
   context are sent to Gemini and that the existing API key may incur usage
   charges. Journal and portfolio records are not sent. Stocks, forex,
   financial-statement fundamentals, and on-chain data are not connected.
4. **Risk Center — implemented with data limitations.** It reports
   journal-derived FIFO exposures and realized drawdown; concentration;
   hypothetical sizing, stop-loss, and reward-to-risk scenarios; and available
   public-asset history metrics. It does not claim account-level risk-adjusted
   performance without equity/cash-flow history.
5. **Integration — implemented locally.** Existing signed-in user IDs scope
   queries and per-user widget keys. Portfolio calculations reuse the FIFO
   journal engine. Wallet data remains browser-local and is namespaced per
   account; legacy data is never reassigned automatically.
6. **UI consistency — code updated; manual verification pending.** Existing
   localization and theme conventions were retained. Sign-in, dropdown
   persistence, logos, light/dark appearance, and responsive layouts still
   require browser testing.
7. **Performance — targeted safeguards added; not benchmarked.** Alert requests
   are paginated/batched, price history is cached with bounded entries, and
   research/risk requests have selection limits and are user-triggered. No
   load/performance benchmark was run.

### Broader vision items not implemented in this pass

Multi-exchange normalization/adapters, DEX analytics, and the historical
strategy backtesting lab remain open roadmap items. No data provider,
methodology, or performance claims were invented for these modules.

## Bugs fixed

- Corrected coin/currency identity and selection behavior, exact CSV asset
  resolution, and portfolio grouping by stable asset ID.
- Fixed scheduled-alert Supabase authorization and HTTP response handling;
  Telegram delivery failures no longer mark alerts as successfully triggered.
- Prevented portfolio sells from closing buys for a different asset/strategy.
- Scoped account-specific Streamlit widget state and wallet browser storage to
  avoid cross-account state reuse in the same browser.
- Added formula-safe CSV serialization and explicit failures for Telegram
  delivery/test flows.

## Database and security

- No database schema, migration, or RLS policy was applied.
- A non-destructive `strategy_budgets` migration and user-isolation policy
  outline is in [FEATURE_GAP_REPORT.md](./FEATURE_GAP_REPORT.md); implementation
  is blocked pending confirmation of the auth relationship and a safe
  non-production Supabase target.
- User-scoped client query filters are present but are not proof of RLS
  enforcement. The scheduled job uses a GitHub Actions service-role secret to
  process all users' alerts.
- No live Supabase, Midtrans, Telegram, Gemini, or browser end-to-end test was
  performed. No credentials were used for this validation.
- The optional Gemini integration reuses the existing provider integration; no
  dependency or paid subscription was added. API usage may still be billable
  under the configured key.

## Files created

- `chainscope/exports.py`
- `chainscope/performance_coach.py`
- `chainscope/research.py`
- `chainscope/risk.py`
- `tests/test_alerts_cron.py`
- `tests/test_exports.py`
- `tests/test_journal_calc.py`
- `tests/test_performance_coach.py`
- `tests/test_research.py`
- `tests/test_risk.py`
- `tests/test_telegram.py`
- `FEATURE_GAP_REPORT.md`
- `DEVELOPMENT_PROGRESS.md`

## Files modified

- `.github/workflows/check_alerts.yml`
- `README.md`
- `app.py`
- `chainscope/api.py`
- `chainscope/config.py`
- `chainscope/db.py`
- `chainscope/journal_calc.py`
- `chainscope/personal_wallet.html`
- `chainscope/telegram.py`
- `chainscope/ui.py`
- `chainscope/wallet_component.py`
- `scripts/check_alerts_cron.py`
- `tests/test_api.py`
- `tests/test_config.py`
- `tests/test_db_profile.py`
- `tests/test_db_watchlist.py`
- `tests/test_ui.py`
- `tests/test_wallet_component.py`

## Verification results

- `.venv\Scripts\python.exe -m pytest -q`: **179 passed**, with one existing
  `google.generativeai` deprecation warning.
- `.venv\Scripts\python.exe -m compileall -q app.py chainscope scripts tests`:
  passed.
- `git diff --check`: passed; Git emitted only a line-ending normalization
  warning for `chainscope/personal_wallet.html`.
- No live-service, browser, accessibility, load, or financial-advice validation
  is implied by these local tests.
