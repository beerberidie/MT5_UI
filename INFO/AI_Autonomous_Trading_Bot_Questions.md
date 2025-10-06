# AI Autonomous Trading Bot: Full Question Bank & Blueprint

This document is a comprehensive checklist of questions and decision areas that successful traders address when designing and running **AI-driven autonomous trading bots**. It is structured top-down, covering strategy, data, modeling, execution, risk, and free data acquisition.

---

## 1. Vision & Scope
- What outcomes define “success” (monthly return, max drawdown, Sharpe, win-rate, capacity)?
- What level of autonomy is acceptable vs. mandatory human approval (full auto, semi-auto, trade guardrails only)?
- What markets, sessions, and holding periods do you target (scalps/intraday/swing)?
- What capital, leverage, and margin constraints are assumed?
- What’s your “do nothing” baseline to beat (e.g., buy/hold, trend follow, passive carry)?

---

## 2. Strategy Edge
- What repeatable market behaviors does the edge exploit (trend, mean-revert, carry, seasonality, flow)?
- Where does the edge likely break (regimes/news/liquidity droughts)?
- What signals matter most, and how did you validate they weren’t data-mined?
- How do you combine signals (rank, linear blend, stacking, ensemble voting, meta-labeling)?
- What *won’t* you trade and why (product rules, broker rules, FIFO, lot size limits)?

---

## 3. Instruments & Broker Mapping
- Which instruments are most robust for the approach (FX majors, index CFDs, gold/crypto)?
- How do you handle **symbol aliases** across brokers/MT5 (e.g., “US_500” vs “SPX500” vs “.US500”)?
- Hedging vs netting accounts—what’s required for your order logic?
- Minimum lot, tick size, contract multipliers—how are these abstracted in your bot?

---

## 4. Data Requirements
- What data types are essential: ticks, 1-min bars, OHLCV, DOM/level2, funding rates, econ releases, news, sentiment?
- What time zones and calendars do you standardize on? How do you handle DST and broker server time?
- What latencies are acceptable for your holding periods?

---

## 5. Free Data Sources (Collection & Storage)
- **Prices/Volumes (OHLCV)**: Stooq, Yahoo Finance, TradingView CSV exports, Dukascopy, HistData, Binance/Bybit APIs for crypto
- **Macro/Econ**: FRED, World Bank, ECB/BOE/BIS, TradingEconomics free tier, government sites
- **News/Sentiment**: NewsAPI, RSS feeds, Reddit/Twitter scraping
- **Calendars**: Central bank sites, government calendars
- **FX-Specific**: Dukascopy JForex bars, HistData 1-min, Stooq FX

Key Questions:
- What’s your plan if a free endpoint throttles or changes format?
- How do you store (CSV, Parquet), partition (symbol/date), and compress data?
- How do you de-dup, gap-fill, and verify checksums?
- What’s your missing-data policy?
- How do you manage rate limits and retries?
- What licensing and usage terms apply?

---

## 6. Data Engineering & Governance
- Canonical timebase (UTC) and symbol map file
- Preventing look-ahead and survivorship bias
- Data validation (monotonic time, no negative volume, outlier clamps)
- Econ data revisions
- Retention policy and backups

---

## 7. Labeling, Features & Modeling
- Target definition (forward returns, meta-labels, regime labels)
- Features: volatility, trend, microstructure, cross-asset spreads
- Model families: trees, GBMs, linear, CNN/LSTM, Transformers, RL
- Where LLMs help (news summarization, decision support, not signal prediction)
- Avoiding overfitting (walk-forward CV, embargo, purging)

---

## 8. Backtesting & Simulation
- Walk-forward design
- Modeling fees, spreads, swaps, slippage
- Broker rules (FIFO, OCO, min step)
- Metrics: Sharpe, Sortino, profit factor, turnover, drawdown
- Stress tests: flash crashes, gaps, spread widening, embargo periods

---

## 9. Risk, Sizing & Portfolio
- Risk framework: daily loss, exposure caps, correlation
- Position sizing: volatility targeting, fixed risk per trade, Kelly capped
- Aggregating strategies: correlation-aware, convex combination
- Kill switches: latency, PnL, slippage, news flags
- Overnight/weekend policies

---

## 10. Execution & MT5/Python Bridge
- Execution path: MT5 terminal + Python, broker REST/WebSocket, FIX
- Idempotent order handling
- Retry/backoff logic, timeouts
- SL/TP and trailing stop management
- Logging state changes

---

## 11. Monitoring & Alerts
- Real-time health checks (feed, loop, broker connectivity, clock skew)
- Dashboards/alerts: local web UI, Telegram/Discord, Grafana
- Runbook for exceptions
- Daily open/close routines

---

## 12. Drift & Adaptation
- Drift and regime detection
- Re-training triggers (manual vs. auto)
- Model retirement/resuscitation policies

---

## 13. Experiment Tracking & Reproducibility
- Versioning (Git, hashes, tags)
- Experiment trackers (CSV ledger, MLflow, W&B)
- Reproducibility guarantees (seeds, pinned libs, Docker)

---

## 14. Automation & Orchestration
- Scheduler (cron, Task Scheduler, n8n)
- Pipeline design: ingest → validate → features → train → backtest → deploy
- Config standards (YAML/TOML), secrets management
- Hot-swapping models

---

## 15. Compliance & Audit
- Logs: orders, PnL, exceptions
- Jurisdictional constraints on CFDs/crypto leverage
- Audit trails for reporting/tax

---

## 16. Cost & Practical Constraints
- Target all-in cost (prefer free/near-free stack)
- Local vs. remote runs
- Degraded modes (broker outage, internet/power cuts)

---

## 17. Lessons From What Works
- Which simple strategies survived live trading
- Which ML/RL ideas failed and why
- Operator habits that mattered most

---

## 18. Documentation & SOPs
- One-page SOP for start/stop/unwind
- Auto-filled trader’s diary
- Changelog of model/config updates

---

# Mini-Checklist: Free Data Acquisition
- Which free endpoints per asset class are validated?
- Schema design (UTC timestamp, symbol, OHLCV, source, checksum)
- Scheduler and retry policy
- Normalization across sources
- Gap-fill rules
- Storage format (CSV/Parquet, partitioning)
- End-to-end verification
- Contingency plan if blocked (switch sources, cached mirrors)

---
