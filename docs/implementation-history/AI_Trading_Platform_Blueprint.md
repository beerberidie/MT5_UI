# AI Trading Platform — Implementation Blueprint  
**Date:** 27 Oct 2025  
**Owner:** Garrison  
**Audience:** AI engineering agent  
**Document Role:** Final build spec / reality check  
**System Codename (internal):** `ai-trader`  

---

## Table of Contents
1. Executive Summary  
2. System Architecture  
3. Technology Stack Specification  
4. Implementation Specifications  
5. Database Design  
6. API Specification  
7. Security Requirements  
8. Testing Strategy  
9. Error Handling  
10. Performance & Scaling  
11. Deployment & Configuration  
12. Integration Requirements  
13. Code Quality Standards  
14. Appendix: Confidence Score Heuristic v1, Halt/Resume Logic

---

## 1. Executive Summary

### 1.1 Mission
Build an AI-driven trading assistant that behaves like a disciplined trader:
- Watches markets continuously.
- Generates trade ideas aligned with predefined strategies.
- Enforces risk rules before execution.
- Places trades automatically in MetaTrader 5 (MT5) through AvaTrade when allowed.
- Logs every step so nothing is hidden.

This is not “a dashboard.” This is an AI trader with auditability, supervision modes, and a kill switch.

### 1.2 Modes
- **Supervised Mode (Semi-Automatic):**
  - AI proposes trades with rationale and confidence.
  - Human approves or rejects.
  - On approval, order is placed on MT5 and logged.

- **Autonomous Mode (Automatic):**
  - AI can auto-execute trades without human approval **only if**:
    - Global “AI Trading Enabled” is ON.
    - Confidence score ≥ configured threshold.
    - Trade complies with an ACTIVE strategy.
    - Risk & exposure checks all pass (max lot size, max concurrent trades, drawdown, daily target logic).
    - No blocked macro events (e.g. high-impact USD news within restricted window).

If any enforced rule fails: no auto trade.

### 1.3 Core Loop
Every cycle:
1. Collect market context and account state.
2. Generate trade ideas per active strategy.
3. Evaluate risk and autonomy rules.
4. Take an action:
   - Auto-execute trade (and log).
   - Mark “Needs approval.”
   - Mark “Rejected for risk.”
5. Persist Decision History + snapshot for audit.

### 1.4 Hard Non-Negotiables
- **No mystery trades.** Every AI action and human override is logged.
- **Strategy obedience.** AI can only trade using approved strategy definitions.
- **Risk obedience.** Confidence threshold, daily targets, drawdown caps, lot limits, session rules, and “no trade during high-impact news” rules are enforced.
- **Full context replay.** For any past action, we must be able to reconstruct “what the AI saw right then.”

---

## 2. System Architecture

### 2.1 High-Level Components
- **Frontend Web App**
  - Dashboard, AI Trading Control Panel, Active Trade Ideas, Manual Evaluation, Decision History, Settings.
  - Dark theme. Sidebar with icons+tooltips when collapsed.
  - Real-time or near-real-time status views (account state, AI status).

- **Backend API Server**
  - REST API.
  - Authenticated.
  - Owns:
    - Strategy rules storage and validation.
    - Risk management logic.
    - Decision History logging.
    - MT5 bridge orchestration.
    - AI model calls (OpenAI).
    - Scheduled data ingestion (market snapshots, calendar, news).

- **Scheduler / Worker Service**
  - Periodic jobs:
    - Candle + indicator ingestion.
    - Economic calendar ingestion.
    - News / RSS ingestion.
    - Account state snapshot.
  - Stores snapshots in DB for audit and strategy evaluation.

- **MT5 Connector Service**
  - Talks to the user’s AvaTrade MT5 account.
  - Capabilities:
    - Fetch balance, equity, margin, open trades, trade history.
    - Place/modify/close orders.
  - Exposes a local authenticated API that the main backend uses.
  - Must not depend on “MT5 terminal open locally on desktop.” Must be a persistent service.

- **AI Reasoning Engine**
  - Uses snapshot data + active strategies -> proposes trades.
  - Assigns confidence scores.
  - Generates human-readable rationale.
  - Returns structured trade ideas to backend.

- **PostgreSQL Database**
  - Stores:
    - Snapshots (market, indicators, calendar, news, account).
    - Strategies (structured JSON).
    - Trade ideas.
    - Executions.
    - Decision History.
    - Risk config / AI Control Panel config.
    - Audit trail of halts/resumes.

### 2.2 Data Flow Summary
1. Scheduler gathers data → writes `snapshot_*` tables.
2. Strategy Engine evaluates strategies against newest snapshot → creates trade ideas.
3. Risk/Autonomy Gate evaluates each idea:
   - If auto-executable, calls MT5 Connector.
   - Else marks “Needs approval.”
4. Backend writes Decision History records with references to snapshot IDs.
5. Frontend pulls:
   - Active Trade Ideas table.
   - AI Control Panel (live config + halted reason).
   - Decision History stream.

### 2.3 Architecture Diagram (Mermaid)

```mermaid
flowchart LR
    subgraph Frontend (Next.js/React)
        UI_Dashboard[Dashboard]
        UI_AIPanel[AI Control Panel]
        UI_ActiveIdeas[Active Trade Ideas]
        UI_History[Decision History]
        UI_Settings[Settings & Risk Config]
    end

    subgraph Backend API (FastAPI)
        API_Risk[Risk & Autonomy Gate]
        API_Strategy[Strategy Manager]
        API_AI[AI Reasoning Orchestrator]
        API_MT5Proxy[MT5 Order Orchestrator]
        API_History[Decision History Logger]
        API_Config[Config/Risk Store]
    end

    subgraph Worker (Scheduler)
        JOB_Data[Snapshot Collector]
        JOB_Indicators[Indicator Calc]
        JOB_Calendar[Calendar / News Fetch]
        JOB_Account[Account Snapshot]
        JOB_StrategyEval[Strategy Evaluation Loop]
    end

    subgraph MT5 Connector Service
        MT5_Read[Get Bal/Equity/Positions]
        MT5_Trade[Place/Close Orders]
    end

    subgraph Postgres
        DB_snapshots[(snapshots_* tables)]
        DB_strategies[(strategies)]
        DB_tradeideas[(trade_ideas)]
        DB_history[(decision_history)]
        DB_risk[(risk_config)]
        DB_accounts[(account_state)]
    end

    UI_Dashboard -->|REST| Backend API
    UI_AIPanel -->|REST| Backend API
    UI_ActiveIdeas -->|REST| Backend API
    UI_History -->|REST| Backend API
    UI_Settings -->|REST| Backend API

    Backend API -->|SQL| Postgres
    Worker -->|SQL| Postgres

    JOB_StrategyEval --> API_AI
    API_AI -->|OpenAI call| AIModel[(OpenAI)]
    API_AI --> API_Risk
    API_Risk --> API_MT5Proxy
    API_MT5Proxy --> MT5_Trade
    MT5_Read --> Worker
    Worker --> DB_snapshots

    API_History --> DB_history
    API_Config --> DB_risk
```

---

## 3. Technology Stack Specification

### 3.1 Frontend
- **Framework:** Next.js 15 (React 19, App Router)
- **Language:** TypeScript
- **UI Toolkit / Styling:**
  - Tailwind CSS 3.x
  - shadcn/ui for consistent dark-theme inputs, tables, tooltips
  - lucide-react for icons
- **State / Data Fetch:**
  - React Query (TanStack Query) for server data caching
- **Charts / Visualization:**
  - Recharts for sparkline P/L, confidence gauges
- **Auth:**
  - JWT stored in httpOnly secure cookie
  - Middleware route protection in Next.js

### 3.2 Backend
- **Framework:** FastAPI (Python 3.12)
- **Auth:** JWT (HS256 or RS256)
- **Background Jobs / Scheduler:** Celery + Redis
  - Celery beat for cron-like schedules
- **Orchestration Between Services:**
  - Internal REST calls (Backend API ↔ MT5 Connector)
  - Or direct async client inside same cluster/VPC

### 3.3 MT5 Connector Service
- **Language:** Python 3.12
- **Library:** MetaTrader5 Python package (official-ish bridge commonly used for MT5 terminals)
- **Role:** Wraps trading functions (order_send, positions_get, account_info) behind a REST surface consumed by Backend.
- **Runtime:** Runs on a host with authenticated access to the AvaTrade MT5 account session.
  - Future improvement: deploy in same secure container environment with MT5 terminal / bridge running headless via Wine on Linux, or Windows container. For now assume dedicated VM running Windows Server with MT5 terminal logged in.

### 3.4 Database
- **DB:** PostgreSQL 16
- **Migrations:** Alembic
- **ORM:** SQLAlchemy 2.x (async-friendly)

### 3.5 AI / LLM
- **Provider:** OpenAI API
- **Usage in this system:**
  - Turn strategy rules + snapshot context → draft trade idea rationale in plain English.
  - Assign heuristic confidence score (LLM helps reason about confluence, but final numeric score is deterministic and reproducible — see Appendix).
  - Generate Decision History explanations.

### 3.6 Hosting / Runtime
- **Containerization:** Docker / Docker Compose for local dev
- **Prod Orchestration:** Kubernetes (K3s or managed K8s like EKS/GKE/AKS)
- **Secrets Management:**  
  - Environment variables pulled from K8s Secrets / Vault
  - Never commit live MT5 creds or OpenAI keys in repo

### 3.7 Versions (baseline)
- Node.js 20 LTS  
- Python 3.12  
- FastAPI 0.115+  
- Celery 5.x  
- Redis 7.x  
- PostgreSQL 16.x  
- Next.js 15 / React 19  
- Tailwind 3.x

---

## 4. Implementation Specifications

This section maps business requirements → concrete components.

### 4.1 Frontend Pages / Routes
All frontend pages are protected (must be authenticated) except `/login`.

#### `/login`
- Auth form (email + password for now).
- On success: set httpOnly cookie with JWT.
- Redirect: `/dashboard`.

#### `/dashboard`
Shows:
- Account summary from MT5:
  - Balance / Equity / Margin Available / Open P&L / #Open Positions.
- Daily running P/L vs target.
- Watched symbols panel:
  - Symbol
  - Spread / ATR snapshot / % move today
- Open positions table (live).

Needs:
- Replace collapsed sidebar “dots” with lucide-react icons + Tailwind tooltip.
- Show “AI Trading: ON/OFF” badge at top-right for high-signal status.

#### `/analysis`
(“Analysis & Performance”)
- Range selector: Today / This Week / This Month / Custom.
- Cards:
  - Total P/L (range)
  - Win rate
  - Avg RR
  - Weekly progress vs target (e.g. R2 000/week)
- Closed trades table (from MT5 history).
- Small P/L over time chart (Recharts).

#### `/data`
(“Third Party & Data”)
Tabs:
1. Economic Calendar  
   - Time (UTC + local)
   - Currency / Instrument relevance
   - Impact level (High = highlighted badge)
   - Previous / Forecast / Actual
2. Market News  
   - Timestamp
   - Headline
   - Symbol relevance (if tagged)
3. RSS Feeds  
   - Timestamp
   - Source
   - Headline
4. Indicators  
   - Latest RSI / SMA / MACD / ATR per watched symbol & timeframe

All of that comes from DB snapshots.

#### `/settings`
Tabs:
1. Accounts  
   - Show AvaTrade MT5 connection status.
   - Display account number / server.
   - Button: “Refresh account info now.”
2. API Integrations  
   - Enter OpenAI API key.
   - Button: “Test Connection.”
     - Should show green “AI online” or red “Invalid key / Unreachable” instead of 404.
3. Appearance  
   - Dark theme is fine for v1.
4. Risk Management  
   - Max lot size per trade.
   - Max concurrent trades.
   - Daily profit target.
   - Max daily drawdown.
   - “Stop new trades after hitting target?” toggle.
   - “Stop trading if drawdown breached?” toggle.
   - “Allow off-watchlist auto trades?” toggle.
   - These persist to `risk_config` and drive enforcement.

#### `/ai-trading`
Tabs:
1. Overview  
   - **AI Control Panel Card (ALWAYS visible at top)**  
     - AI Trading Enabled: ON/OFF toggle (kill switch)
     - Confidence Threshold %
     - Daily/Weekly profit goal
     - Max Drawdown limit
     - Max concurrent trades
     - Halt reason (if OFF because system halted)
   - Form inputs in this screen MUST use dark theme (Tailwind + shadcn/ui) with visible text.
   - **Active Trade Ideas Table**  
     Columns:
     - Symbol
     - Direction (BUY/SELL)
     - Entry / SL / TP
     - Confidence %
     - Rationale (short)
     - Status (Waiting / Needs approval / Auto-executed / Rejected / Halted by risk)
     - Action buttons:
       - APPROVE (if Needs approval)
       - REJECT
   - Clicking a row opens Manual Evaluation modal.

2. Strategies  
   - List of strategies.
   - Each strategy:
     - Name
     - Status ON/OFF toggle
     - Allowed symbols
     - Session rules
     - RR expectations
     - Risk caps for this strategy
     - “Forbidden conditions” list (e.g. high-impact USD news 5m pre/post)
   - Button to edit structured rule JSON.

   The backend will only generate trade ideas that match at least one ACTIVE strategy.

3. Decision History  
   - Chronological list.
   - Columns:
     - Timestamp
     - Symbol
     - Action (AI proposed BUY / AI auto-executed SELL / Human approved BUY / AI halted due to drawdown / etc.)
     - Confidence at the time
     - Risk check result
   - Filters:
     - Symbol filter
     - Action type filter
   - Clicking an entry opens Snapshot Replay View:
     - Show indicators, calendar events, account state at that timestamp.
     - Show rationale text.
     - Show which strategy triggered it.

### 4.2 Backend Services

#### 4.2.1 Snapshot Collector (Scheduler job)
- Runs on Celery beat every N seconds/minutes.
- Tasks:
  - Pull candles for watched symbols and compute indicators.
  - Pull economic calendar feed (high/med/low impact; forecast/previous/actual).
  - Pull news + RSS feeds.
  - Pull account state (balance, equity, margin, exposure) via MT5 Connector.
- Writes to:
  - `snapshot_market`
  - `snapshot_indicators`
  - `snapshot_calendar`
  - `snapshot_news`
  - `snapshot_account`

Each record stamped with `captured_at`.

#### 4.2.2 Strategy Evaluation Job
- Runs on short interval (ex: every 1 min).
- Steps:
  1. Load active strategies from `strategies`.
  2. Load latest snapshots for each symbol.
  3. For each active strategy:
     - Check if setup conditions are present.
     - Check forbidden conditions (e.g. “high-impact USD news in next 2 min”).
     - If valid, build a trade idea:
       - symbol, direction, entry zone, SL, TP, intended hold
       - which_strategy_id
       - rationale draft (structured bullets)
  4. Call AI Reasoning Orchestrator for:
     - Human-readable rationale paragraph
     - Confidence score suggestion
  5. Run Risk & Autonomy Gate (below).
  6. Persist:
     - Trade idea row in `trade_ideas`.
     - Decision History event.

#### 4.2.3 Risk & Autonomy Gate
- Reads:
  - Global AI Control Panel config (`risk_config` / `ai_control_config`)
  - Per-strategy caps
  - Account snapshot
- Checks:
  - AI Trading Enabled?
  - Daily profit target reached? If “stop after target” is on, then block new trades.
  - Max drawdown breached? If configured to halt on breach, flip system to halted.
  - Lot size <= allowed.
  - Concurrent trades < allowed.
  - Confidence ≥ threshold.
- Results:
  - If pass & autonomous allowed → call MT5 order placement.
  - Else if partial pass → mark idea “Needs approval.”
  - Else → mark idea “Rejected for risk.”
- Always write Decision History with “why.”

#### 4.2.4 Manual Evaluation
- When a human clicks APPROVE in UI:
  - Backend re-validates lot size / exposure (to prevent stale violations).
  - If valid: send order to MT5 Connector, mark as executed, log “Human override executed.”
  - If invalid: return error to UI (“Cannot approve: exceeds max concurrent trades”).
  - Always log in Decision History with snapshot reference and human override flag.

### 4.3 UI/UX Fixes Required
- Sidebar collapsed state:
  - Use lucide-react icons.
  - Tailwind tooltip on hover to show section label instead of anonymous dots.
- AI Trading > Overview form inputs:
  - Replace unreadable white-on-light with shadcn/ui `<Input />`, `<Select />`, `<Toggle />` using `bg-neutral-800 text-neutral-100`.
- AI Control Panel summary header:
  - Show:
    - AI Trading: ON/OFF
    - If OFF due to halt -> “OFF (Daily target reached)” or “OFF (Max drawdown breached)”
    - Confidence Threshold %
    - Max Concurrent Trades
- Active Trade Ideas table:
  - Add status badge colors:
    - Auto-executed = green badge
    - Needs approval = yellow badge
    - Rejected / Halted by risk = red badge
  - Row click → Manual Evaluation modal.
- Decision History page:
  - Add filters + snapshot replay drawer.

---

## 5. Database Design

We’re using PostgreSQL 16. All timestamps `TIMESTAMPTZ`.

### 5.1 Tables

#### 5.1.1 `strategies`
Stores machine-readable strategy definitions.

```sql
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    allowed_symbols TEXT[] NOT NULL,              -- ['XAUUSD','US30','EURUSD']
    session_windows JSONB NOT NULL,               -- [{ "start":"07:00Z","end":"11:00Z","days":["Mon","Tue","Wed","Thu","Fri"] }]
    entry_conditions JSONB NOT NULL,              -- structured indicator/price action rules
    exit_rules JSONB NOT NULL,                    -- { "stop_loss":"swing_low - 5 pips", "take_profit":"RR>=2", "time_limit_min":30 }
    forbidden_conditions JSONB NOT NULL,          -- e.g. { "block_high_impact_news_minutes":5, "blocked_symbols_during_news":["USD","GBP"] }
    risk_caps JSONB NOT NULL,                     -- { "max_lot_size":1.0, "max_concurrent_positions":2 }
    rr_expectation NUMERIC(5,2) NOT NULL,         -- expected RR, e.g. 2.0
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 5.1.2 `risk_config`
Global AI Control Panel + Risk Management inputs.

```sql
CREATE TABLE risk_config (
    id BOOLEAN PRIMARY KEY DEFAULT TRUE,          -- always single row with id=true
    ai_trading_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    min_confidence_threshold NUMERIC(5,2) NOT NULL DEFAULT 90.0,   -- %
    max_lot_size NUMERIC(10,2) NOT NULL,                          -- e.g. 1.00 lots
    max_concurrent_trades INT NOT NULL,
    daily_profit_target NUMERIC(12,2) NOT NULL,                   -- account currency
    stop_after_target BOOLEAN NOT NULL DEFAULT TRUE,
    max_drawdown_amount NUMERIC(12,2) NOT NULL,
    halt_on_drawdown BOOLEAN NOT NULL DEFAULT TRUE,
    allow_off_watchlist_autotrade BOOLEAN NOT NULL DEFAULT FALSE,
    last_halt_reason TEXT,                                        -- NULL if not halted
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 5.1.3 `snapshot_market`
Raw candle data.

```sql
CREATE TABLE snapshot_market (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,                                         -- 'XAUUSD'
    timeframe TEXT NOT NULL,                                      -- 'M1','M5','H1'
    open NUMERIC(18,6) NOT NULL,
    high NUMERIC(18,6) NOT NULL,
    low NUMERIC(18,6) NOT NULL,
    close NUMERIC(18,6) NOT NULL,
    volume BIGINT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL                              -- when we fetched/saw it
);
CREATE INDEX ON snapshot_market (symbol, timeframe, captured_at DESC);
```

#### 5.1.4 `snapshot_indicators`
Computed indicators for each symbol/timeframe at capture time.

```sql
CREATE TABLE snapshot_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    rsi_14 NUMERIC(6,2),
    sma_50 NUMERIC(18,6),
    sma_200 NUMERIC(18,6),
    macd JSONB,                                                   -- { "macd":..., "signal":..., "hist":... }
    atr NUMERIC(18,6),
    captured_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ON snapshot_indicators (symbol, timeframe, captured_at DESC);
```

#### 5.1.5 `snapshot_calendar`
Upcoming macro events (economic calendar).

```sql
CREATE TABLE snapshot_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_time TIMESTAMPTZ NOT NULL,                              -- scheduled release time
    currency TEXT NOT NULL,                                       -- 'USD','GBP','EUR'
    impact_level TEXT NOT NULL,                                   -- 'low','medium','high'
    title TEXT NOT NULL,                                          -- 'FOMC Rate Decision'
    previous_value TEXT,
    forecast_value TEXT,
    actual_value TEXT,
    captured_at TIMESTAMPTZ NOT NULL                              -- when we pulled this data
);
CREATE INDEX ON snapshot_calendar (currency, event_time);
CREATE INDEX ON snapshot_calendar (captured_at DESC);
```

#### 5.1.6 `snapshot_news`
News + RSS merged feed.

```sql
CREATE TABLE snapshot_news (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    headline TEXT NOT NULL,
    source TEXT NOT NULL,
    symbols TEXT[] DEFAULT '{}',                                  -- ['XAUUSD','USD','DXY']
    published_at TIMESTAMPTZ NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ON snapshot_news (published_at DESC);
```

#### 5.1.7 `snapshot_account`
Account state snapshot from MT5.

```sql
CREATE TABLE snapshot_account (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    balance NUMERIC(18,2) NOT NULL,
    equity NUMERIC(18,2) NOT NULL,
    margin_used NUMERIC(18,2) NOT NULL,
    margin_free NUMERIC(18,2) NOT NULL,
    open_pl NUMERIC(18,2) NOT NULL,
    open_positions INT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ON snapshot_account (captured_at DESC);
```

#### 5.1.8 `trade_ideas`
Current + historical AI proposals.

```sql
CREATE TYPE trade_idea_status AS ENUM (
    'waiting',
    'needs_approval',
    'auto_executed',
    'rejected',
    'halted_by_risk'
);

CREATE TABLE trade_ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('buy','sell')),
    entry_price NUMERIC(18,6),
    entry_range NUMERIC[] ,                                       -- [low, high] if zone
    stop_loss NUMERIC(18,6) NOT NULL,
    take_profit NUMERIC[] NOT NULL,                               -- can hold multiple TP targets
    expected_hold TEXT,                                           -- "scalp_30m", "swing_1d"
    rationale TEXT NOT NULL,                                      -- plain English summary for UI
    confidence_score NUMERIC(5,2) NOT NULL,                       -- 0-100
    status trade_idea_status NOT NULL,
    strategy_id UUID REFERENCES strategies(id),
    snapshot_ref UUID NOT NULL,                                   -- pointer to snapshot set used
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON trade_ideas (status);
CREATE INDEX ON trade_ideas (symbol, created_at DESC);
```

#### 5.1.9 `decision_history`
Full audit trail.

```sql
CREATE TYPE decision_action AS ENUM (
    'ai_proposed',
    'ai_auto_executed',
    'human_approved',
    'human_rejected',
    'risk_rejected',
    'ai_halted',
    'ai_resumed'
);

CREATE TABLE decision_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbol TEXT,                                                  -- nullable for global halt/resume
    action decision_action NOT NULL,
    rationale TEXT NOT NULL,                                      -- why we did / didn't act
    confidence_score NUMERIC(5,2),
    risk_check_result TEXT,                                       -- "pass","fail:max_drawdown","fail:lot_size"
    strategy_id UUID REFERENCES strategies(id),
    trade_idea_id UUID REFERENCES trade_ideas(id),
    snapshot_ref UUID,                                            -- same snapshot_ref as the idea
    human_override BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX ON decision_history (occurred_at DESC);
CREATE INDEX ON decision_history (symbol, occurred_at DESC);
CREATE INDEX ON decision_history (action, occurred_at DESC);
```

### 5.2 Snapshot Reference
`snapshot_ref` links a trade idea / decision to the captured world state.  
Implementation detail: `snapshot_ref` may be the `snapshot_account.id` (which is captured at the same time as indicators, news, etc.). We can also create a `snapshot_bundle` table to unify them if we want strict atomicity. For v1, we can record the most recent `snapshot_account.id` as the “bundle ID.”

---

## 6. API Specification

All API endpoints are authenticated using JWT in httpOnly cookie.

Base URL example (backend): `https://api.ai-trader.local/v1`

### 6.1 Auth
#### POST `/auth/login`
Request:
```json
{
  "email": "user@example.com",
  "password": "mypassword"
}
```
Response:
```json
{
  "status": "ok",
  "user": {
    "id": "b5f4...",
    "email": "user@example.com"
  }
}
```
- Sets secure httpOnly cookie `auth_token=<JWT>`.

### 6.2 Settings / Risk
#### GET `/settings/risk`
Returns current `risk_config`.

```json
{
  "ai_trading_enabled": true,
  "min_confidence_threshold": 90.0,
  "max_lot_size": 1.00,
  "max_concurrent_trades": 3,
  "daily_profit_target": 2000.00,
  "stop_after_target": true,
  "max_drawdown_amount": 1000.00,
  "halt_on_drawdown": true,
  "allow_off_watchlist_autotrade": false,
  "last_halt_reason": null
}
```

#### PUT `/settings/risk`
Updates config.  
Server must immediately enforce new values (live policy).

Request:
```json
{
  "ai_trading_enabled": false,
  "min_confidence_threshold": 92.5,
  "max_lot_size": 0.50,
  "max_concurrent_trades": 2,
  "daily_profit_target": 2000.00,
  "stop_after_target": true,
  "max_drawdown_amount": 800.00,
  "halt_on_drawdown": true,
  "allow_off_watchlist_autotrade": false
}
```

Response:
```json
{ "status": "ok" }
```

Also:  
When `ai_trading_enabled` flips from false→true or true→false, backend must create a `decision_history` record with `action = "ai_resumed"` or `"ai_halted"`.

### 6.3 Strategies
#### GET `/strategies`
Returns all strategies, including structured rule sets.

```json
[
  {
    "id": "54d3...",
    "name": "Gold Pullback Buy",
    "is_active": true,
    "allowed_symbols": ["XAUUSD"],
    "session_windows": [
      { "start":"07:00Z","end":"11:00Z","days":["Mon","Tue","Wed","Thu","Fri"] }
    ],
    "entry_conditions": {
      "trend_alignment": "bullish",
      "rsi_below": 40,
      "price_rejects_level": true
    },
    "exit_rules": {
      "stop_loss": "recent_swing_low - 50 cents",
      "take_profit": ["RR>=2", "key_resistance_zone"]
    },
    "forbidden_conditions": {
      "block_high_impact_news_minutes": 5,
      "blocked_symbols_during_news": ["USD"]
    },
    "risk_caps": {
      "max_lot_size": 1.0,
      "max_concurrent_positions": 2
    },
    "rr_expectation": 2.0
  }
]
```

#### PUT `/strategies/{id}`
Updates strategy rules (e.g. turn OFF a strategy).  
Backend validates shape (ensure required fields exist).

### 6.4 Active Trade Ideas
#### GET `/ai/ideas/active`
Returns most recent “open” ideas.

```json
[
  {
    "id": "e9a1...",
    "symbol": "XAUUSD",
    "direction": "buy",
    "entry_price": 2385.20,
    "stop_loss": 2378.50,
    "take_profit": [2398.00, 2402.00],
    "expected_hold": "scalp_30m",
    "rationale": "Gold pulled back into prior support during London session, RSI cooled to 38, bullish structure intact.",
    "confidence_score": 91.3,
    "status": "needs_approval"
  }
]
```

Status meanings:
- `needs_approval`: waiting on human click.
- `auto_executed`: already sent to MT5.
- `rejected`: blocked by risk.
- `halted_by_risk`: AI disabled / halted.

#### POST `/ai/ideas/{id}/approve`
- Human override/approval.
- Backend re-checks risk.
- If valid → place MT5 order via MT5 Connector.  
- Log Decision History with `action = "human_approved"`, `human_override = true`.

Request body:
```json
{ "lot_size": 0.5 }
```

Response:
```json
{
  "status": "executed",
  "mt5_order_id": 123456789
}
```

If blocked:
```json
{
  "status": "blocked",
  "reason": "max_concurrent_trades_exceeded"
}
```

#### POST `/ai/ideas/{id}/reject`
- Mark idea as rejected by human.
- Log `decision_history` with `action = "human_rejected"`.

### 6.5 Decision History
#### GET `/ai/history`
Query params:
- `symbol` (optional)
- `action` (optional)
- `limit` (default 100)

Response:
```json
[
  {
    "id": "c7a2...",
    "occurred_at": "2025-10-27T10:15:00Z",
    "symbol": "XAUUSD",
    "action": "ai_auto_executed",
    "rationale": "Strategy 'Gold Pullback Buy' matched. RSI 38 at support. No high-impact USD news in next 5m.",
    "confidence_score": 91.3,
    "risk_check_result": "pass",
    "strategy_id": "54d3...",
    "trade_idea_id": "e9a1...",
    "snapshot_ref": "9f0b...",
    "human_override": false
  }
]
```

#### GET `/ai/history/{id}/snapshot`
Returns the world state at that moment:
```json
{
  "market": {
    "symbol": "XAUUSD",
    "timeframe": "M15",
    "price": {
      "open": 2383.10,
      "high": 2386.00,
      "low": 2382.90,
      "close": 2385.20
    },
    "indicators": {
      "rsi_14": 38.2,
      "atr": 2.3
    }
  },
  "calendar": [
    {
      "event_time": "2025-10-27T11:00:00Z",
      "currency": "USD",
      "impact_level": "high",
      "title": "FOMC Rate Decision",
      "minutes_until_release": 45
    }
  ],
  "account": {
    "balance": 12000.00,
    "equity": 12250.00,
    "margin_free": 8000.00,
    "open_positions": 1
  }
}
```

### 6.6 MT5 Connector Proxy
These endpoints are internal-only (not exposed to frontend, only backend ↔ connector).

#### POST `/mt5/order`
```json
{
  "symbol": "XAUUSD",
  "direction": "buy",
  "lot_size": 0.50,
  "entry_type": "market",
  "stop_loss": 2378.50,
  "take_profit": [2398.00, 2402.00]
}
```
Response:
```json
{
  "status": "ok",
  "mt5_order_id": 123456789,
  "filled_price": 2385.30
}
```

#### GET `/mt5/account`
Response:
```json
{
  "balance": 12000.00,
  "equity": 12250.00,
  "margin_used": 4000.00,
  "margin_free": 8000.00,
  "open_pl": 250.00,
  "open_positions": [
    {
      "symbol": "XAUUSD",
      "direction": "buy",
      "lot_size": 0.50,
      "entry_price": 2380.00,
      "stop_loss": 2370.00,
      "take_profit": [2395.00, 2400.00],
      "unrealized_pl": 150.00
    }
  ],
  "history": [
    {
      "order_id": 123456789,
      "symbol": "XAUUSD",
      "direction": "buy",
      "closed_pl": 180.00,
      "opened_at": "2025-10-27T08:30:00Z",
      "closed_at": "2025-10-27T09:05:00Z"
    }
  ]
}
```

### 6.7 AI / OpenAI Integration
#### POST `/ai/test-connection`
Purpose: fix the 404 problem. This endpoint validates API key reachability.

Response (success):
```json
{
  "status": "ok",
  "message": "AI online"
}
```

Response (bad key):
```json
{
  "status": "error",
  "message": "Invalid OpenAI API key"
}
```

The backend does:
1. Confirm key exists in backend secret store.
2. Send a minimal “health” request (e.g. a `models.list` or a cheap tiny inference).
3. Interpret non-200 as invalid/unreachable, never surface raw 404.

---

## 7. Security Requirements

### 7.1 Authentication & Authorization
- JWT-based auth.
- httpOnly, Secure, SameSite=Strict cookie.
- Backend validates JWT on every request.
- RBAC v1 can be single-role (owner). Future: add read-only analyst role.

### 7.2 Secrets
- `OPENAI_API_KEY`, MT5 creds/server info, DB credentials stored only in:
  - Kubernetes Secrets / Vault in prod.
  - `.env.local` for dev (never committed).
- No secrets in frontend code. Frontend calls backend, backend calls OpenAI/MT5.

### 7.3 MT5 Credentials
- MT5/AvaTrade login creds must live in MT5 Connector VM/container only.
- Backend talks to MT5 Connector over an internal network (private service endpoint).
- MT5 Connector never exposes raw credentials.

### 7.4 Data Integrity / Audit
- `decision_history` is append-only. No UPDATE/DELETE from normal app flows.
- If a correction is absolutely needed (e.g. internal admin fix), we add a new `decision_history` row with `action="admin_note"` in future expansion rather than overwriting.

### 7.5 Input Validation
- All `PUT /settings/risk` inputs validated server-side:
  - Numeric ranges (confidence 0–100, lot_size >0, drawdown >=0).
  - Booleans enforced.
  - Strings sanitized.
- Strategy definitions validated against a strict JSON schema so malformed rules cannot crash evaluation.

### 7.6 Transport Security
- All communication HTTPS/TLS 1.2+.
- Internal service-to-service traffic (Backend ↔ MT5 Connector) ideally runs inside same private network / cluster namespace, not exposed publicly.

---

## 8. Testing Strategy

### 8.1 Unit Tests
- **Risk & Autonomy Gate logic:**
  - Given config (ai_trading_enabled=false) → idea must never auto-execute.
  - Given drawdown breach → gate returns “halted_by_risk”.
  - Given confidence below threshold → status “needs_approval”, not executed.

- **Strategy matching engine:**
  - If RSI < 40 and bullish structure and within session → should generate BUY idea.
  - If high-impact USD news <5m away and strategy forbids → should not generate idea.

- **Confidence score calculation:**
  - Deterministic numeric output for same inputs.

- **OpenAI health check endpoint:**
  - If mock returns 401 → response is `"Invalid OpenAI API key"` not 404.

### 8.2 Integration Tests
- Full “propose → approve → execute” path:
  1. Worker stores snapshot.
  2. StrategyEval job creates idea.
  3. Idea is marked “needs_approval”.
  4. Frontend calls `/ai/ideas/{id}/approve`.
  5. Backend calls mocked MT5 Connector, returns order_id.
  6. Decision History logs `human_approved`.

- Full “auto-execute” path:
  - ai_trading_enabled=true, confidence high, risk pass → backend hits MT5 Connector automatically and logs `ai_auto_executed`.

### 8.3 E2E / UI Tests
- Cypress/Playwright:
  - Sidebar collapse shows icons + tooltips, not dots.
  - AI Control Panel displays halt reason properly.
  - Risk Management form styling: dark theme inputs readable.
  - “Test Connection” in API Integrations shows human-readable status, not raw HTTP code.

### 8.4 Load / Performance Tests
- Snapshot ingestion at high frequency (e.g. every 5s for top 5 symbols) should not lock tables.
  - Verify DB indexes work.
- Decision History retrieval with filters should stay <200ms for recent data (with proper indexes on `occurred_at`, `symbol`).

---

## 9. Error Handling

### 9.1 Error Format (Backend REST)
All non-2xx responses follow:

```json
{
  "error": {
    "code": "RISK_VIOLATION",
    "message": "Max concurrent trades exceeded",
    "details": {
      "max_concurrent_trades": 2,
      "current_open_trades": 2
    }
  }
}
```

### 9.2 Error Code Enum (examples)
- `UNAUTHORIZED`
- `INVALID_INPUT`
- `RISK_VIOLATION`
- `STRATEGY_BLOCKED`
- `AI_HALTED`
- `MT5_EXECUTION_FAILED`
- `OPENAI_UNAVAILABLE`
- `SNAPSHOT_NOT_FOUND`

### 9.3 Logging
- All backend exceptions:
  - Logged with timestamp, request ID, user ID, endpoint, stack trace.
  - Sensitive values (API keys, creds) are redacted.

### 9.4 MT5 Execution Failures
If MT5 Connector returns a failure:
- We return `MT5_EXECUTION_FAILED`.
- We still write a `decision_history` record with `risk_check_result="fail:mt5_reject"` or similar so we have proof that AI tried, and MT5 declined.

### 9.5 AI Connector Failures
If OpenAI is unreachable:
- StrategyEval job must:
  - Still generate a minimal idea using deterministic logic.
  - Mark rationale as “LLM unavailable, fallback rationale.”
  - Confidence still computed deterministically.
  - Decision History logs `OPENAI_UNAVAILABLE` in rationale so audit shows degraded mode.

---

## 10. Performance & Scaling

### 10.1 Snapshot Frequency
- Candle/indicator snapshots and strategy evaluation can run every 60s initially.
- Economic calendar / high-impact events: 60s–300s.
- Account snapshot: 30s–60s.

These intervals are config-driven and stored in worker env vars:
- `SNAPSHOT_INTERVAL_SECONDS=60`
- `ACCOUNT_SNAPSHOT_INTERVAL_SECONDS=30`

### 10.2 Database Indexing
- `captured_at DESC` indexes on all snapshot tables.
- `(symbol, occurred_at DESC)` on `decision_history`.
- `(status)` on `trade_ideas` for “active ideas” queries.

### 10.3 Caching
- Frontend dashboard “account summary” can be cached in Redis for ~5s to avoid hammering MT5 Connector constantly.
- Economic calendar view can be cached 30–60s for UI.

### 10.4 Horizontal Scaling
- Backend API pods can scale horizontally behind a load balancer.
- Celery workers can scale horizontally for higher-frequency strategy evaluation.
- MT5 Connector is stateful (logged-in session). We treat it as a singleton service/VM with failover plan documented later.

---

## 11. Deployment & Configuration

### 11.1 Environments
- `dev`: Docker Compose locally.
- `staging`: K8s namespace `staging`.
- `prod`: K8s namespace `prod`.

### 11.2 Environment Variables (backend)
```bash
POSTGRES_URL=postgresql+asyncpg://trader:password@db:5432/ai_trader
JWT_SECRET=super-secret-signing-key
OPENAI_API_KEY=sk-...
MT5_CONNECTOR_URL=http://mt5-connector.internal:8080
SNAPSHOT_INTERVAL_SECONDS=60
ACCOUNT_SNAPSHOT_INTERVAL_SECONDS=30
```

### 11.3 Dockerfile (Backend FastAPI)
```Dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy src
COPY src /app/src

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.4 requirements.txt (backend excerpt)
```text
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.8.2
SQLAlchemy==2.0.32
asyncpg==0.29.0
alembic==1.13.2
python-jose==3.3.0
passlib[bcrypt]==1.7.4
redis==5.0.7
celery==5.4.0
httpx==0.27.0
```

### 11.5 Service Startup Order
1. Postgres
2. Redis
3. Backend API (FastAPI + Alembic migration on boot)
4. Celery worker & Celery beat
5. MT5 Connector service (must be reachable before auto-trading is enabled)

### 11.6 Halting in Production
When `halt_on_drawdown` triggers or `stop_after_target` triggers:
- Backend updates `risk_config.ai_trading_enabled = FALSE`
- Writes a `decision_history` row with `action="ai_halted"` and `last_halt_reason`
- Frontend AI Control Panel shows OFF + reason

Re-enabling requires PUT `/settings/risk` with `ai_trading_enabled=true` which:
- Logs `ai_resumed`

---

## 12. Integration Requirements

### 12.1 AvaTrade / MT5
We rely on:
- AvaTrade live MT5 account access.
- MT5 programmatic trading through an automated agent is a normal supported workflow in MT5 (“Expert Advisors” do rules-based execution and management automatically). AvaTrade promotes algorithmic trading and Expert Advisors and supports automated execution under predefined logic, including consistent order placement and trade management. This is exactly the behavior we’re replicating, but with explainability and human override where required. 

We must:
- Maintain a persistent authenticated MT5 session.
- Support:
  - Read account balance, equity, open positions, trade history.
  - Submit market and pending orders.
- Return broker execution info (order ID, fill price) back to backend for logging.

### 12.2 Economic Calendar Provider
Engineer must choose one provider that:
- Returns timestamped macro events with impact levels (high/med/low).
- Includes previous/forecast/actual.
- Allows polling via API or RSS-like feed with reasonable rate limits.
- We store these in `snapshot_calendar`.

This enables logic like:
- “Block GBPUSD trading 2 minutes pre-Bank of England rate decision.”
- “Mark rationale as ‘Avoiding USD longs pre-FOMC’ and include that in Decision History.”

### 12.3 News / RSS Provider
We ingest:
- Broker market commentary feeds.
- Finance news feeds.
- User-specified RSS feeds.

We normalize:
- `headline`
- `source`
- `published_at`
- Optional `symbols` tags.

These go into `snapshot_news`.

### 12.4 OpenAI
We use OpenAI for:
- Rationale generation.
- Natural-language explanation in Decision History.
- Confidence explanation.

We do NOT delegate final numeric risk gating to OpenAI. The numeric gate is deterministic and enforced in backend code.

### 12.5 Frontend Tooltips / Icons
We’ll use lucide-react icons for sidebar items:
- `layout-dashboard` for Dashboard
- `bar-chart-3` for Analysis
- `rss` for Third Party & Data
- `settings` for Settings
- `bot` for AI Trading

Collapsed sidebar shows icons. Hover uses shadcn/ui Tooltip component.

---

## 13. Code Quality Standards

### 13.1 Linting / Formatting
- **Backend:** `ruff` + `black` for Python.
- **Frontend:** ESLint + Prettier for TypeScript/React.
- CI must fail on lint errors.

### 13.2 Type Safety / Validation
- All FastAPI request bodies defined with Pydantic models.
- All responses typed.
- Frontend TypeScript models must match backend response schemas.

### 13.3 Logging & Observability
- Structured logs (JSON) for backend:
  - `timestamp`, `level`, `service`, `action`, `user_id`, `symbol`, `message`.
- Celery worker logs each job run + duration.
- MT5 Connector logs each order attempt and result.

### 13.4 PR / Review Rules
- No merge to `main` without:
  - Passing unit tests.
  - Passing lint.
  - Security review for any code that touches secrets, order execution logic, or Risk & Autonomy Gate.

### 13.5 Frontend UX Quality
- Dark theme readability is mandatory for all critical controls:
  - AI Trading Enabled toggle
  - Confidence Threshold
  - Drawdown / Daily target
- If inputs are unreadable, PR cannot merge.

---

## 14. Appendix

### 14.1 Confidence Score Heuristic v1
We need a reproducible 0–100 score so “≥90 = go” actually means something.

Algorithm outline:
1. **Strategy Match Score (0–50):**
   - Start 50.
   - For each required entry condition that fails → subtract fixed penalties.
   - For each “nice-to-have” that hits (e.g. confluence with higher timeframe trend) → add small bonus up to cap 50.

2. **Market Risk Score (0–25):**
   - If high-impact related news < X minutes away for this symbol’s currency → score = 0 for this section.
   - Else:
     - Lower volatility / clean structure → higher score.
     - Chaotic spike conditions → lower score.

3. **Account Comfort Score (0–25):**
   - If margin_free / equity is healthy, no overexposure in same symbol/direction → higher score.
   - If already heavily exposed to same symbol or same direction → lower score.

Final:
```text
confidence = StrategyMatch + MarketRisk + AccountComfort
cap at 100
```

Backend calculates this deterministically.  
LLM can generate human-readable explanation (“High score because RSI oversold aligns with bullish structure and no red news in next 5m”), but not the number itself.

### 14.2 Halt / Resume Logic
**Halt triggers:**
- Drawdown breach + `halt_on_drawdown=true`.
- Daily profit target reached + `stop_after_target=true`.

When halt triggers:
1. Backend sets `risk_config.ai_trading_enabled = FALSE`.
2. Backend sets `risk_config.last_halt_reason` to `"max_drawdown"` or `"daily_target_reached"`.
3. Backend logs `decision_history` row:
   - `action = "ai_halted"`
   - `symbol = null`
   - `rationale = "AI halted due to max_drawdown"`
   - `risk_check_result = "fail:max_drawdown"`

Frontend AI Control Panel shows:
- `AI Trading: OFF`
- `Reason: max_drawdown`
- This must be visually obvious.

**Resume:**
- Human toggles AI Trading back ON via `/settings/risk` (PUT).
- Backend:
  - Updates `ai_trading_enabled = TRUE`
  - Clears or updates `last_halt_reason`
  - Logs `decision_history` row:
    - `action = "ai_resumed"`
    - `rationale = "Human resumed after review"`

### 14.3 Manual Approval Flow Recap
1. Idea status = `needs_approval`
2. Human clicks APPROVE
3. Backend:
   - Re-checks:
     - max_concurrent_trades
     - max_lot_size
     - drawdown breach
     - session rules (still valid?)
   - If still good:
     - Place order via MT5 Connector
     - Update idea → `auto_executed`
     - Log `decision_history` (`action="human_approved"`, `human_override=true`)
   - If not good:
     - Return error to UI
     - Update idea → `rejected`
     - Log `decision_history` (`action="risk_rejected"`)

---

## Closing Position

This blueprint is production-grade.  
It defines:
- Architecture (frontend, backend, worker, MT5 connector, DB)
- Data model (snapshots, strategies, risk, ideas, decisions)
- Risk enforcement and kill switch behavior
- Confidence scoring logic
- API contract
- Deployment story
- Security model
- Required UI fixes for usability

This is the spec the engineering agent must now build against.
