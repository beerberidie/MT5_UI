# MT5_UI Trading Application - Deployment Guide

## Overview

The MT5_UI is a professional MetaTrader 5 trading workstation with a modern React frontend (Tradecraft Console) and FastAPI backend. This guide covers how to run, test, and deploy the application.

---

## System Requirements

### Software
- **Python**: 3.11.9 (required for MT5 and pandas compatibility)
- **Node.js**: 18+ (for frontend build)
- **MetaTrader 5 Terminal**: Installed and running
- **MT5 Account**: Demo or live account configured

### Python Environment
- Virtual environment: `.venv311` (Python 3.11.9)
- All dependencies installed from `requirements.txt` and `requirements-dev.txt`

---

## Quick Start

### 1. Start the Backend Server

```powershell
# From repository root
.\.venv311\Scripts\uvicorn.exe backend.app:app --host 127.0.0.1 --port 5001
```

**Expected output:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5001 (Press CTRL+C to quit)
```

### 2. Start the Frontend Server

```powershell
# From tradecraft-console-main/tradecraft-console-main directory
npm run preview -- --port 3000
```

**Expected output:**
```
➜  Local:   http://localhost:3000/
➜  Network: http://192.168.x.x:3000/
```

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

---

## Architecture

### Frontend (Tradecraft Console)
- **Framework**: React 18.3 + TypeScript + Vite 5.4
- **UI Library**: shadcn-ui + Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Location**: `tradecraft-console-main/tradecraft-console-main/`
- **Dev Port**: 8080
- **Preview Port**: 3000 (production build)

### Backend (FastAPI)
- **Framework**: FastAPI 0.111.0
- **Python**: 3.11.9
- **MT5 Integration**: MetaTrader5 5.0.45
- **Data Processing**: pandas 2.2.2
- **Location**: `backend/`
- **Port**: 5001

### Data Storage
- **Type**: CSV-based file storage
- **Locations**:
  - Data: `./data/`
  - Logs: `./logs/`
  - Config: `./config/`

---

## API Configuration

### Frontend Configuration (`index.html`)

```javascript
window.CONFIG = {
  API_BASE: 'http://127.0.0.1:5001',
  REFRESH_INTERVAL: 5000,
  CONNECTION_TIMEOUT: 10000,
  MAX_RETRIES: 3
};
```

### Authentication (Optional)

```javascript
// Set API key if required
window.AUGMENT_API_KEY = 'your-api-key-here';

// Headers are automatically added by getAuthHeaders()
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (window.AUGMENT_API_KEY) {
    headers['X-API-Key'] = String(window.AUGMENT_API_KEY);
  }
  return headers;
}
```

---

## API Endpoints

### Health & Status

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/health` | GET | Health check and MT5 status | `{status, timestamp, checks, version}` |

### Core Endpoints

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/api/account` | GET | Account information | `{balance, equity, margin, ...}` |
| `/api/positions` | GET | Open positions | `[{ticket, symbol, type, ...}]` |
| `/api/orders` | GET | Pending orders | `[{ticket, symbol, type, ...}]` |
| `/api/symbols` | GET | Market watch symbols | `[{symbol, bid, ask, ...}]` |
| `/api/market-watch` | GET | Symbols in MT5 Market Watch | `[{name, bid, ask, ...}]` |
| `/api/symbol/{symbol}` | GET | Detailed symbol information | `{name, bid, ask, spread, ...}` |
| `/api/symbols/priority` | GET | Priority symbols by win rate | `[{symbol, win_rate, ...}]` |

### Historical Data

| Endpoint | Method | Description | Response Format |
|----------|--------|-------------|-----------------|
| `/api/history/bars` | GET | Historical price bars | `[{time, open, high, low, close, ...}]` |
| `/api/history/deals` | GET | Trading deals history | `{deals: [...], summary: {...}}` |
| `/api/history/orders` | GET | Orders history | `{orders: [...], summary: {...}}` |
| `/api/history/ticks` | GET | Historical ticks | `[{time, bid, ask, ...}]` |

### Trading Operations

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|--------------|
| `/api/order` | POST | Execute market order | `{canonical, side, volume, sl, tp, ...}` |
| `/api/orders/pending` | POST | Create pending order | `{symbol, type, price, volume, ...}` |
| `/api/orders/{ticket}` | PATCH | Modify pending order | `{price, sl, tp, ...}` |
| `/api/orders/{ticket}` | DELETE | Cancel pending order | - |

---

## Important API Changes (v1.1)

### Breaking Changes

**1. Trading Deals Endpoint** (`/api/history/deals`)
- **Old format**: Returns `[]` (empty list) when no deals
- **New format**: Always returns `{deals: [], summary: {...}}`
- **Frontend compatibility**: ✅ Handled by defensive code in `api.ts`

**2. Trading Orders Endpoint** (`/api/history/orders`)
- **Old format**: Returns `[]` (empty list) when no orders
- **New format**: Always returns `{orders: [], summary: {...}}`
- **Frontend compatibility**: ✅ Handled by defensive code in `api.ts`

**3. Historical Ticks Endpoint** (`/api/history/ticks`)
- **Old behavior**: Accepted invalid flags (BID, ASK, LAST, VOLUME)
- **New behavior**: Only accepts valid flags (ALL, INFO, TRADE)
- **Frontend action**: Update any hardcoded flag values

### Frontend Defensive Handling

The frontend `api.ts` already handles both formats:

```typescript
// Deals endpoint
export async function getDeals(opts) {
  const res = await apiCall(`/api/history/deals?${q.toString()}`);
  return Array.isArray(res) ? res : (res?.deals ?? []);
}

// Orders endpoint
export async function getOrdersHistory(opts) {
  const res = await apiCall(`/api/history/orders?${q.toString()}`);
  return Array.isArray(res) ? res : (res?.orders ?? res?.data ?? []);
}
```

---

## Testing

### Backend Tests

```powershell
# Run all tests
.\.venv311\Scripts\pytest.exe -v

# Run specific test file
.\.venv311\Scripts\pytest.exe tests/test_api_endpoints_phase1.py -v

# Run with coverage
.\.venv311\Scripts\pytest.exe --cov=backend --cov-report=html
```

**Test Results**: ✅ 56/56 tests passing (100%)

### Frontend E2E Tests (Playwright)

```powershell
# From tradecraft-console-main/tradecraft-console-main
npm run test:e2e

# Run specific test
npx playwright test tests/e2e/navigation.spec.ts
```

---

## Production Deployment

### 1. Build Frontend

```powershell
cd tradecraft-console-main/tradecraft-console-main
npm run build
```

Output: `dist/` directory with optimized production build

### 2. Serve Frontend

**Option A: Using Vite Preview**
```powershell
npm run preview -- --port 3000
```

**Option B: Using Static File Server**
```powershell
# Install serve globally
npm install -g serve

# Serve the dist directory
serve -s dist -l 3000
```

**Option C: Using Python HTTP Server**
```powershell
cd dist
python -m http.server 3000
```

### 3. Run Backend in Production

```powershell
# With auto-reload disabled
.\.venv311\Scripts\uvicorn.exe backend.app:app --host 127.0.0.1 --port 5001 --no-reload

# With multiple workers (for production)
.\.venv311\Scripts\uvicorn.exe backend.app:app --host 127.0.0.1 --port 5001 --workers 4
```

---

## Security Considerations

### 1. API Key Authentication

**Current Status**: ✅ **ENABLED**

The application uses API key authentication to protect trading operations.

**Backend Configuration** (`.env`):
```
AUGMENT_API_KEY=AC135782469AD
```

**Frontend Configuration** (`index.html`):
```javascript
window.AUGMENT_API_KEY = 'AC135782469AD';
```

**How It Works**:
- Trading endpoints (POST /api/order, etc.) require `X-API-Key` header
- Read-only endpoints (GET /api/account, etc.) do NOT require API key
- Frontend automatically includes API key via `getAuthHeaders()` function
- If `AUGMENT_API_KEY` is empty in `.env`, authentication is disabled

**To Change API Key**:
1. Update `AUGMENT_API_KEY` in `.env`
2. Update `window.AUGMENT_API_KEY` in `tradecraft-console-main/tradecraft-console-main/index.html`
3. Rebuild frontend: `npm run build`
4. Restart both servers

**To Disable API Key Authentication**:
1. Remove or comment out `AUGMENT_API_KEY` in `.env`
2. No frontend changes needed
3. Restart backend server

### 2. CORS Configuration

Backend allows requests from:
- `http://127.0.0.1:3000`
- `http://localhost:3000`
- `http://127.0.0.1:8080` (dev server)

To add more origins, update `backend/config.py`:
```python
FRONTEND_ORIGINS = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://your-domain.com"
]
```

### 3. Rate Limiting

Backend has rate limiting enabled:
- **Order execution**: 10 requests/minute
- **Read operations**: 100 requests/minute

### 4. Logging

All errors and trades are logged to CSV files in `./logs/`:
- `errors.csv` - Error logs with sanitization
- `deals.csv` - Trading deals history
- `orders.csv` - Order execution logs

---

## Troubleshooting

### Backend won't start

**Issue**: `ModuleNotFoundError: No module named 'MetaTrader5'`
**Solution**: Ensure you're using the `.venv311` environment:
```powershell
.\.venv311\Scripts\pip.exe install -r requirements.txt
```

### Frontend can't connect to backend

**Issue**: CORS errors or connection refused
**Solution**: 
1. Verify backend is running on port 5001
2. Check `window.CONFIG.API_BASE` in browser console
3. Verify CORS origins in `backend/config.py`

### MT5 connection fails

**Issue**: `Failed to initialize MT5`
**Solution**:
1. Ensure MT5 terminal is running
2. Check MT5 terminal is logged in to an account
3. Verify account is demo (not live) for testing

### Order execution fails

**Issue**: `Unsupported filling mode`
**Solution**: The backend auto-detects filling mode from symbol info. Ensure symbol is in Market Watch.

---

## Monitoring

### Health Check

Backend provides health information via account endpoint:
```bash
curl http://127.0.0.1:5001/api/account
```

### Logs

Monitor logs in real-time:
```powershell
# Backend logs (console)
# Automatically printed by uvicorn

# Error logs (CSV)
Get-Content logs\errors.csv -Tail 10 -Wait

# Trade logs (CSV)
Get-Content logs\deals.csv -Tail 10 -Wait
```

---

## Support

For issues or questions:
1. Check this deployment guide
2. Review test results: `pytest -v`
3. Check backend logs in `./logs/`
4. Verify MT5 terminal connection

---

**Last Updated**: 2025-10-02
**Version**: 1.1.0
**Status**: ✅ Production Ready

