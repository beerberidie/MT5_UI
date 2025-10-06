# AI Trading System Integration Blueprint
**Project:** MT5_UI AI Trading Capabilities Integration  
**Date:** 2025-10-06  
**Status:** Analysis & Planning Phase

---

## Executive Summary

This blueprint outlines the integration of autonomous AI trading capabilities into the existing MT5_UI trading workstation. The integration will transform the current manual trading platform into a hybrid system supporting both manual and AI-driven trading operations.

### Current State
- **Frontend:** Vite React TypeScript application with shadcn-ui components
- **Backend:** FastAPI with MetaTrader5 Python integration
- **Features:** Manual trading, market watch, position management, historical data access
- **Infrastructure:** CSV-based data storage, rate limiting, basic risk management

### Target State
- **AI Trading Engine:** Autonomous strategy evaluation and execution
- **EMNR Rules System:** Entry/Exit/Strong/Weak condition evaluation
- **Confidence Scoring:** 0-100 scoring model for trade quality assessment
- **Scheduler:** Action planning based on confidence and risk parameters
- **Symbol Profiles:** Per-symbol knowledge base with session preferences
- **AI Dashboard:** Left sidebar AI section with monitoring and controls

### Integration Approach
**Hybrid Architecture:** Extend existing MT5_UI rather than replace, maintaining backward compatibility while adding AI capabilities as optional features that can be enabled/disabled per symbol.

---

## Phase 1: Analysis Results

### 1.1 Current MT5_UI Architecture

#### Backend Components (FastAPI)
- `backend/app.py` - Main API with 30+ endpoints
- `backend/mt5_client.py` - MT5 terminal integration wrapper
- `backend/risk.py` - Risk limits and symbol mapping
- `backend/csv_io.py` - CSV data persistence utilities
- `backend/models.py` - Pydantic request/response models
- `backend/config.py` - Environment configuration

#### Frontend Components (React + TypeScript)
- `src/pages/Index.tsx` - Main trading dashboard
- `src/pages/AI.tsx` - Placeholder AI page (minimal implementation)
- `src/pages/Analysis.tsx` - Performance analytics
- `src/pages/Settings.tsx` - User settings
- `src/components/TradingDashboard.tsx` - Core trading UI (950+ lines)
- `src/lib/api.ts` - API client functions
- `src/lib/settings-context.tsx` - Risk settings state management

#### Data Storage
- `config/` - Symbol maps, risk limits, session windows (CSV)
- `logs/` - Orders, errors, security events (CSV)
- `data/` - Account snapshots, bars, ticks, history (CSV)

#### Key Features
- Live MT5 market watch synchronization
- Market/pending order placement
- Position management with close functionality
- Historical bars and ticks retrieval
- Trading history and deals tracking
- Rate limiting (10 req/min orders, 100 req/min reads)
- Daily loss limit enforcement (currently disabled)
- Session window validation
- Volume validation and rounding
- API key authentication (optional)

### 1.2 AI Trading System Documentation Review

#### Core AI Components (from ai_trading_system_modular_light_revision/)
1. **EMNR Rules Engine** (`apps/strategy/emnr.py`)
   - Evaluates indicator-based conditions
   - Returns entry/exit/strong/weak flags
   - JSON-based rule definitions per symbol/timeframe

2. **Confidence Scoring** (`apps/strategy/confidence.py`)
   - Weights: entry(+30), strong(+25), weak(-15), exit(-40), align(+10)
   - News penalty support (-20 to -40)
   - Output: 0-100 score

3. **Action Scheduler** (`apps/strategy/scheduler.py`)
   - <60: observe only
   - 60-74: pending orders only
   - ≥75: market/pending orders (if RR ≥ min_rr)

4. **Autonomy Loop** (`apps/strategy/autonomy_loop.py`)
   - Orchestrates: fetch → evaluate → score → schedule → act → log

#### Data Structures
- **EMNR Schema:** Symbol/timeframe/sessions/indicators/conditions/strategy
- **Symbol Profile:** Best sessions, timeframes, drivers, style, management rules
- **Session Maps:** London, NY, Tokyo, Sydney (SAST timezone)

#### Key Concepts from Blueprints
- Walk-forward backtesting
- Risk budgets and kill switches
- Approval queue for semi-autonomous mode
- Experiment tracking and reproducibility
- Daily routines and health checks
- Drift detection and model retirement

### 1.3 Gap Analysis

#### Missing from Current MT5_UI
1. **AI Strategy Engine**
   - No EMNR rule evaluation
   - No confidence scoring model
   - No automated decision-making
   - No symbol profiling system

2. **Data Infrastructure**
   - No indicator calculation pipeline
   - No news/calendar integration
   - No macro data tracking (DXY, US10Y, VIX)
   - No daily market snapshot storage

3. **AI-Specific Risk Management**
   - No confidence-based position sizing
   - No RR (risk/reward) validation
   - No news embargo windows
   - No strategy invalidation monitoring

4. **Monitoring & Logging**
   - No AI decision audit trail
   - No trade idea logging
   - No confidence score history
   - No execution plan tracking

5. **UI Components**
   - AI page is placeholder only
   - No AI controls in sidebar
   - No confidence visualization
   - No strategy status indicators
   - No approval queue interface

#### Existing Components to Leverage
1. **MT5 Integration** - Fully functional, can be reused
2. **Order Execution** - Market/pending orders work well
3. **Risk Framework** - Daily loss limits, session windows, volume validation
4. **Rate Limiting** - Already implemented with slowapi
5. **CSV Storage** - Can extend for AI data
6. **API Authentication** - X-API-Key pattern established
7. **Frontend Architecture** - React Router, TanStack Query, shadcn-ui ready

#### Conflicts & Incompatibilities
1. **Minimal conflicts** - AI system is additive, not replacement
2. **Symbol mapping** - Need to align canonical symbols between systems
3. **Timezone handling** - AI docs use SAST, backend uses UTC (need conversion)
4. **Data format** - AI uses JSON schemas, backend uses CSV (need bridge)

---

## Phase 2: Implementation Blueprint

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Vite React Frontend                       │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │   Trading    │      AI      │      Analysis            │ │
│  │   Dashboard  │   Dashboard  │      & Settings          │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
│         │                │                    │              │
│         └────────────────┴────────────────────┘              │
│                          │                                   │
│                    API Client (api.ts)                       │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP/JSON
┌──────────────────────────┼───────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Existing Endpoints: /api/symbols, /api/order, etc.   │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  NEW AI Endpoints: /api/ai/*, /api/strategies/*       │ │
│  └────────────────────────────────────────────────────────┘ │
│         │                    │                               │
│  ┌──────┴──────┐      ┌──────┴──────────────────────────┐  │
│  │ MT5 Client  │      │   AI Strategy Engine (NEW)      │  │
│  │  (existing) │      │  - EMNR Evaluator               │  │
│  └─────────────┘      │  - Confidence Scorer            │  │
│                       │  - Action Scheduler             │  │
│                       │  - Indicator Calculator         │  │
│                       └─────────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │  CSV Files   │  AI Rules    │   AI Logs & History      │ │
│  │  (existing)  │  (JSON)      │   (CSV/JSON)             │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Components to Add

#### Backend - New Modules

**File: `backend/ai/__init__.py`**
- Package initialization

**File: `backend/ai/emnr.py`**
- Port from `ai_trading_system_modular_light_revision/apps/strategy/emnr.py`
- Evaluate entry/exit/strong/weak conditions
- Load rules from JSON files

**File: `backend/ai/confidence.py`**
- Port from `ai_trading_system_modular_light_revision/apps/strategy/confidence.py`
- Calculate 0-100 confidence scores
- Apply alignment bonuses and news penalties

**File: `backend/ai/scheduler.py`**
- Port from `ai_trading_system_modular_light_revision/apps/strategy/scheduler.py`
- Map confidence to actions (observe/pending_only/open_or_scale)
- Apply RR validation

**File: `backend/ai/autonomy_loop.py`**
- Port from `ai_trading_system_modular_light_revision/apps/strategy/autonomy_loop.py`
- Orchestrate full evaluation cycle
- Return trade ideas with execution plans

**File: `backend/ai/indicators.py`** (NEW)
- Calculate EMA, RSI, MACD, ATR from historical bars
- Use pandas for efficient computation
- Cache recent calculations

**File: `backend/ai/symbol_profiles.py`** (NEW)
- Load/save symbol profile JSON files
- Validate against schema
- Provide defaults for unconfigured symbols

**File: `backend/ai/rules_manager.py`** (NEW)
- Load/save EMNR rule JSON files
- Validate against schema
- CRUD operations for rules

**File: `backend/ai/ai_logger.py`** (NEW)
- Log AI decisions to CSV
- Track: timestamp, symbol, confidence, action, trade_idea, execution_plan
- Separate from order logs

**File: `backend/ai_routes.py`** (NEW)
- AI-specific API endpoints
- Mount to main app

#### Backend - New API Endpoints

```python
# Strategy Management
GET    /api/ai/strategies                    # List all symbol strategies
GET    /api/ai/strategies/{symbol}           # Get strategy for symbol
POST   /api/ai/strategies/{symbol}           # Create/update strategy
DELETE /api/ai/strategies/{symbol}           # Delete strategy

# Symbol Profiles
GET    /api/ai/profiles                      # List all profiles
GET    /api/ai/profiles/{symbol}             # Get profile for symbol
POST   /api/ai/profiles/{symbol}             # Create/update profile
DELETE /api/ai/profiles/{symbol}             # Delete profile

# AI Evaluation
POST   /api/ai/evaluate/{symbol}             # Run evaluation cycle for symbol
POST   /api/ai/evaluate/batch                # Run for multiple symbols
GET    /api/ai/status                        # Get AI engine status

# AI Decisions & History
GET    /api/ai/decisions                     # Recent AI decisions
GET    /api/ai/decisions/{symbol}            # Decisions for specific symbol
GET    /api/ai/trade-ideas                   # Active trade ideas

# AI Controls
POST   /api/ai/enable/{symbol}               # Enable AI for symbol
POST   /api/ai/disable/{symbol}              # Disable AI for symbol
POST   /api/ai/kill-switch                   # Emergency stop all AI trading
GET    /api/ai/enabled-symbols               # List AI-enabled symbols

# Indicators (for debugging/display)
GET    /api/ai/indicators/{symbol}           # Get current indicator values
```

#### Frontend - New Components

**File: `src/components/ai/AIControlPanel.tsx`**
- Enable/disable AI per symbol
- Kill switch button
- AI engine status indicator
- Confidence threshold controls

**File: `src/components/ai/StrategyEditor.tsx`**
- EMNR rule editor (JSON or form-based)
- Indicator parameter configuration
- Save/load strategies

**File: `src/components/ai/SymbolProfileEditor.tsx`**
- Edit symbol profiles
- Session preferences
- RR targets, risk percentages
- Management rules (breakeven, trailing)

**File: `src/components/ai/TradeIdeasPanel.tsx`**
- Display active trade ideas
- Show confidence scores
- Execution plan details
- Approve/reject buttons (for semi-auto mode)

**File: `src/components/ai/AIDecisionLog.tsx`**
- Table of recent AI decisions
- Filter by symbol, date, confidence
- Export functionality

**File: `src/components/ai/ConfidenceGauge.tsx`**
- Visual confidence score display (0-100)
- Color-coded by threshold (red <60, yellow 60-74, green ≥75)

**File: `src/components/ai/IndicatorDisplay.tsx`**
- Show current indicator values for symbol
- EMA trends, RSI, MACD status
- ATR for volatility

#### Frontend - Modified Components

**File: `src/components/TradingDashboard.tsx`**
- Add AI indicator badges to symbol rows
- Show AI-enabled status
- Display confidence scores inline

**File: `src/pages/AI.tsx`**
- Replace placeholder with full AI dashboard
- Layout: Control panel + Trade ideas + Decision log
- Real-time updates via polling or SSE

**File: `src/lib/api.ts`**
- Add AI endpoint functions
- Type definitions for AI responses

#### Data Files - New Structure

```
config/
  ai/
    strategies/
      EURUSD_H1.json          # EMNR rules per symbol/timeframe
      XAUUSD_H1.json
      ...
    profiles/
      EURUSD.json             # Symbol profiles
      XAUUSD.json
      ...
    settings.json             # Global AI settings

logs/
  ai_decisions.csv            # AI decision audit trail
  ai_trade_ideas.csv          # Trade idea history
  ai_errors.csv               # AI-specific errors

data/
  ai/
    indicators/
      EURUSD_H1_latest.json   # Cached indicator values
      ...
```

### 2.3 Components to Modify

**File: `backend/app.py`**
- Import and mount AI routes
- Add AI-specific middleware if needed
- Extend health check to include AI status

**File: `backend/models.py`**
- Add Pydantic models for AI requests/responses
- EMNRRules, SymbolProfile, TradeIdea, AIDecision, etc.

**File: `backend/risk.py`**
- Add function to load AI-specific risk settings
- Integrate confidence-based position sizing

**File: `backend/csv_io.py`**
- Add JSON file I/O utilities
- Validation helpers for AI schemas

**File: `requirements.txt`**
- Add: `ta-lib` or `pandas-ta` for indicators (optional, can use custom)
- Add: `schedule` for autonomy loop timing
- Add: `jsonschema` for validation

**File: `tradecraft-console-main/tradecraft-console-main/src/App.tsx`**
- No changes needed (routes already support /ai)

**File: `tradecraft-console-main/tradecraft-console-main/src/components/TradingDashboard.tsx`**
- Add AI status badges to symbol list
- Add confidence score column (optional)
- Add "AI" button to enable/disable per symbol

### 2.4 Components to Delete

**None** - This is an additive integration. All existing components remain functional.

### 2.5 Components to Rewrite

**None** - Existing components work well. Only extensions needed.

---

## Phase 3: Data Flow Diagrams

### 3.1 AI Evaluation Cycle

```
1. User enables AI for EURUSD on H1 timeframe
   ↓
2. Frontend: POST /api/ai/enable/EURUSD
   ↓
3. Backend: Load EURUSD_H1.json strategy rules
   ↓
4. Autonomy Loop (every N minutes):
   a. Fetch latest H1 bars from MT5
   b. Calculate indicators (EMA, RSI, MACD, ATR)
   c. Evaluate EMNR conditions → {entry, exit, strong, weak}
   d. Calculate confidence score (0-100)
   e. Check alignment (trend/timeframe/session)
   f. Apply news penalty if in embargo window
   g. Scheduler determines action
   h. If action = "open_or_scale":
      - Validate RR ratio
      - Check daily loss limit
      - Calculate position size
      - POST /api/order (existing endpoint)
   i. Log decision to ai_decisions.csv
   ↓
5. Frontend polls /api/ai/decisions
   ↓
6. Display in AI Dashboard with confidence gauge
```

### 3.2 Manual Override Flow

```
1. AI generates trade idea (confidence 78)
   ↓
2. User sees in Trade Ideas panel
   ↓
3. User clicks "Reject" button
   ↓
4. Frontend: POST /api/ai/trade-ideas/{id}/reject
   ↓
5. Backend: Mark idea as rejected, skip execution
   ↓
6. Log override to ai_decisions.csv
```

### 3.3 Kill Switch Flow

```
1. User clicks "KILL SWITCH" button
   ↓
2. Frontend: POST /api/ai/kill-switch
   ↓
3. Backend:
   a. Disable AI for all symbols
   b. Cancel pending AI orders
   c. Optionally close AI positions (configurable)
   d. Log kill switch event
   ↓
4. Frontend: Show "AI DISABLED" banner
```

---

## Phase 4: UI/UX Changes

### 4.1 Left Sidebar Addition

**Current Sidebar:**
- Dashboard (active)
- Analysis
- Settings

**New Sidebar:**
- Dashboard (active)
- **AI Trader** ← NEW
- Analysis
- Settings

### 4.2 AI Page Layout

```
┌─────────────────────────────────────────────────────────┐
│  AI Trader                                    [KILL SW] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─ AI Control Panel ─────────────────────────────────┐ │
│  │  Engine Status: ● ACTIVE                           │ │
│  │  Enabled Symbols: EURUSD, XAUUSD (2/23)            │ │
│  │  Confidence Threshold: [====|====] 75              │ │
│  │  Mode: ○ Full Auto  ● Semi-Auto  ○ Observe Only   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─ Active Trade Ideas ───────────────────────────────┐ │
│  │  Symbol  │ Conf │ Action      │ RR  │ Controls    │ │
│  │  EURUSD  │  78  │ BUY 0.02    │ 2.5 │ [✓] [✗]    │ │
│  │  XAUUSD  │  82  │ SELL 0.01   │ 3.0 │ [✓] [✗]    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─ Recent Decisions ─────────────────────────────────┐ │
│  │  Time     │ Symbol │ Conf │ Action    │ Result    │ │
│  │  14:23:15 │ EURUSD │  78  │ BUY       │ Executed  │ │
│  │  14:18:42 │ XAUUSD │  62  │ Observe   │ Skipped   │ │
│  │  14:15:10 │ EURUSD │  45  │ Observe   │ Skipped   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Trading Dashboard Enhancements

Add AI badges to symbol rows:
```
EURUSD    1.0850  ↑0.12%  [AI: 78]  [BUY] [SELL]
XAUUSD    2650.30 ↓0.05%  [AI: --]  [BUY] [SELL]
```

### 4.4 Dark Theme Consistency

All AI components follow existing dark theme:
- Background: `bg-background`
- Panels: `bg-panel`
- Borders: `border-border`
- Text: `text-text-primary`, `text-text-secondary`
- Confidence colors: Red (<60), Yellow (60-74), Green (≥75)

---

## Phase 5: Dependencies

### 5.1 Python Backend

**Add to `requirements.txt`:**
```
# AI Trading Dependencies
pandas-ta==0.3.14b0         # Technical indicators (alternative to ta-lib)
schedule==1.2.0             # Autonomy loop scheduling
jsonschema==4.19.0          # JSON validation
python-dateutil==2.8.2      # Timezone handling
```

**Optional (if using TA-Lib):**
```
TA-Lib==0.4.28              # Requires binary installation
```

### 5.2 Frontend

**No new dependencies needed** - All required packages already installed:
- React, TypeScript, TanStack Query
- shadcn-ui components
- lucide-react icons

---

## Phase 6: Security & Risk Management

### 6.1 AI-Specific Risk Controls

1. **Confidence Thresholds**
   - Minimum confidence for execution (default: 75)
   - Configurable per symbol

2. **RR Validation**
   - Minimum RR ratio (default: 2.0)
   - Reject trades below threshold

3. **News Embargo**
   - Block trading N minutes before/after high-impact news
   - Configurable embargo window (default: 30 min)

4. **Daily Loss Limits**
   - Leverage existing `_check_daily_loss_limit()`
   - Apply to AI trades same as manual

5. **Position Limits**
   - Max concurrent AI positions (default: 3)
   - Max positions per symbol (default: 1)

6. **Volume Limits**
   - Max volume per AI trade (default: 0.01 lots for demo)
   - Leverage existing volume validation

7. **Kill Switch**
   - Immediate halt of all AI activity
   - Logged with timestamp and reason
   - Requires manual re-enable

### 6.2 Authentication

- AI endpoints use same `require_api_key` dependency
- Rate limiting: 10 req/min for AI execution, 100 req/min for reads

### 6.3 Audit Trail

All AI decisions logged with:
- Timestamp (UTC)
- Symbol, timeframe
- Indicator values
- EMNR flags (entry/exit/strong/weak)
- Confidence score
- Action taken
- Execution result
- User overrides

---

## Phase 7: Testing Strategy

### 7.1 Unit Tests

**Backend:**
- `tests/test_ai_emnr.py` - EMNR evaluation logic
- `tests/test_ai_confidence.py` - Confidence scoring
- `tests/test_ai_scheduler.py` - Action scheduling
- `tests/test_ai_indicators.py` - Indicator calculations
- `tests/test_ai_routes.py` - API endpoints

**Frontend:**
- `tests/ai/AIControlPanel.test.tsx`
- `tests/ai/TradeIdeasPanel.test.tsx`
- `tests/ai/ConfidenceGauge.test.tsx`

### 7.2 Integration Tests

- Full evaluation cycle (fetch → evaluate → execute)
- Kill switch functionality
- Manual override flow
- Multi-symbol concurrent evaluation

### 7.3 E2E Tests (Playwright)

- Enable AI for symbol via UI
- View trade ideas
- Approve/reject trade idea
- Trigger kill switch
- View decision log

### 7.4 Demo Account Testing

- All AI trades use demo MT5 account
- Test volume: 0.01 lots
- Test symbols: EURUSD, XAUUSD initially
- Monitor for 1 week before expanding

---

## Phase 8: Implementation Phases

### Phase 8.1: Foundation (Week 1)
**Priority: HIGH**

1. Create backend AI module structure
   - `backend/ai/__init__.py`
   - Port EMNR, confidence, scheduler modules
   - Add indicators.py with basic EMA/RSI/MACD

2. Create data directories
   - `config/ai/strategies/`
   - `config/ai/profiles/`
   - `logs/ai_decisions.csv`

3. Add Pydantic models for AI
   - EMNRRules, SymbolProfile, TradeIdea, AIDecision

4. Create first AI endpoint
   - `POST /api/ai/evaluate/{symbol}` - Manual evaluation trigger

5. Unit tests for core AI logic

**Deliverable:** Backend can evaluate a symbol and return confidence score

### Phase 8.2: API Layer (Week 2)
**Priority: HIGH**

1. Implement all AI endpoints
   - Strategy CRUD
   - Profile CRUD
   - Evaluation endpoints
   - Decision history
   - Control endpoints (enable/disable/kill-switch)

2. Add AI logging
   - ai_decisions.csv writer
   - ai_trade_ideas.csv writer

3. Integration with existing order flow
   - AI calls existing `/api/order` endpoint
   - Respect all existing risk checks

4. Integration tests

**Deliverable:** Full AI API functional, tested with Postman/curl

### Phase 8.3: Frontend Foundation (Week 3)
**Priority: MEDIUM**

1. Create AI components
   - AIControlPanel
   - TradeIdeasPanel
   - AIDecisionLog
   - ConfidenceGauge

2. Update api.ts with AI functions

3. Rebuild AI.tsx page with real components

4. Add AI nav item to sidebar

**Deliverable:** AI page displays real data, controls work

### Phase 8.4: Dashboard Integration (Week 4)
**Priority: MEDIUM**

1. Add AI badges to TradingDashboard symbol rows

2. Add enable/disable AI buttons per symbol

3. Real-time confidence updates

4. Polish UI/UX

**Deliverable:** Seamless AI integration in main dashboard

### Phase 8.5: Autonomy Loop (Week 5)
**Priority: MEDIUM**

1. Implement background scheduler
   - Run evaluation every N minutes for enabled symbols
   - Configurable interval (default: 5 min)

2. Add autonomy loop controls
   - Start/stop via API
   - Status monitoring

3. Semi-auto mode
   - Generate trade ideas
   - Wait for user approval
   - Execute on approval

**Deliverable:** AI can run autonomously in background

### Phase 8.6: Advanced Features (Week 6)
**Priority: LOW**

1. Strategy editor UI
   - JSON editor with validation
   - Form-based editor for non-technical users

2. Symbol profile editor UI

3. News embargo integration
   - Calendar API integration
   - Embargo window enforcement

4. Macro data tracking
   - DXY, US10Y, VIX integration
   - Display in AI dashboard

**Deliverable:** Full-featured AI trading system

### Phase 8.7: Testing & Refinement (Week 7)
**Priority: HIGH**

1. E2E tests with Playwright

2. Demo account live testing
   - 1 week observation
   - Monitor all AI decisions
   - Validate risk controls

3. Performance optimization
   - Indicator calculation caching
   - API response times

4. Documentation
   - User guide for AI features
   - API documentation
   - Strategy creation guide

**Deliverable:** Production-ready AI system

---

## Phase 9: Risk Assessment & Mitigation

### 9.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Indicator calculation errors | HIGH | MEDIUM | Extensive unit tests, validate against known values |
| MT5 connection failures during AI execution | HIGH | MEDIUM | Retry logic, fallback to manual mode, alerts |
| Race conditions in autonomy loop | MEDIUM | LOW | Use locks, single-threaded evaluation per symbol |
| JSON schema validation failures | MEDIUM | MEDIUM | Strict validation, default values, error logging |
| Frontend state sync issues | LOW | MEDIUM | Use TanStack Query for cache management |

### 9.2 Trading Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI executes bad trades | HIGH | MEDIUM | Start with low confidence threshold (80+), demo only |
| Runaway trading (too many orders) | HIGH | LOW | Rate limiting, position limits, kill switch |
| Daily loss limit exceeded | HIGH | LOW | Existing daily loss check, AI respects same limits |
| News event causes losses | MEDIUM | MEDIUM | News embargo windows, volatility filters |
| Strategy overfitting | MEDIUM | HIGH | Walk-forward testing, out-of-sample validation |

### 9.3 Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| User confusion with AI controls | MEDIUM | MEDIUM | Clear UI labels, tooltips, user guide |
| Accidental kill switch activation | LOW | LOW | Confirmation dialog, log all kill switch events |
| Strategy file corruption | MEDIUM | LOW | JSON validation, backups, version control |
| Log file growth | LOW | HIGH | Log rotation, archival, cleanup scripts |

---

## Phase 10: Success Metrics

### 10.1 Technical Metrics

- **API Response Time:** <200ms for evaluation endpoints
- **Indicator Calculation:** <100ms for 120 bars
- **Frontend Load Time:** <2s for AI page
- **Test Coverage:** >80% for AI modules
- **Uptime:** 99%+ for autonomy loop

### 10.2 Trading Metrics

- **Confidence Accuracy:** Track actual vs predicted outcomes
- **Win Rate:** Target >50% for confidence ≥75
- **RR Ratio:** Average ≥2.0 for executed trades
- **Daily Loss:** Never exceed configured limit
- **Execution Rate:** <5% rejected orders

### 10.3 User Experience Metrics

- **Time to Enable AI:** <2 minutes for first symbol
- **Strategy Creation:** <10 minutes for basic strategy
- **Decision Visibility:** Real-time updates (<5s latency)
- **Override Response:** Instant UI feedback

---

## Appendix A: File-by-File Change List

### Files to Create (Backend)

1. `backend/ai/__init__.py` - Package init
2. `backend/ai/emnr.py` - EMNR evaluator (port from ai_trading_system)
3. `backend/ai/confidence.py` - Confidence scorer (port from ai_trading_system)
4. `backend/ai/scheduler.py` - Action scheduler (port from ai_trading_system)
5. `backend/ai/autonomy_loop.py` - Orchestration (port from ai_trading_system)
6. `backend/ai/indicators.py` - Indicator calculations (NEW)
7. `backend/ai/symbol_profiles.py` - Profile management (NEW)
8. `backend/ai/rules_manager.py` - EMNR rules CRUD (NEW)
9. `backend/ai/ai_logger.py` - AI-specific logging (NEW)
10. `backend/ai_routes.py` - AI API endpoints (NEW)
11. `tests/test_ai_emnr.py` - Unit tests
12. `tests/test_ai_confidence.py` - Unit tests
13. `tests/test_ai_scheduler.py` - Unit tests
14. `tests/test_ai_indicators.py` - Unit tests
15. `tests/test_ai_routes.py` - Integration tests

### Files to Create (Frontend)

1. `src/components/ai/AIControlPanel.tsx` - Main AI controls
2. `src/components/ai/StrategyEditor.tsx` - Strategy editor
3. `src/components/ai/SymbolProfileEditor.tsx` - Profile editor
4. `src/components/ai/TradeIdeasPanel.tsx` - Trade ideas display
5. `src/components/ai/AIDecisionLog.tsx` - Decision history
6. `src/components/ai/ConfidenceGauge.tsx` - Confidence visualization
7. `src/components/ai/IndicatorDisplay.tsx` - Indicator values
8. `tests/ai/AIControlPanel.test.tsx` - Component tests
9. `tests/ai/TradeIdeasPanel.test.tsx` - Component tests
10. `tests/ai/ConfidenceGauge.test.tsx` - Component tests

### Files to Modify (Backend)

1. `backend/app.py` - Mount AI routes, extend health check
2. `backend/models.py` - Add AI Pydantic models
3. `backend/risk.py` - Add AI risk settings loader
4. `backend/csv_io.py` - Add JSON I/O utilities
5. `requirements.txt` - Add AI dependencies

### Files to Modify (Frontend)

1. `src/pages/AI.tsx` - Replace placeholder with full dashboard
2. `src/lib/api.ts` - Add AI endpoint functions
3. `src/components/TradingDashboard.tsx` - Add AI badges and controls

### Data Files to Create

1. `config/ai/strategies/EURUSD_H1.json` - Example strategy
2. `config/ai/strategies/XAUUSD_H1.json` - Example strategy
3. `config/ai/profiles/EURUSD.json` - Example profile
4. `config/ai/profiles/XAUUSD.json` - Example profile
5. `config/ai/settings.json` - Global AI settings
6. `logs/ai_decisions.csv` - Decision audit trail
7. `logs/ai_trade_ideas.csv` - Trade idea history
8. `logs/ai_errors.csv` - AI-specific errors

---

## Appendix B: Estimated Complexity

| Component | Lines of Code | Complexity | Time Estimate |
|-----------|---------------|------------|---------------|
| Backend AI modules | ~800 | Medium | 3 days |
| Backend AI routes | ~400 | Medium | 2 days |
| Backend tests | ~600 | Low | 2 days |
| Frontend AI components | ~1200 | Medium | 4 days |
| Frontend tests | ~400 | Low | 1 day |
| Dashboard integration | ~200 | Low | 1 day |
| Autonomy loop | ~300 | High | 2 days |
| Documentation | N/A | Low | 2 days |
| **Total** | **~3900** | **Medium** | **17 days** |

**Note:** Estimates assume 1 developer working full-time. Actual time may vary based on testing iterations and refinements.

---

## Appendix C: Next Steps

1. **Review this blueprint** with stakeholders
2. **Prioritize phases** based on business needs
3. **Set up development environment** with AI dependencies
4. **Create first strategy** for EURUSD as proof of concept
5. **Implement Phase 8.1** (Foundation) and validate
6. **Iterate** through remaining phases
7. **Test extensively** on demo account before any live consideration

---

**End of Blueprint**

