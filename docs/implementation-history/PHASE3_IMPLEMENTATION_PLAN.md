# Phase 3: Advanced Features & Autonomy - Implementation Plan

## 📋 Overview

**Branch:** `feature/ai-integration-phase1`  
**Status:** Ready to begin  
**Prerequisites:** ✅ Phase 1 Complete, ✅ Phase 2 Complete, ✅ All 128 tests passing

Phase 3 focuses on implementing advanced AI trading features including trade idea execution, autonomy loop, performance tracking, and enhanced UI capabilities.

---

## 🎯 Phase 3 Objectives

### Primary Goals
1. **Trade Idea Execution** - Connect approved trade ideas to actual order placement
2. **Autonomy Loop** - Background scheduler for automated AI evaluations
3. **Position Management** - Automated SL/TP adjustments and breakeven moves
4. **Performance Tracking** - AI trade performance metrics and analytics
5. **Advanced UI Features** - Enhanced controls and monitoring capabilities

### Success Criteria
- ✅ Trade ideas can be approved and executed automatically
- ✅ Autonomy loop runs in background for enabled symbols
- ✅ Performance metrics tracked and displayed
- ✅ All safety controls maintained (rate limiting, daily loss limits)
- ✅ Semi-auto mode enforced (manual approval required by default)
- ✅ Comprehensive tests for all new features
- ✅ Documentation updated

---

## 📦 Phase 3 Components

### 3.1 Trade Idea Execution System

**Backend Components:**

#### `backend/ai/executor.py` (NEW)
**Purpose:** Execute approved trade ideas via MT5

**Key Functions:**
```python
async def execute_trade_idea(idea: TradeIdea, mt5_client: MT5Client) -> ExecutionResult:
    """Execute an approved trade idea."""
    # Validate idea is approved
    # Check daily loss limit
    # Validate volume against symbol_map.csv
    # Place order via mt5_client
    # Log execution result
    # Update idea status to 'executed'
    
async def validate_execution_safety(idea: TradeIdea) -> ValidationResult:
    """Validate trade idea meets all safety requirements."""
    # Check RR ratio >= min_rr
    # Verify volume within limits
    # Check daily loss not exceeded
    # Validate symbol is tradeable
    
async def calculate_position_size(idea: TradeIdea, account_balance: float) -> float:
    """Calculate position size based on risk percentage."""
    # Use risk % from execution plan
    # Calculate based on SL distance
    # Respect min/max volume limits
```

**API Endpoints:**
```python
POST /api/ai/trade-ideas/{id}/approve
POST /api/ai/trade-ideas/{id}/reject
POST /api/ai/trade-ideas/{id}/execute
GET  /api/ai/trade-ideas/pending
GET  /api/ai/trade-ideas/history
```

**Tests:**
- `tests/test_ai_executor.py` - Unit tests for execution logic
- `tests/test_ai_execution_api.py` - Integration tests for API endpoints

---

### 3.2 Autonomy Loop System

**Backend Components:**

#### `backend/ai/autonomy_loop.py` (ENHANCE)
**Purpose:** Background scheduler for automated AI evaluations

**Key Features:**
```python
class AutonomyLoop:
    """Background task runner for AI evaluations."""
    
    def __init__(self, engine: AIEngine, interval_minutes: int = 5):
        self.engine = engine
        self.interval = interval_minutes
        self.running = False
        self.enabled_symbols = {}  # {symbol: {timeframe, auto_execute}}
        
    async def start(self):
        """Start the autonomy loop."""
        # Begin background task
        # Evaluate enabled symbols every interval
        
    async def stop(self):
        """Stop the autonomy loop."""
        # Gracefully shutdown
        
    async def evaluate_all_symbols(self):
        """Run evaluation for all enabled symbols."""
        # For each enabled symbol:
        #   - Evaluate with AIEngine
        #   - Generate trade idea if conditions met
        #   - If auto_execute=True: execute immediately
        #   - If auto_execute=False: add to pending queue
        
    async def add_symbol(self, symbol: str, timeframe: str, auto_execute: bool):
        """Enable AI for a symbol."""
        
    async def remove_symbol(self, symbol: str):
        """Disable AI for a symbol."""
```

**API Endpoints:**
```python
POST /api/ai/autonomy/start
POST /api/ai/autonomy/stop
GET  /api/ai/autonomy/status
PUT  /api/ai/autonomy/interval  # Change evaluation interval
```

**Implementation Notes:**
- Use `asyncio.create_task()` for background execution
- Implement proper cancellation on shutdown
- Add error handling and retry logic
- Log all evaluation cycles
- Respect rate limiting (max 1 eval per symbol per interval)

**Tests:**
- `tests/test_autonomy_loop.py` - Unit tests for loop logic
- `tests/test_autonomy_api.py` - Integration tests for API

---

### 3.3 Position Management System

**Backend Components:**

#### `backend/ai/position_manager.py` (NEW)
**Purpose:** Automated position management for AI trades

**Key Features:**
```python
class PositionManager:
    """Manage AI-opened positions."""
    
    async def check_breakeven_conditions(self, position: Position) -> bool:
        """Check if position should move to breakeven."""
        # If profit >= 1.0 * ATR: move SL to entry
        
    async def check_partial_exit_conditions(self, position: Position) -> bool:
        """Check if partial profit should be taken."""
        # If profit >= 50% of TP: close 50% of position
        
    async def check_trailing_stop_conditions(self, position: Position) -> bool:
        """Check if trailing stop should be updated."""
        # If profit >= 2.0 * ATR: trail SL by 1.0 * ATR
        
    async def manage_all_positions(self):
        """Run management checks on all AI positions."""
        # Get all open positions
        # For each AI-opened position:
        #   - Check breakeven
        #   - Check partial exit
        #   - Check trailing stop
        #   - Execute modifications if needed
```

**API Endpoints:**
```python
GET  /api/ai/positions/managed
POST /api/ai/positions/{id}/breakeven
POST /api/ai/positions/{id}/trail-stop
```

**Configuration:**
```json
// config/ai/position_management.json
{
  "breakeven_trigger_atr": 1.0,
  "partial_exit_trigger_percent": 50,
  "partial_exit_amount_percent": 50,
  "trailing_stop_trigger_atr": 2.0,
  "trailing_stop_distance_atr": 1.0
}
```

**Tests:**
- `tests/test_position_manager.py` - Unit tests for management logic

---

### 3.4 Performance Tracking System

**Backend Components:**

#### `backend/ai/performance_tracker.py` (NEW)
**Purpose:** Track and analyze AI trading performance

**Key Features:**
```python
class PerformanceTracker:
    """Track AI trade performance metrics."""
    
    def record_trade_result(self, idea: TradeIdea, result: TradeResult):
        """Record completed trade result."""
        # Log to ai_performance.csv
        # Update running statistics
        
    def get_performance_metrics(self, symbol: str = None) -> PerformanceMetrics:
        """Get performance metrics."""
        # Win rate by confidence level
        # Average RR ratio
        # Profit factor
        # Max drawdown
        # Sharpe ratio (if enough data)
        
    def get_confidence_accuracy(self) -> Dict[int, float]:
        """Analyze confidence score accuracy."""
        # For each confidence bucket (0-20, 20-40, etc.):
        #   - Calculate actual win rate
        #   - Compare to expected
        
    def get_symbol_performance(self) -> List[SymbolPerformance]:
        """Get performance breakdown by symbol."""
        # Trades, wins, losses, profit, win rate per symbol
```

**Data Storage:**
```csv
# logs/ai_performance.csv
timestamp,symbol,timeframe,confidence,action,direction,entry,sl,tp,exit_price,profit,duration_minutes,result
```

**API Endpoints:**
```python
GET /api/ai/performance/overview
GET /api/ai/performance/by-symbol
GET /api/ai/performance/by-confidence
GET /api/ai/performance/accuracy
```

**Tests:**
- `tests/test_performance_tracker.py` - Unit tests for metrics calculation

---

### 3.5 Frontend Enhancements

**New Components:**

#### `src/components/ai/TradeIdeaApprovalDialog.tsx`
**Purpose:** Modal dialog for approving trade ideas with details

**Features:**
- Full trade idea details
- Risk calculation display
- Account impact preview
- Approve/Reject buttons
- Execution confirmation

#### `src/components/ai/AutonomyControls.tsx`
**Purpose:** Controls for autonomy loop

**Features:**
- Start/Stop autonomy loop
- Interval configuration
- Status indicator (running/stopped)
- Last evaluation timestamp
- Next evaluation countdown

#### `src/components/ai/PerformanceDashboard.tsx`
**Purpose:** AI performance analytics dashboard

**Features:**
- Overall metrics (win rate, profit factor, trades)
- Performance by symbol (table)
- Performance by confidence level (chart)
- Confidence accuracy analysis
- Recent trades list

#### `src/components/ai/PositionManagementPanel.tsx`
**Purpose:** Display AI-managed positions

**Features:**
- List of AI-opened positions
- Breakeven status
- Trailing stop status
- Manual override buttons
- P/L tracking

**Enhanced Components:**

#### `src/pages/AI.tsx` - Add 4th Tab
**New Tab:** "Performance"
- Performance dashboard
- Charts and metrics
- Export functionality

#### `src/components/ai/AIControlPanel.tsx` - Enhancements
- Add autonomy loop controls
- Show last evaluation time
- Display pending trade ideas count
- Add quick actions (evaluate all, approve all)

---

## 🔧 Implementation Order

### Week 1: Trade Idea Execution

**Day 1-2: Backend Executor**
- [ ] Create `backend/ai/executor.py`
- [ ] Implement `execute_trade_idea()`
- [ ] Implement `validate_execution_safety()`
- [ ] Implement `calculate_position_size()`
- [ ] Add execution API endpoints
- [ ] Write unit tests (`test_ai_executor.py`)

**Day 3-4: Frontend Execution UI**
- [ ] Create `TradeIdeaApprovalDialog.tsx`
- [ ] Update `TradeIdeaCard.tsx` to use dialog
- [ ] Add execution confirmation flow
- [ ] Add loading states and error handling
- [ ] Test with demo MT5 account

**Day 5: Integration & Testing**
- [ ] Integration tests for execution flow
- [ ] End-to-end test: evaluate → approve → execute
- [ ] Verify rate limiting respected
- [ ] Verify daily loss limits enforced
- [ ] Commit: "Phase 3: Trade Idea Execution System"

---

### Week 2: Autonomy Loop

**Day 1-2: Backend Autonomy Loop**
- [ ] Enhance `backend/ai/autonomy_loop.py`
- [ ] Implement `AutonomyLoop` class
- [ ] Add start/stop functionality
- [ ] Implement background task runner
- [ ] Add autonomy API endpoints
- [ ] Write unit tests (`test_autonomy_loop.py`)

**Day 3-4: Frontend Autonomy Controls**
- [ ] Create `AutonomyControls.tsx`
- [ ] Add to AI Control Panel
- [ ] Implement start/stop buttons
- [ ] Add interval configuration
- [ ] Add status monitoring
- [ ] Test autonomy loop with demo account

**Day 5: Integration & Testing**
- [ ] Integration tests for autonomy loop
- [ ] Test multi-symbol evaluation
- [ ] Verify interval timing
- [ ] Test graceful shutdown
- [ ] Commit: "Phase 3: Autonomy Loop Implementation"

---

### Week 3: Position Management & Performance

**Day 1-2: Position Management**
- [ ] Create `backend/ai/position_manager.py`
- [ ] Implement breakeven logic
- [ ] Implement partial exit logic
- [ ] Implement trailing stop logic
- [ ] Add position management API endpoints
- [ ] Write unit tests (`test_position_manager.py`)

**Day 3-4: Performance Tracking**
- [ ] Create `backend/ai/performance_tracker.py`
- [ ] Implement metrics calculation
- [ ] Create `logs/ai_performance.csv` schema
- [ ] Add performance API endpoints
- [ ] Write unit tests (`test_performance_tracker.py`)

**Day 5: Frontend Performance UI**
- [ ] Create `PerformanceDashboard.tsx`
- [ ] Create `PositionManagementPanel.tsx`
- [ ] Add Performance tab to AI page
- [ ] Add charts and visualizations
- [ ] Commit: "Phase 3: Position Management & Performance Tracking"

---

### Week 4: Polish & Documentation

**Day 1-2: UI Enhancements**
- [ ] Add notifications for AI events
- [ ] Add export functionality for performance data
- [ ] Add filters and search to decision history
- [ ] Improve loading states and animations
- [ ] Add keyboard shortcuts

**Day 3-4: Testing & Bug Fixes**
- [ ] Comprehensive integration testing
- [ ] Performance testing (load, stress)
- [ ] Fix any bugs found
- [ ] Optimize slow operations
- [ ] Verify all safety controls

**Day 5: Documentation**
- [ ] Create `PHASE3_COMPLETION_SUMMARY.md`
- [ ] Update `PHASE3_TESTING_GUIDE.md`
- [ ] Create user guide for AI features
- [ ] Update API documentation
- [ ] Create strategy creation guide
- [ ] Commit: "Phase 3: Documentation & Final Polish"

---

## 🧪 Testing Strategy

### Unit Tests
- All new modules have >80% coverage
- Mock MT5 client for executor tests
- Mock time for autonomy loop tests
- Test edge cases and error conditions

### Integration Tests
- Full execution flow (evaluate → approve → execute)
- Autonomy loop with multiple symbols
- Position management with real positions
- Performance tracking with historical data

### Manual Testing
- Test with demo MT5 account
- Verify all safety controls
- Test UI responsiveness
- Test error handling
- Verify rate limiting

---

## 🔒 Safety Controls

### Execution Safety
- ✅ RR ratio validation (min 2.0)
- ✅ Daily loss limit check
- ✅ Volume validation against symbol_map.csv
- ✅ Rate limiting (10 req/min for orders)
- ✅ Manual approval required (semi-auto mode)

### Autonomy Loop Safety
- ✅ Max 1 evaluation per symbol per interval
- ✅ Graceful shutdown on errors
- ✅ Kill switch stops all AI activity
- ✅ Respects session windows
- ✅ News embargo enforcement

### Position Management Safety
- ✅ Only manage AI-opened positions
- ✅ Never widen stop loss
- ✅ Breakeven only after profit
- ✅ Trailing stop only after significant profit
- ✅ Manual override available

---

## 📊 Success Metrics

### Technical Metrics
- All tests passing (target: >150 tests)
- Test coverage >80%
- API response time <500ms
- Frontend load time <2s
- Autonomy loop uptime >99%

### Trading Metrics
- Win rate >50% for confidence ≥75
- Average RR ratio ≥2.0
- Daily loss limit never exceeded
- Execution rate >95%
- Confidence accuracy within 10%

---

## 🚀 Deliverables

### Code
- 5 new backend modules (~800 lines)
- 4 new frontend components (~600 lines)
- 10+ new API endpoints
- 50+ new tests

### Documentation
- Phase 3 completion summary
- Testing guide
- User guide for AI features
- API documentation
- Strategy creation guide

### Features
- ✅ Trade idea execution
- ✅ Autonomy loop
- ✅ Position management
- ✅ Performance tracking
- ✅ Enhanced UI controls

---

## 📝 Notes

- All work continues on `feature/ai-integration-phase1` branch
- Commit incrementally with clear messages
- Test thoroughly before each commit
- Maintain backward compatibility
- Respect user preferences (semi-auto mode, demo account)
- Follow existing code patterns and styling

---

**Ready to begin Phase 3 implementation!** 🚀

