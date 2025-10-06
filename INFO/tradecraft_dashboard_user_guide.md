# Tradecraft Trading Dashboard — User Guide

A mobile‑friendly guide to help you get started and trade confidently.

---

## Table of Contents
- [Application Overview](#application-overview)
- [System Requirements](#system-requirements)
- [Getting Started](#getting-started)
- [User Interface Guide](#user-interface-guide)
  - [Dashboard](#dashboard)
  - [Analysis](#analysis)
  - [AI](#ai)
  - [Settings](#settings)
- [Feature Documentation](#feature-documentation)
  - [Market Orders with Auto‑Fill](#market-orders-with-auto-fill)
  - [Pending Orders](#pending-orders)
  - [Risk Management Settings](#risk-management-settings)
  - [Data & Analysis Tools](#data--analysis-tools)
- [Current Limitations](#current-limitations)
- [Development Status](#development-status)
- [Quick Commands](#quick-commands)

---

## Application Overview
The **Tradecraft Trading Dashboard** is designed to be your fast, reliable, and risk-aware workstation for MetaTrader 5. With its sleek React frontend and powerful FastAPI backend, the dashboard helps you focus on trading decisions while handling the heavy lifting of risk management, order placement, and analysis.

Think of it as your **control center**: one screen to place trades, track performance, analyze markets, and enforce consistency in your trading practice.

### What It Offers
- **Seamless MT5 Integration** — Place market and pending orders directly against your MT5 terminal.
- **Smart Auto-Fill** — SL and TP are automatically calculated using your chosen method (PIPS, ATR, PERCENT) and risk/reward target.
- **Built-In Risk Discipline** — Define your default/max risk settings and let the dashboard keep you aligned.
- **Comprehensive Monitoring** — Keep an eye on balances, equity, open positions, order history, and symbol behavior.
- **Analysis at a Glance** — Review recent deals, risk exposure, and key performance metrics all in one place.

### Why It Matters
Trading is about making quick decisions under uncertainty. The dashboard is built to:
- **Speed up workflows**: No more fumbling through MT5 menus.
- **Enforce consistency**: Your risk strategy is always applied.
- **Give clarity**: See exposure, P/L, and symbol behavior before and after trades.

---

## System Requirements
- Windows (recommended) for MT5 compatibility
- MetaTrader 5 terminal installed and logged into a demo account (keep it open)
- Python 3.11 (recommended for MT5 + pandas compatibility)
- Node.js (LTS) for building the frontend
- Modern browser (Edge/Chrome)
- Local ports:
  - Backend: 127.0.0.1:5001
  - Frontend: 127.0.0.1:3000

Optional:
- X‑API‑Key header if you enforce API authentication
- Python virtual environment (.venv)

---

## Getting Started

### 1. Prepare Python Environment
```powershell
py -3.11 -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
- Copy `.env.example` to `.env`
- Ensure MT5 terminal is running and logged in

### 3. Start the Backend (Dev)
```powershell
uvicorn backend.app:app --host 127.0.0.1 --port 5001 --reload
```

### 4. Build and Preview the Frontend
In `tradecraft-console-main/tradecraft-console-main`:
```bash
npm install
npm run build
npx vite preview --port 3000 --strictPort
```

Open http://127.0.0.1:3000

**Tips**
- Default backend URL is http://127.0.0.1:5001
- If using an API key, the app adds `X-API-Key` in requests

---

## User Interface Guide

### Navigation
- Left sidebar: Dashboard, Analysis, AI, Settings
- Tap a button to switch the main content page
- Sidebar can collapse; icons remain visible

### Dashboard
- **Order Entry** (top):
  - Tabs: Market Order | Pending
  - Inputs: Symbol, Volume, Deviation, SL, TP
  - Buttons:
    - Market: BUY / SELL
    - Pending: Place Pending (select type: Buy/Sell Limit/Stop)
  - Auto‑fill:
    - Uses your Settings (strategy + R/R)
    - Side‑aware SL/TP
    - Preserves manual SL/TP edits until inputs change
- **Market Watch / Priority Symbols**:
  - At‑a‑glance symbol list with prices/changes
- **Account Summary**:
  - Balance, Equity, Margin Level, P/L
- **Activity**:
  - Deals: recent trades with totals (profit/commission)
  - Orders: pending orders list (Modify / Cancel) + order history

### Analysis
- **Market Overview**:
  - Priority symbols with price and daily change
- **Performance Analytics**:
  - Balance, Equity, Total Profit (from deals), Win Rate
- **Risk Analysis**:
  - Your risk settings (Default/Max, R/R)
  - Open exposure (total lots), Floating P/L
- **Historical Data**:
  - Recent deals table
- **Symbol Analysis**:
  - Symbol selector + H1 bars (robust fetch with count‑first, 48h fallback)

### AI
- Dedicated AI interface page (placeholder for upcoming features)

### Settings
- **Risk Management**:
  - Default Risk %, Max Risk %, R/R Target
  - SL/TP Strategy: PIPS | ATR | PERCENT
  - Settings persist locally and drive auto‑fill

---

## Feature Documentation

### Market Orders with Auto‑Fill
- Select “Market Order” tab
- Set Symbol, Volume
- Auto‑fill SL/TP:
  - PIPS: fixed pip distances with R/R
  - ATR: volatility‑based distances (strategy dependent)
  - PERCENT: percentage distances
- Side‑aware, rounded, and validated
- Manual SL/TP edits are preserved until context changes

### Pending Orders
- Select “Pending” tab
- Choose type (Buy Limit/Stop, Sell Limit/Stop)
- Enter Pending Price and Volume
- Auto‑fill SL/TP based on pending price and your strategy
- Manage existing pending orders:
  - Activity → Orders: Modify price/SL/TP or Cancel

### Risk Management Settings
- Default Risk %, Max Risk %, R/R Target
- Strategy: PIPS / ATR / PERCENT
- Settings are applied across market and pending auto‑fill

### Data & Analysis Tools
- **Dashboard Activity**:
  - Deals summary, order history, pending orders list with actions
- **Analysis Page**:
  - Symbols overview, performance metrics, risk exposure
  - Recent deals table, symbol bars for context
- **Bars Retrieval**:
  - Count‑first; if empty, uses 48h time range fallback

---

## Current Limitations
- Pending order stop‑level constraints:
  - Broker minimum distance can reject close pending prices/changes
  - Current UI does not auto‑optimize to satisfy stop‑levels yet
- AI page is a placeholder (no live recommendations yet)
- Analysis charts are minimal (tables/metrics available; richer charts planned)
- Guardrails (rate‑limiting, sanitized logging, daily loss enforcement) to be expanded

---

## Development Status

### Working Now
- Navigation: Dashboard / Analysis / AI / Settings
- Order entry:
  - Market + Pending with risk‑aware auto‑fill
  - Pending list with Modify / Cancel
- Analysis:
  - Overview, performance, risk exposure, recent deals, symbol bars
- Testing:
  - Playwright multi‑server startup (frontend + backend)
  - E2E coverage for navigation, orders, settings persistence, bars fallback
- UI/UX:
  - 90% global scaling, accessible form labels, TDZ bug fix

### Coming Next
- Stop‑level‑aware optimizer (reduce pending rejections)
- Guardrails: slowapi limits, structured logs, daily loss checks
- Analysis v2: charts (sparklines/equity curve), volatility/ATR, S/R hints
- AI v1: insights and suggestions

---

## Quick Commands

### Backend (from repo root)
```powershell
py -3.11 -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app:app --host 127.0.0.1 --port 5001 --reload
```

### Frontend (from tradecraft-console-main/tradecraft-console-main)
```bash
npm install
npm run build
npx vite preview --port 3000 --strictPort
```

### Health Checks
```bash
# API health
http://127.0.0.1:5001/api/health

# Open UI
http://127.0.0.1:3000
```
