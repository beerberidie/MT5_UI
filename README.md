# MT5 Local Workstation

A local trading workstation for MetaTrader 5. A FastAPI backend talks to the MT5 terminal, a rule-based engine proposes trade ideas, and **nothing is executed until a human approves it.**

> Scope, stated plainly: the "AI" here is a rule-based signal engine (indicators plus confidence scoring). There is no machine-learning model in this repo.

## What's in it
- **MT5 bridge** (`backend/mt5_client.py`): account, positions and order placement through the MetaTrader5 Python package
- **Signal engine** (`backend/ai/`): indicators, rule sets, per-symbol profiles, and confidence scoring that produce trade ideas
- **Human approval** (`backend/trade_approval_routes.py`): approve, reject, or modify each idea before it reaches the broker
- **Risk limits** (`backend/risk.py`): limits, symbol map and trading sessions loaded from config
- **Background work** (`backend/celery_app.py`, `backend/tasks/`): Celery tasks for signal generation, data refresh and maintenance
- **Storage:** CSV files for market data; trade ideas as JSON files; SQLAlchemy models with Alembic migrations
- **Encryption service** for stored secrets (`backend/services/encryption_service.py`)
- **Monitoring** middleware and routes; live updates over server-sent events
- TypeScript web console

## Run it (Windows; the MT5 terminal must be installed and logged in)
```powershell
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn backend.app:app --host 127.0.0.1 --port 5001
```

## Tests
```bash
pytest -q
```
151 test functions; CI runs lint and tests on Python 3.9, 3.10 and 3.11.

## Not financial advice
This is a personal engineering project. It makes no claim about trading performance.
