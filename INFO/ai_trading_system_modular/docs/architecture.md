# System Architecture (Final)

```mermaid
flowchart LR
  subgraph Research & Data
    A1[Market Data Ingest (OHLCV/Tick/DOM/Calendars/News)]
    A2[Validation & Governance (UTC, symbol map, retention)]
    A3[Feature/Label Pipeline (T+N targets, meta-labels)]
    A4[Model Training & Walk-Forward Selection]
    A5[Backtests & Stress Tests (costs, slippage, gaps)]
  end

  subgraph Strategy Engine (Python)
    B1[Signal Orchestrator]
    B2[Risk Manager (vol targeting, caps, sleeves)]
    B3[Order Router (idempotent, bracket, retries)]
    B4[Reconciliation Ledger (intent→order→fill→position)]
  end

  subgraph Execution (MT5)
    C1[MT5 Terminal API]
    C2[Broker]
  end

  subgraph Ops & Dashboard
    D1[Tradecraft Web Dashboard (Positions/Orders/Risk)]
    D2[Alerts & Runbooks (Telegram/Discord/Grafana)]
    D3[Health Checks (feed/clock/connectivity)]
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
 
## Tech Stack
- Python 3.11, Node.js 20, TypeScript 5, React 18, Next.js 14, Tailwind 3
- MetaTrader5 Python API; pandas, numpy, scikit-learn, xgboost, pytorch/tensorflow
- FastAPI + Uvicorn; Redis; PostgreSQL; Docker Compose
- Grafana/Prometheus for monitoring

## Project Structure
```
ai-trading-bot/
├─ apps/
│  ├─ strategy/        # signals, models
│  ├─ gateway/         # FastAPI + MT5 order router
│  └─ dashboard/       # Tradecraft React frontend
├─ packages/           # shared libs
├─ infra/              # Docker, configs, monitoring
├─ data/               # CSV/Parquet storage
├─ tests/              # pytest + integration
└─ README.md
```
