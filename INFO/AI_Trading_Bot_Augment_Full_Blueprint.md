# Master Blueprint: AI Trading Bot (MT5 + Python + Custom Frontend) — Augment-Style

## Executive Summary

**Goal**  
Build an autonomous/semi-autonomous trading system around **MetaTrader 5 (MT5)** execution with a **Python** strategy engine and a **custom web dashboard**, supporting robust data engineering, research/backtesting, deployment, risk controls, and live operations.

**Scope**  
- Success Metrics: Track monthly return, max drawdown, Sharpe ratio, and deployable capital capacity.
- Autonomy Levels: Support full-auto, semi-auto, and “manual approvals required” modes via an approval queue and override switches.
- Markets & Horizons: From scalps and intraday to swing and long-term; instruments include FX majors, indices, gold, and crypto with broker symbol mapping.
- Capital & Constraints: Respect account size, leverage, and broker rules; benchmark against a “do-nothing” baseline.
- Strategy Edge: Explicitly define exploitable behaviors (trend, mean reversion, seasonality), validation to avoid data-mining bias, and ensemble signal-combination with exclusion rules.

**High-Level Outcomes**  
- Research: Data ingestion (free + paid), labeling, features, modeling, and **walk-forward backtesting** with realistic costs & execution rules.
- Risk & Portfolio: Top-down budgets, capped Kelly/vol targeting, sleeves aggregation, hard kill-switches, and weekend policies.
- Execution: MT5 ↔ Python bridge, idempotent order flow, bracket orders, retry/backoff, and reconciliation ledger.
- Ops/Monitoring: Health checks, alerts (Telegram/Discord), exception runbooks, and standardized daily routines.
- Governance: Experiment tracking, versioning, secrets, audit trails, compliance, and reproducibility.
- Reliability & UX: UPS + auto-restart, hotspot fallback, auto-flat SOP if broker down; rich dashboard with trade timelines and risk budgets.

---

## System Architecture

### Logical View (Mermaid Diagram)

```mermaid
flowchart LR
  subgraph Research & Data
    A1[Market Data Ingest
(OHLCV/Tick/DOM/Calendars/News)]
    A2[Validation & Governance
(symbol map, UTC, retention)]
    A3[Feature/Label Pipeline
(T+N targets, meta-labels)]
    A4[Model Training & Selection
(GBMs/LSTMs/TF + walk-forward)]
    A5[Backtests & Stress
(costs, slippage, gaps)]
  end

  subgraph Strategy Engine (Python)
    B1[Signal Orchestrator]
    B2[Risk Manager
(vol targeting, caps, sleeves)]
    B3[Order Router
(idempotent, bracket)]
    B4[Reconciliation Ledger
(intent→order→fill→position)]
  end

  subgraph Execution (MT5)
    C1[MetaTrader5 Terminal]
    C2[Broker]
  end

  subgraph Ops & UI
    D1[Web Dashboard
(Positions/Orders/Approvals)]
    D2[Alerts & Runbooks
(Telegram/Discord/Grafana)]
    D3[Health Checks
(feed/clock/connectivity)]
    D4[Kill Switch & Manual Overrides]
  end

  A1-->A2-->A3-->A4-->A5-->B1
  B1-->B2-->B3-->C1-->C2
  C2-->C1-->B4
  B4-->D1
  B3-->D1
  D1-->D4
  D2-->D4
  D3-->D4
```

---

## Technology Stack Specification

- Python 3.11, Node.js 20, TypeScript 5, Next.js 14, React 18, Tailwind 3
- MetaTrader5 terminal & Python package
- pandas, numpy, pyarrow, scikit-learn, xgboost, lightgbm, tensorflow/pytorch, mlflow
- FastAPI + Uvicorn, Plotly
- PostgreSQL 16, Redis 7
- Docker + Compose
- Grafana/Prometheus

(Env vars and installation commands as described earlier.)

---

## Implementation Specifications

### Project Structure
```
ai-trading-bot/
├─ apps/
│  ├─ strategy/
│  ├─ gateway/
│  └─ dashboard/
├─ packages/
├─ infra/
├─ data/
├─ tests/
└─ README.md
```

- Configs in YAML + `.env`
- Pipeline: ingest → validate → train → backtest → deploy → trade
- Approval queue: Redis

---

## Database Design

- Tables: accounts, instruments, orders, order_fills, positions, pnl_daily, metrics_daily, audit_logs, configs
- SQL schema (as defined earlier)
- Sample inserts (EURUSD, US_500, XAUUSD)

---

## API Specification

- Endpoints: health, positions, orders, overrides, approvals
- Models: OrderRequest, OrderResponse
- Example FastAPI code for gateway

---

## Security Requirements

- API Key
- TLS
- Pydantic validation, SQL constraints
- Secrets in `.env`
- Audit logs

---

## Testing Strategy

- Unit tests, integration tests
- Paper trading environment
- Stress/load tests
- Example pytest (idempotency)

---

## Error Handling

- JSON envelope with codes (ORDER_REJECTED, BROKER_DOWN, etc.)
- audit_logs table for logging
- Runbooks for operator actions

---

## Performance & Scaling

- Parquet storage, UTC normalization
- Redis caching
- Local MT5
- Vectorized backtests
- Kill switch triggers

---

## Deployment & Configuration

- Local-first with Docker Compose
- Postgres, Redis, gateway services
- Example Dockerfile and compose.yaml

---

## Integration Requirements

- Data APIs: Yahoo, Stooq, Binance, FRED, TradingEconomics, NewsAPI, Reddit, CoinDesk
- Alerts via Telegram/Discord
- MLflow for tracking
- Cron/n8n for automation
- Reliability SOPs

---

## Code Quality Standards

- black, ruff, isort, mypy
- Pre-commit hooks
- Peer review required for strategy/risk changes
- Documentation and changelog maintained

---

# ✅ End of AI Trading Bot Augment-Style Blueprint
