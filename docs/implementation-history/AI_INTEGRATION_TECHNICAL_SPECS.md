# AI Trading Integration - Technical Specifications

**Companion Document to:** AI_TRADING_INTEGRATION_BLUEPRINT.md  
**Date:** 2025-10-06

---

## 1. Data Schemas

### 1.1 EMNR Strategy Schema

**File:** `config/ai/strategies/{SYMBOL}_{TIMEFRAME}.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "symbol": "EURUSD",
  "timeframe": "H1",
  "sessions": ["London", "NewYork"],
  "indicators": {
    "ema": {
      "fast": 20,
      "slow": 50
    },
    "rsi": {
      "period": 14,
      "overbought": 70,
      "oversold": 30
    },
    "macd": {
      "fast": 12,
      "slow": 26,
      "signal": 9
    },
    "atr": {
      "period": 14,
      "multiplier": 1.5
    }
  },
  "conditions": {
    "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
    "exit": ["rsi_gt_70", "price_close_lt_ema_slow"],
    "strong": ["macd_hist_gt_0", "atr_above_median"],
    "weak": ["long_upper_wick", "divergence_bearish"]
  },
  "strategy": {
    "direction": "long",
    "min_rr": 2.0,
    "news_embargo_minutes": 30,
    "invalidations": ["close_below_ema_slow", "macro_contra_surge"]
  }
}
```

### 1.2 Symbol Profile Schema

**File:** `config/ai/profiles/{SYMBOL}.json`

```json
{
  "symbol": "EURUSD",
  "bestSessions": ["London", "NewYork"],
  "bestTimeframes": ["M15", "H1", "H4"],
  "externalDrivers": ["DXY", "US10Y", "FED_SPEECHES"],
  "style": {
    "bias": "trend-follow",
    "rrTarget": 2.0,
    "maxRiskPct": 0.03
  },
  "management": {
    "breakevenAfterRR": 1.0,
    "partialAtRR": 1.5,
    "trailUsingATR": true,
    "atrMultiplier": 1.5
  },
  "invalidations": ["close_below_ema_slow", "macro_contra_surge"]
}
```

### 1.3 AI Settings Schema

**File:** `config/ai/settings.json`

```json
{
  "enabled": true,
  "mode": "semi-auto",
  "evaluation_interval_seconds": 300,
  "confidence_threshold": 75,
  "min_rr_ratio": 2.0,
  "max_concurrent_positions": 3,
  "max_positions_per_symbol": 1,
  "default_risk_pct": 0.01,
  "news_embargo_minutes": 30,
  "timezone": "Africa/Johannesburg",
  "sessions": {
    "London": {"start": "09:00", "end": "17:30"},
    "NewYork": {"start": "14:30", "end": "22:00"},
    "Tokyo": {"start": "02:00", "end": "10:00"},
    "Sydney": {"start": "00:00", "end": "08:00"}
  }
}
```

### 1.4 Trade Idea Schema

```json
{
  "id": "uuid-v4",
  "timestamp": "2025-10-06T14:23:15.123Z",
  "symbol": "EURUSD",
  "timeframe": "H1",
  "confidence": 78,
  "action": "open_or_scale",
  "direction": "buy",
  "entry_price": 1.0850,
  "stop_loss": 1.0820,
  "take_profit": 1.0910,
  "volume": 0.02,
  "rr_ratio": 2.5,
  "emnr_flags": {
    "entry": true,
    "exit": false,
    "strong": true,
    "weak": false
  },
  "indicators": {
    "ema_fast": 1.0845,
    "ema_slow": 1.0830,
    "rsi": 55,
    "macd_hist": 0.0005,
    "atr": 0.0025
  },
  "execution_plan": {
    "action": "open_or_scale",
    "riskPct": "0.02"
  },
  "status": "pending_approval",
  "approved_by": null,
  "executed_at": null,
  "result": null
}
```

### 1.5 AI Decision Log Schema

**File:** `logs/ai_decisions.csv`

```csv
timestamp,symbol,timeframe,confidence,action,direction,entry,sl,tp,volume,rr,emnr_entry,emnr_exit,emnr_strong,emnr_weak,status,result,error
2025-10-06T14:23:15.123Z,EURUSD,H1,78,open_or_scale,buy,1.0850,1.0820,1.0910,0.02,2.5,true,false,true,false,executed,pending,
2025-10-06T14:18:42.456Z,XAUUSD,H1,62,pending_only,sell,2650.30,2655.00,2640.00,0.01,2.0,true,false,false,false,skipped,,
2025-10-06T14:15:10.789Z,EURUSD,H1,45,observe,,,,,,,false,false,false,false,skipped,,
```

---

## 2. API Specifications

### 2.1 Pydantic Models

**File:** `backend/models.py` (additions)

```python
from typing import Literal, Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

# EMNR Strategy Models
class IndicatorConfig(BaseModel):
    ema: Optional[Dict[str, int]] = None
    rsi: Optional[Dict[str, Any]] = None
    macd: Optional[Dict[str, int]] = None
    atr: Optional[Dict[str, Any]] = None

class StrategyConfig(BaseModel):
    direction: Literal["long", "short", "both"]
    min_rr: float = Field(default=2.0, ge=1.0)
    news_embargo_minutes: int = Field(default=30, ge=0)
    invalidations: List[str] = []

class EMNRRules(BaseModel):
    symbol: str
    timeframe: Literal["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    sessions: List[Literal["London", "NewYork", "Tokyo", "Sydney"]]
    indicators: IndicatorConfig
    conditions: Dict[str, List[str]]  # entry, exit, strong, weak
    strategy: StrategyConfig

# Symbol Profile Models
class StyleConfig(BaseModel):
    bias: Literal["trend-follow", "mean-revert", "breakout"]
    rrTarget: float = Field(default=2.0, ge=1.0)
    maxRiskPct: float = Field(default=0.03, ge=0.001, le=0.1)

class ManagementConfig(BaseModel):
    breakevenAfterRR: float = Field(default=1.0, ge=0)
    partialAtRR: float = Field(default=1.5, ge=0)
    trailUsingATR: bool = True
    atrMultiplier: float = Field(default=1.5, ge=0.5)

class SymbolProfile(BaseModel):
    symbol: str
    bestSessions: List[str]
    bestTimeframes: List[str]
    externalDrivers: List[str]
    style: StyleConfig
    management: ManagementConfig
    invalidations: List[str]

# Trade Idea Models
class EMNRFlags(BaseModel):
    entry: bool
    exit: bool
    strong: bool
    weak: bool

class IndicatorValues(BaseModel):
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    rsi: Optional[float] = None
    macd_hist: Optional[float] = None
    atr: Optional[float] = None

class ExecutionPlan(BaseModel):
    action: Literal["observe", "pending_only", "open_or_scale", "wait_rr"]
    riskPct: str

class TradeIdea(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    timeframe: str
    confidence: int = Field(ge=0, le=100)
    action: str
    direction: Optional[Literal["buy", "sell"]] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    volume: Optional[float] = None
    rr_ratio: Optional[float] = None
    emnr_flags: EMNRFlags
    indicators: IndicatorValues
    execution_plan: ExecutionPlan
    status: Literal["pending_approval", "approved", "rejected", "executed", "cancelled"]
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    result: Optional[str] = None

# AI Decision Models
class AIDecision(BaseModel):
    timestamp: datetime
    symbol: str
    timeframe: str
    confidence: int
    action: str
    direction: Optional[str] = None
    entry: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    volume: Optional[float] = None
    rr: Optional[float] = None
    emnr_entry: bool
    emnr_exit: bool
    emnr_strong: bool
    emnr_weak: bool
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

# Request/Response Models
class EvaluateRequest(BaseModel):
    symbol: str
    timeframe: str = "H1"
    force: bool = False  # Force evaluation even if recently evaluated

class EvaluateResponse(BaseModel):
    trade_idea: Optional[TradeIdea] = None
    confidence: int
    action: str
    message: str

class AIStatusResponse(BaseModel):
    enabled: bool
    mode: str
    enabled_symbols: List[str]
    active_trade_ideas: int
    last_evaluation: Optional[datetime] = None
    autonomy_loop_running: bool

class EnableAIRequest(BaseModel):
    timeframe: str = "H1"
    auto_execute: bool = False  # If false, requires approval
```

### 2.2 API Endpoint Details

#### POST /api/ai/evaluate/{symbol}

**Request:**
```json
{
  "timeframe": "H1",
  "force": false
}
```

**Response (200):**
```json
{
  "trade_idea": {
    "id": "abc-123",
    "timestamp": "2025-10-06T14:23:15.123Z",
    "symbol": "EURUSD",
    "confidence": 78,
    "action": "open_or_scale",
    "direction": "buy",
    "entry_price": 1.0850,
    "stop_loss": 1.0820,
    "take_profit": 1.0910,
    "volume": 0.02,
    "rr_ratio": 2.5,
    ...
  },
  "confidence": 78,
  "action": "open_or_scale",
  "message": "Trade idea generated. Awaiting approval."
}
```

**Response (409 - Low Confidence):**
```json
{
  "trade_idea": null,
  "confidence": 45,
  "action": "observe",
  "message": "Confidence below threshold. No action taken."
}
```

#### GET /api/ai/status

**Response (200):**
```json
{
  "enabled": true,
  "mode": "semi-auto",
  "enabled_symbols": ["EURUSD", "XAUUSD"],
  "active_trade_ideas": 2,
  "last_evaluation": "2025-10-06T14:23:15.123Z",
  "autonomy_loop_running": true
}
```

#### POST /api/ai/kill-switch

**Request:** Empty body or optional reason
```json
{
  "reason": "Market volatility spike"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "AI trading disabled for all symbols",
  "disabled_symbols": ["EURUSD", "XAUUSD"],
  "cancelled_trade_ideas": 2,
  "timestamp": "2025-10-06T14:30:00.000Z"
}
```

---

## 3. Indicator Calculation Specifications

### 3.1 EMA (Exponential Moving Average)

```python
def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    Calculate EMA using pandas for efficiency.
    
    Args:
        prices: List of closing prices
        period: EMA period (e.g., 20, 50)
    
    Returns:
        List of EMA values (same length as prices, NaN for initial values)
    """
    import pandas as pd
    series = pd.Series(prices)
    ema = series.ewm(span=period, adjust=False).mean()
    return ema.tolist()

# Usage
closes = [1.0850, 1.0855, 1.0860, ...]  # From historical bars
ema_20 = calculate_ema(closes, 20)
ema_50 = calculate_ema(closes, 50)

# Condition: ema_fast_gt_slow
ema_fast_gt_slow = ema_20[-1] > ema_50[-1]
```

### 3.2 RSI (Relative Strength Index)

```python
def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    Calculate RSI using pandas.
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
    
    Returns:
        List of RSI values (0-100)
    """
    import pandas as pd
    series = pd.Series(prices)
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

# Usage
closes = [1.0850, 1.0855, ...]
rsi = calculate_rsi(closes, 14)

# Conditions
rsi_lt_30 = rsi[-1] < 30  # Oversold
rsi_gt_70 = rsi[-1] > 70  # Overbought
rsi_between_40_60 = 40 <= rsi[-1] <= 60  # Neutral zone
```

### 3.3 MACD (Moving Average Convergence Divergence)

```python
def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
    """
    Calculate MACD, signal line, and histogram.
    
    Returns:
        Dict with 'macd', 'signal', 'histogram' keys
    """
    import pandas as pd
    series = pd.Series(prices)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.tolist(),
        'signal': signal_line.tolist(),
        'histogram': histogram.tolist()
    }

# Usage
closes = [1.0850, 1.0855, ...]
macd_data = calculate_macd(closes)

# Conditions
macd_hist_gt_0 = macd_data['histogram'][-1] > 0  # Bullish
macd_hist_lt_0 = macd_data['histogram'][-1] < 0  # Bearish
```

### 3.4 ATR (Average True Range)

```python
def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
    """
    Calculate ATR from OHLC bars.
    
    Args:
        bars: List of dicts with 'high', 'low', 'close' keys
        period: ATR period (default 14)
    
    Returns:
        List of ATR values
    """
    import pandas as pd
    df = pd.DataFrame(bars)
    
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr.tolist()

# Usage
bars = [
    {'high': 1.0860, 'low': 1.0840, 'close': 1.0850},
    {'high': 1.0870, 'low': 1.0845, 'close': 1.0865},
    ...
]
atr = calculate_atr(bars, 14)

# Conditions
atr_median = sorted(atr[-50:])[ len(atr[-50:]) // 2 ]  # Median of last 50
atr_above_median = atr[-1] > atr_median
```

---

## 4. Condition Evaluation Logic

### 4.1 Fact Generation

```python
def generate_facts(bars: List[Dict], indicators: IndicatorConfig) -> Dict[str, bool]:
    """
    Generate boolean facts from indicator values.
    
    Args:
        bars: Historical OHLC bars
        indicators: Indicator configuration from strategy
    
    Returns:
        Dict of condition_name -> bool
    """
    closes = [b['close'] for b in bars]
    
    facts = {}
    
    # EMA facts
    if indicators.ema:
        ema_fast = calculate_ema(closes, indicators.ema['fast'])
        ema_slow = calculate_ema(closes, indicators.ema['slow'])
        facts['ema_fast_gt_slow'] = ema_fast[-1] > ema_slow[-1]
        facts['ema_fast_lt_slow'] = ema_fast[-1] < ema_slow[-1]
        facts['price_above_ema_fast'] = closes[-1] > ema_fast[-1]
        facts['price_below_ema_fast'] = closes[-1] < ema_fast[-1]
        facts['price_close_lt_ema_slow'] = closes[-1] < ema_slow[-1]
    
    # RSI facts
    if indicators.rsi:
        rsi = calculate_rsi(closes, indicators.rsi['period'])
        facts['rsi_lt_30'] = rsi[-1] < indicators.rsi['oversold']
        facts['rsi_gt_70'] = rsi[-1] > indicators.rsi['overbought']
        facts['rsi_between_40_60'] = 40 <= rsi[-1] <= 60
    
    # MACD facts
    if indicators.macd:
        macd_data = calculate_macd(closes, indicators.macd['fast'], indicators.macd['slow'], indicators.macd['signal'])
        facts['macd_hist_gt_0'] = macd_data['histogram'][-1] > 0
        facts['macd_hist_lt_0'] = macd_data['histogram'][-1] < 0
    
    # ATR facts
    if indicators.atr:
        atr = calculate_atr(bars, indicators.atr['period'])
        atr_median = sorted(atr[-50:])[ len(atr[-50:]) // 2 ]
        facts['atr_above_median'] = atr[-1] > atr_median
        facts['atr_below_median'] = atr[-1] < atr_median
    
    # Candlestick pattern facts (simplified)
    last_bar = bars[-1]
    body = abs(last_bar['close'] - last_bar['open'])
    upper_wick = last_bar['high'] - max(last_bar['open'], last_bar['close'])
    lower_wick = min(last_bar['open'], last_bar['close']) - last_bar['low']
    
    facts['long_upper_wick'] = upper_wick > body * 2
    facts['long_lower_wick'] = lower_wick > body * 2
    
    # Divergence (requires more complex logic, placeholder)
    facts['divergence_bearish'] = False  # TODO: Implement
    facts['divergence_bullish'] = False  # TODO: Implement
    
    return facts
```

### 4.2 EMNR Evaluation

```python
def evaluate_emnr(facts: Dict[str, bool], rules: EMNRRules) -> EMNRFlags:
    """
    Evaluate EMNR conditions based on facts.
    
    Args:
        facts: Dict of condition_name -> bool
        rules: EMNR strategy rules
    
    Returns:
        EMNRFlags with entry/exit/strong/weak booleans
    """
    entry = all(facts.get(cond, False) for cond in rules.conditions.get('entry', []))
    exit = all(facts.get(cond, False) for cond in rules.conditions.get('exit', []))
    strong = all(facts.get(cond, False) for cond in rules.conditions.get('strong', []))
    weak = all(facts.get(cond, False) for cond in rules.conditions.get('weak', []))
    
    return EMNRFlags(entry=entry, exit=exit, strong=strong, weak=weak)
```

---

## 5. Confidence Scoring Logic

```python
WEIGHTS = {
    "entry": 30,
    "strong": 25,
    "weak": -15,
    "exit": -40,
    "align": 10
}

def calculate_confidence(
    emnr_flags: EMNRFlags,
    align_ok: bool,
    news_penalty: int = 0
) -> int:
    """
    Calculate confidence score (0-100).
    
    Args:
        emnr_flags: EMNR evaluation results
        align_ok: True if trend/timeframe/session aligned
        news_penalty: Negative penalty for news events (-20 to -40)
    
    Returns:
        Confidence score (0-100)
    """
    score = 0
    
    if emnr_flags.entry:
        score += WEIGHTS["entry"]
    if emnr_flags.strong:
        score += WEIGHTS["strong"]
    if emnr_flags.weak:
        score += WEIGHTS["weak"]
    if emnr_flags.exit:
        score += WEIGHTS["exit"]
    
    if align_ok:
        score += WEIGHTS["align"]
    
    score += news_penalty  # Negative value
    
    # Clamp to 0-100
    return max(0, min(100, score))
```

### 5.1 Alignment Check

```python
def check_alignment(
    symbol: str,
    timeframe: str,
    current_session: str,
    profile: SymbolProfile
) -> bool:
    """
    Check if current conditions align with symbol profile.
    
    Returns:
        True if timeframe and session are in best lists
    """
    timeframe_ok = timeframe in profile.bestTimeframes
    session_ok = current_session in profile.bestSessions
    
    return timeframe_ok and session_ok
```

---

## 6. Action Scheduling Logic

```python
def schedule_action(
    confidence: int,
    min_rr_ok: bool,
    risk_cap_pct: float = 0.03
) -> ExecutionPlan:
    """
    Determine action based on confidence and RR validation.
    
    Args:
        confidence: Confidence score (0-100)
        min_rr_ok: True if RR ratio meets minimum
        risk_cap_pct: Maximum risk percentage
    
    Returns:
        ExecutionPlan with action and risk percentage
    """
    if confidence < 60:
        return ExecutionPlan(action="observe", riskPct="0")
    
    if confidence < 75:
        return ExecutionPlan(
            action="pending_only",
            riskPct=f"{min(risk_cap_pct / 2, 0.02):.2f}"
        )
    
    if not min_rr_ok:
        return ExecutionPlan(action="wait_rr", riskPct="0")
    
    return ExecutionPlan(
        action="open_or_scale",
        riskPct=f"{risk_cap_pct:.2f}"
    )
```

---

## 7. Position Sizing Logic

```python
def calculate_position_size(
    account_balance: float,
    risk_pct: float,
    entry_price: float,
    stop_loss: float,
    symbol_info: Dict
) -> float:
    """
    Calculate position size based on risk percentage.
    
    Args:
        account_balance: Account balance in account currency
        risk_pct: Risk percentage (e.g., 0.02 for 2%)
        entry_price: Planned entry price
        stop_loss: Stop loss price
        symbol_info: Symbol information from MT5
    
    Returns:
        Volume in lots
    """
    risk_amount = account_balance * risk_pct
    price_distance = abs(entry_price - stop_loss)
    
    # Get contract size and tick value from symbol_info
    contract_size = symbol_info.get('trade_contract_size', 100000)
    tick_value = symbol_info.get('trade_tick_value', 1.0)
    tick_size = symbol_info.get('trade_tick_size', 0.00001)
    
    # Calculate volume
    ticks = price_distance / tick_size
    risk_per_lot = ticks * tick_value
    volume = risk_amount / risk_per_lot if risk_per_lot > 0 else 0
    
    # Round to min/step
    min_vol = symbol_info.get('volume_min', 0.01)
    vol_step = symbol_info.get('volume_step', 0.01)
    
    volume = max(min_vol, round(volume / vol_step) * vol_step)
    
    return volume
```

---

## 8. Autonomy Loop Implementation

```python
import schedule
import time
import threading
from datetime import datetime, timezone

class AutonomyLoop:
    def __init__(self, ai_engine, interval_seconds: int = 300):
        self.ai_engine = ai_engine
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the autonomy loop in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the autonomy loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run_loop(self):
        """Main loop that runs evaluations."""
        while self.running:
            try:
                enabled_symbols = self.ai_engine.get_enabled_symbols()
                
                for symbol_config in enabled_symbols:
                    symbol = symbol_config['symbol']
                    timeframe = symbol_config['timeframe']
                    
                    try:
                        # Run evaluation
                        result = self.ai_engine.evaluate(symbol, timeframe)
                        
                        # If action required and auto-execute enabled
                        if result['action'] in ['open_or_scale', 'pending_only']:
                            if symbol_config.get('auto_execute', False):
                                self.ai_engine.execute_trade_idea(result['trade_idea'])
                            else:
                                # Store for manual approval
                                self.ai_engine.store_trade_idea(result['trade_idea'])
                    
                    except Exception as e:
                        self.ai_engine.log_error(symbol, str(e))
                
            except Exception as e:
                print(f"Autonomy loop error: {e}")
            
            # Sleep for interval
            time.sleep(self.interval_seconds)
```

---

## 9. Frontend API Integration

### 9.1 API Client Functions

**File:** `src/lib/api.ts` (additions)

```typescript
// AI Strategy Management
export async function getStrategies(): Promise<EMNRRules[]> {
  return apiCall('/api/ai/strategies');
}

export async function getStrategy(symbol: string): Promise<EMNRRules> {
  return apiCall(`/api/ai/strategies/${symbol}`);
}

export async function saveStrategy(symbol: string, rules: EMNRRules): Promise<void> {
  return apiCall(`/api/ai/strategies/${symbol}`, {
    method: 'POST',
    body: JSON.stringify(rules),
  });
}

// AI Evaluation
export async function evaluateSymbol(symbol: string, timeframe: string = 'H1'): Promise<EvaluateResponse> {
  return apiCall(`/api/ai/evaluate/${symbol}`, {
    method: 'POST',
    body: JSON.stringify({ timeframe }),
  });
}

// AI Status & Control
export async function getAIStatus(): Promise<AIStatusResponse> {
  return apiCall('/api/ai/status');
}

export async function enableAI(symbol: string, timeframe: string = 'H1', autoExecute: boolean = false): Promise<void> {
  return apiCall(`/api/ai/enable/${symbol}`, {
    method: 'POST',
    body: JSON.stringify({ timeframe, auto_execute: autoExecute }),
  });
}

export async function disableAI(symbol: string): Promise<void> {
  return apiCall(`/api/ai/disable/${symbol}`, {
    method: 'POST',
  });
}

export async function triggerKillSwitch(reason?: string): Promise<void> {
  return apiCall('/api/ai/kill-switch', {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

// Trade Ideas
export async function getTradeIdeas(): Promise<TradeIdea[]> {
  return apiCall('/api/ai/trade-ideas');
}

export async function approveTradeIdea(id: string): Promise<void> {
  return apiCall(`/api/ai/trade-ideas/${id}/approve`, {
    method: 'POST',
  });
}

export async function rejectTradeIdea(id: string): Promise<void> {
  return apiCall(`/api/ai/trade-ideas/${id}/reject`, {
    method: 'POST',
  });
}

// AI Decisions
export async function getAIDecisions(symbol?: string, limit: number = 50): Promise<AIDecision[]> {
  const params = new URLSearchParams();
  if (symbol) params.append('symbol', symbol);
  params.append('limit', limit.toString());
  return apiCall(`/api/ai/decisions?${params}`);
}
```

---

**End of Technical Specifications**

*This document provides detailed implementation specifications for the AI trading integration. Refer to AI_TRADING_INTEGRATION_BLUEPRINT.md for the overall architecture and implementation plan.*

