# ChainScope ID feature gap report

Reviewed against the application routes, persistence calls, tests, dependencies,
scheduled alert workflow, and README on 2026-11-09. A visible route or module
alone is not treated as proof of a complete feature.

## Baseline inventory (before Batch 1)

| Feature | Classification | Evidence and remaining gap |
|---|---|---|
| Watchlist | Fully implemented | Supabase rows are filtered by `user_id`; the UI synchronizes selections and loads prices for saved assets. |
| Portfolio | Implemented but incomplete | The active page derives holdings from journal buys/sells and current CoinGecko prices. It has no realized P/L, custom strategy lifecycle, or position-level risk. The older `portfolio.json` module is separate and is not the active page's persistence. |
| Trading Journal | Implemented but incomplete | Manual entries, strategy tags, user-scoped reads, pagination, and clear-all exist. Editing individual trades and deleting an individual trade are not exposed in the UI. |
| CSV Import/Export | Implemented but incomplete | Journal CSV import exists, but validates rows weakly and does not map a strategy column. CSV export is absent despite being claimed in README. |
| Alerts | Broken / requires repair | The UI and Supabase alert CRUD exist, but the scheduled workflow calls a script whose `Authorization` header is a literal placeholder. Consequently the scheduled fetch/trigger path cannot authenticate. |
| Converter | Fully implemented | Converts between supported fiat currencies and priced CoinGecko assets using live prices and a cached exchange rate; unavailable rate data is surfaced. |
| Personal Wallet | Implemented but incomplete | The standalone wallet supports local transactions and CSV export, but saves to browser `localStorage`; data is not synchronized to the signed-in Supabase account or other devices. |
| Multi-user authentication | Implemented but incomplete | Supabase signup/login/session restore/password reset and user-scoped trade/watchlist/alert queries exist. No SQL schema or RLS policies are in the repository, so policy enforcement and isolation cannot be independently verified here. |
| Midtrans payment integration | Implemented but incomplete | Snap checkout and transaction-status checks exist. There is no webhook/reconciliation workflow in the repository; production configuration and end-to-end payment verification were not available during this inspection. |
| AI Assistant | Implemented but incomplete | Optional Gemini integration answers a question about a crypto asset using recent price-derived indicators. It does not cover stocks/forex, fundamentals, news-grounded research, or explicit verified-vs-generated evidence labels. |
| Market Dashboard | Fully implemented (crypto scope) | CoinGecko market data, search, charts, gainers/losers, market summaries, indicators, and cached feeds are present. It is not a unified crypto/stock/forex dashboard. |
| News and Research | Implemented but incomplete | A cached external crypto-news feed is displayed. There are no research reports, news analysis/citations, or stock/forex coverage. |
| Admin Panel | Implemented but incomplete | The UI is gated by a database `dev` role and supports user/profile administration. Underlying authorization policies cannot be verified without the absent schema/RLS definitions. |

## Requested expansion features

| Feature | Classification | Evidence and next step |
|---|---|---|
| Performance Coach | Missing entirely before this batch | No journal performance analytics existed. Batch 1 adds FIFO-based coaching from the signed-in user's existing journal records. |
| Multi-strategy portfolio | Implemented but incomplete | `trades.strategy_tag` is already persisted and a basic allocation pie exists, but strategy-level realized/unrealized results and editable strategy assignment are missing. Batch 1 extends this using the existing tag rather than creating duplicate storage. |
| Risk Management Center | Planned but not implemented | Requested for Batch 2; no integrated portfolio risk dashboard, stop-loss risk, or correlation analysis exists. |
| AI Research Assistant | Planned but not implemented | Requested for Batch 2; only the narrow crypto indicator question flow exists. Broader AI research is deferred pending review of data sources and lowest-cost options. |
| Multi-exchange analytics | Planned but not implemented | Indodax candles/tickers and an Upbit/Indodax BTC/ETH comparison are present, but no unified exchange adapter/asset model or shared rate-limit/cache layer exists. |
| DEX analytics | Planned but not implemented | No DEX/on-chain provider integration or analytics module is present. Provider evaluation is required before implementation. |
| Hedge Fund Strategy Lab | Planned but not implemented | No backtesting, benchmark/scenario analysis, or strategy report environment exists. |

## Batch 1 database and data limitations

No Supabase migration is required for Batch 1: the existing `trades.strategy_tag`
column already stores each trade's strategy label, and the new analytics operate
on the user's existing trade rows. No tables, policies, or relationships are
changed. Strategies therefore remain journal labels, not separately persisted
objects with budgets or lifecycle metadata.

The current journal records a date but no required stop-loss, account equity,
or timeframe. Performance metrics must not claim per-trade risk, percentage
drawdown against account equity, timeframe results, or a psychological
assessment. Date-only records also cannot reliably establish intraday ordering
or trading sessions. Identical asset/strategy timestamps are excluded from FIFO
matching; streak and post-loss sizing observations are withheld when event order
is ambiguous. FIFO results are historical journal-derived estimates; unmatched
sells are reported rather than treated as short positions.

## Batch 1 delivered

- Added the Performance Coach route, with realized win rate/profit factor,
  average win/loss, drawdown in USD, strategy/asset breakdowns, streaks and
  approximate UTC session buckets where timestamps support them. The app
  explicitly withholds risk and timeframe claims unsupported by journal fields.
- Extended the existing portfolio page with FIFO positions and realized /
  unrealized P/L by the journal's existing strategy tags. Users can enter a new
  strategy tag on a manual trade and can map an optional strategy column during
  CSV import.
- No dependencies or database migrations were added. Strategies remain tags on
  journal transactions; renaming/reassigning historical tags and standalone
  strategy budgets remain outside this batch.
- CSV export remains absent, and the scheduled alert workflow still needs a
  separate repair.

No live Supabase-backed user session was used during this inspection, and no
database schema/migration or RLS definitions were found. User-specific runtime
results, RLS behavior, Midtrans payments, and external API availability
therefore remain unverified.

## Follow-up audit and Priority 1 result (2026-11-09)

| Area | Current status |
|---|---|
| Supabase authentication | Implemented in code; not end-to-end tested against a live Supabase project. |
| Market dashboard / watchlist / converter | Implemented; conversion math uses ISO currency codes. Market-data tests pass; live provider behavior was spot-checked only. |
| Portfolio / journal / CSV import-export | Implemented with journal CSV export, portfolio realized-result export, and watchlist export. Positions are FIFO by stable asset ID and strategy. |
| Alerts | Scheduled workflow repaired with authenticated HTTP requests, bounded request timeouts, alert pagination, price batching, Telegram status checks, and retry-on-next-run behavior after delivery failures. In-app chat ID setup and test message added. |
| RLS | Unverified: repository contains no SQL schema or policies and no live Supabase project was accessed. Client queries scope by user ID, but that does not prove database-side isolation. No policy changes were made. |
| Strategy budgets | Partially implemented: actual open FIFO capital and allocation are tracked by existing strategy tags. Persisted user-defined budgets/targets are blocked pending a reviewed migration and RLS policy rollout. |
| AI research | Crypto-focused research, indicators, token-market metrics, headline context, asset comparison, and downloadable reports implemented. Optional Gemini interpretation receives the user's submitted question and selected public market/headline context, not ChainScope journal or portfolio records; stocks/forex and financial statements are not connected. |
| Risk Center | Implemented for journal-derived exposure, concentration, realized drawdown, position-size/stop-loss/R:R scenarios, daily historical volatility, correlation, and an asset Sharpe proxy. Account-level risk-adjusted return remains unavailable without equity/deposit history. |

### Coin / currency selector finding

The public CoinGecko `/coins/list` response was checked on 2026-11-09: it
returned 22,874 objects shaped as `{id, symbol, name}`, with the expected
Bitcoin, Ethereum, Solana, and BNB mappings and no duplicate IDs in that
response. It also includes genuine upstream entries with numeric names and
symbols (for example `01`). Existing code used the correct metadata fields;
the main cause of surprising choices was presenting the entire raw token
catalog without validation or a label convention. The CSV importer had a
separate identity bug: substring/regex matching selected the first symbol or
ID match, which could assign the wrong asset. Currency codes and conversion
math were valid, but labels were abbreviated and the configured IDR default was
not applied by the selector.

Priority 1 changes:

- Normalize CoinGecko `id`, `name`, and `symbol` independently; Unicode-normalize
  text, reject empty/control-character IDs and incomplete metadata, log discarded
  rows, deduplicate by ID, and derive `name (SYMBOL)` labels. Valid numeric and
  unusual names/symbols remain selectable.
- Keep CoinGecko ID as the widget/database key and resolve CSV values only by an
  exact ID, unique exact symbol, or unique exact name. Ambiguous symbols are
  skipped and counted rather than guessed.
- Show human-readable fiat names with ISO codes, honor the configured IDR
  default, and leave all exchange-rate calculations keyed by the original codes.
- Render logos from CoinGecko market metadata matched by ID, with a cached,
  selected-asset lookup where the page did not already have an image.
- Group active portfolio positions by stable coin ID to avoid combining
  different assets that happen to share a symbol.

The earlier selector changes passed 150 tests at that point. The current
execution's final test results are recorded in `DEVELOPMENT_PROGRESS.md` after
the complete regression run. Live database records could not be inspected, and
the live API spot check does not validate every catalog entry.

## Full execution update (2026-11-09)

### Completed in this continuation

- Added journal CSV, FIFO realized-portfolio-results CSV, and watchlist CSV
  downloads. CSV serialization limits fields to the requested export and
  neutralizes spreadsheet-formula text.
- Scoped account-specific Streamlit widget state (watchlists, journal paging,
  alert/Telegram inputs, risk scenarios, AI report state, and payment state) by
  authenticated user ID so a second account in the same browser session cannot
  inherit another account's selections or private form values.
- Namespaced Personal Wallet browser storage using a one-way hash of the
  authenticated user ID. Legacy unscoped browser transactions are preserved
  and offered only through an explicit per-user import confirmation; no old
  local data is automatically reassigned or deleted. The wallet remains local
  to that browser and is not synced to Supabase.
- Repaired the scheduled alert job's Bearer authorization. It now pages active
  alerts, batches CoinGecko lookups, checks HTTP/JSON responses with timeouts,
  sends plain-text Telegram notifications, and marks an alert triggered only
  after confirmed delivery (or when no chat is configured). Failed sends leave
  the alert active for a later scheduled retry. The workflow is concurrency
  limited and uses read-only repository permission.
- Added user-scoped Telegram chat ID setup and an explicit test-message button.
  The bot token remains a server secret; no credential is requested in chat or
  stored in source.
- Added an AI Research page using existing market/history APIs, crypto news,
  the cached Fear & Greed feed, and optional Gemini integration. It labels
  provider observations, derived indicators, headlines, and AI interpretation
  separately; supports crypto asset comparison and downloadable reports; does
  not send journal or portfolio records to Gemini. Watchlist assets are used as
  initial research choices. No new dependency or paid provider was added.
- Added the Risk Center for current FIFO exposures, asset/strategy concentration,
  journal realized-P/L drawdown, hypothetical position sizing, stop-loss,
  reward-to-risk, daily return volatility, historical drawdown, pairwise return
  correlation, and an annualized asset Sharpe proxy under a zero-risk-free-rate
  assumption.
- Unified the existing portfolio holdings view with the journal's FIFO engine,
  closing sells only against buys for the same asset and strategy. This avoids
  cross-strategy sells and over-selling from producing misleading residual
  positions.
- Added bounded cache entries for price histories. The research page limits
  each report to five selected assets; the risk page requests up to ten
  30-day histories only after an explicit user action.

### Database and approval boundary

No database migration or policy change was performed. Existing `profiles`,
`alerts`, `trades`, and `watchlists` tables are assumed by the application, but
their live schemas and RLS policies could not be inspected. Existing code
filters user-owned trades, watchlists, alerts, profile lookups, and chat-ID
updates by the signed-in user's ID; these client-side filters are not proof of
RLS enforcement. The scheduled job intentionally uses its configured Supabase
service-role secret to process all active alerts.

Before enabling persistent strategy-budget targets, propose and review a
non-destructive migration with the Supabase project owner:

1. Add `strategy_budgets` with a generated UUID primary key, `user_id` foreign
   key to the confirmed auth identity table, normalized non-empty
   `strategy_tag`, non-negative `target_capital_usd`, optional bounded
   `target_allocation_pct`, and created/updated timestamps.
2. Add a unique constraint on `(user_id, strategy_tag)` and an index beginning
   with `user_id`; do not cascade-delete journal or profile data.
3. Enable RLS and add separate authenticated SELECT, INSERT, UPDATE, and DELETE
   policies requiring `auth.uid() = user_id` in both `USING` and applicable
   `WITH CHECK` clauses. Confirm grants and service/admin behavior against the
   real schema before applying.
4. Validate with Supabase migration dry-run/backup and two-user isolation tests
   in a non-production project. Only then add persistence and budget-vs-actual
   reporting to the UI.

This remains blocked until the schema relationship, policies, and safe
deployment target are available. Current allocation figures are actual
journal-derived open capital, not user-defined budget targets.

### Remaining limitations and manual verification

- The connected market/news providers cover crypto only. Stock and forex
  fundamentals, economic calendars, and news are not represented.
- Risk-adjusted account returns cannot be derived without account equity and
  cash-flow history. The displayed Sharpe proxy is for individual public asset
  returns, not the user's portfolio. Risk sizing is hypothetical and never
  places trades.
- Alert delivery depends on correctly configured GitHub encrypted secrets and
  a profile `telegram_chat_id`; live Supabase/Telegram delivery was not tested.
  If Telegram accepts a message but the following database update fails, the
  next scheduled run can deliver a duplicate; an idempotent outbox requires a
  schema change.
- Supabase RLS enforcement, authentication, payment checkout, and user-data
  isolation require manual integration testing against the actual Supabase and
  Midtrans environments. No live credentials were used.
- Manual browser testing remains required for sign-in, all affected asset
  selectors/logos, dropdown state after page switches, CSV downloads, both
  themes, responsive layouts, Telegram setup/delivery, and the new research and
  risk flows.
- Multi-exchange normalization, DEX analytics, and the historical strategy
  backtesting lab are not part of this continuation's approved execution
  priorities; no provider or methodology was added for them.
