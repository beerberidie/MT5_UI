# MT5 Local Workstation (FastAPI + HTML/JS, CSV Storage)

This is the first working version based on the provided blueprint.

## Prerequisites
- Windows 10/11
- MetaTrader 5 installed and logged-in (keep terminal open) — required for live account/positions and order placement
- Python 3.11 (recommended for full compatibility) or 3.13 (works for API sans MT5/pandas)

## Quickstart (Python 3.13 minimal stack)
This starts the API and frontend with modern FastAPI/Pydantic versions (no pandas). MT5 features require the MetaTrader5 wheel which may not support 3.13.
```
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install "fastapi>=0.115" pydantic>=2.9 uvicorn sse-starlette watchdog python-dotenv
Copy-Item .env.example .env
uvicorn backend.app:app --host 127.0.0.1 --port 5001 --reload
```
Frontend (in a second terminal):
```
. .venv\Scripts\Activate.ps1
python -m http.server 3000 -d frontend
```
Open http://127.0.0.1:3000

## Full environment per blueprint (Python 3.11)
If you need pandas and the MetaTrader5 Python bridge, use Python 3.11.
```
py -3.11 -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install fastapi==0.111.0 uvicorn==0.30.1 pydantic==2.7.4 python-dotenv==1.0.1 pandas==2.2.2 MetaTrader5==5.0.45 sse-starlette==1.6.5 watchdog==4.0.1
Copy-Item .env.example .env
uvicorn backend.app:app --host 127.0.0.1 --port 5001 --reload
```

## Basic API checks
```
# Health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5001/api/health | Select-Object -ExpandProperty Content
# Symbols
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5001/api/symbols | Select-Object -ExpandProperty Content
```

## Running tests
- Create/activate the 3.11 venv (.venv311) if not already active
- Install dev deps: pip install -r requirements-dev.txt
- Run unit tests: pytest -q
- Run smoke test: python scripts/smoke_test.py

What the tests cover:
- CSV IO (append_csv/read_csv_rows)
- Risk & sessions CSV parsing
- API endpoints with a mocked MT5 client (no live terminal required)
- CORS preflight behavior
- Smoke test starts uvicorn, checks health, and validates config files and imports

## Notes
- All data and logs are stored under `./data` and `./logs` in CSV.
- `config/` contains CSVs to define symbol aliases, sessions, and risk limits.
- Order placement requires the MT5 terminal to be running and the `MetaTrader5` Python package installed in the venv.

