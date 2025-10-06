# AI Trading Integration - Code Examples & Quick Start

**Companion Document to:** AI_TRADING_INTEGRATION_BLUEPRINT.md  
**Date:** 2025-10-06

---

## 1. Quick Start Guide

### 1.1 Prerequisites

1. Existing MT5_UI installation working
2. Python 3.11 virtual environment active
3. MT5 terminal running with demo account
4. Node.js and npm installed for frontend

### 1.2 Installation Steps

```bash
# 1. Install new Python dependencies
pip install pandas-ta==0.3.14b0 schedule==1.2.0 jsonschema==4.19.0

# 2. Create AI directory structure
mkdir -p backend/ai
mkdir -p config/ai/strategies
mkdir -p config/ai/profiles
mkdir -p logs
mkdir -p data/ai/indicators

# 3. Create initial config files
# (See examples below)

# 4. No frontend dependencies needed (already installed)
```

### 1.3 First Strategy Setup (EURUSD)

**Create:** `config/ai/strategies/EURUSD_H1.json`

```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "sessions": ["London", "NewYork"],
  "indicators": {
    "ema": {"fast": 20, "slow": 50},
    "rsi": {"period": 14, "overbought": 70, "oversold": 30},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "atr": {"period": 14, "multiplier": 1.5}
  },
  "conditions": {
    "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
    "exit": ["rsi_gt_70"],
    "strong": ["macd_hist_gt_0"],
    "weak": ["long_upper_wick"]
  },
  "strategy": {
    "direction": "long",
    "min_rr": 2.0,
    "news_embargo_minutes": 30,
    "invalidations": ["price_close_lt_ema_slow"]
  }
}
```

**Create:** `config/ai/profiles/EURUSD.json`

```json
{
  "symbol": "EURUSD",
  "bestSessions": ["London", "NewYork"],
  "bestTimeframes": ["M15", "H1", "H4"],
  "externalDrivers": ["DXY", "US10Y"],
  "style": {
    "bias": "trend-follow",
    "rrTarget": 2.0,
    "maxRiskPct": 0.01
  },
  "management": {
    "breakevenAfterRR": 1.0,
    "partialAtRR": 1.5,
    "trailUsingATR": true,
    "atrMultiplier": 1.5
  },
  "invalidations": ["price_close_lt_ema_slow"]
}
```

**Create:** `config/ai/settings.json`

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
  "timezone": "Africa/Johannesburg"
}
```

---

## 2. Backend Implementation Examples

### 2.1 Core AI Engine Module

**File:** `backend/ai/engine.py`

```python
"""
AI Trading Engine - Main orchestrator
"""
from typing import Dict, List, Optional
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .emnr import evaluate_conditions
from .confidence import confidence_score
from .scheduler import schedule_action
from .indicators import calculate_indicators
from .symbol_profiles import load_profile
from .rules_manager import load_rules
from ..mt5_client import MT5Client
from ..models import TradeIdea, EMNRFlags, IndicatorValues, ExecutionPlan

class AIEngine:
    def __init__(self, config_dir: str, mt5_client: MT5Client):
        self.config_dir = Path(config_dir)
        self.mt5 = mt5_client
        self.enabled_symbols = {}  # symbol -> {timeframe, auto_execute}
    
    def evaluate(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        Run full evaluation cycle for a symbol.
        
        Returns:
            Dict with trade_idea, confidence, action, message
        """
        # 1. Load strategy rules
        rules = load_rules(self.config_dir / "ai" / "strategies", symbol, timeframe)
        if not rules:
            return {
                "trade_idea": None,
                "confidence": 0,
                "action": "observe",
                "message": f"No strategy found for {symbol} {timeframe}"
            }
        
        # 2. Load symbol profile
        profile = load_profile(self.config_dir / "ai" / "profiles", symbol)
        
        # 3. Fetch historical bars from MT5
        bars = self._fetch_bars(symbol, timeframe, count=120)
        if not bars:
            return {
                "trade_idea": None,
                "confidence": 0,
                "action": "observe",
                "message": "Failed to fetch historical data"
            }
        
        # 4. Calculate indicators
        indicator_values = calculate_indicators(bars, rules.indicators)
        
        # 5. Generate facts from indicators
        facts = self._generate_facts(bars, indicator_values, rules.indicators)
        
        # 6. Evaluate EMNR conditions
        emnr_flags = evaluate_conditions(facts, rules.conditions)
        
        # 7. Check alignment
        current_session = self._get_current_session()
        align_ok = (
            timeframe in profile.bestTimeframes and
            current_session in profile.bestSessions
        )
        
        # 8. Calculate confidence
        news_penalty = self._check_news_embargo(symbol, rules.strategy.news_embargo_minutes)
        conf = confidence_score(emnr_flags, align_ok, news_penalty)
        
        # 9. Schedule action
        current_price = bars[-1]['close']
        sl, tp, rr = self._calculate_sl_tp(
            current_price,
            indicator_values.get('atr'),
            rules.strategy.direction,
            profile.style.rrTarget
        )
        min_rr_ok = rr >= rules.strategy.min_rr
        
        exec_plan = schedule_action(conf, min_rr_ok, profile.style.maxRiskPct)
        
        # 10. Generate trade idea if action required
        trade_idea = None
        if exec_plan.action in ["open_or_scale", "pending_only"]:
            trade_idea = self._create_trade_idea(
                symbol, timeframe, conf, exec_plan,
                rules.strategy.direction, current_price, sl, tp, rr,
                emnr_flags, indicator_values
            )
        
        return {
            "trade_idea": trade_idea,
            "confidence": conf,
            "action": exec_plan.action,
            "message": self._get_action_message(exec_plan.action, conf)
        }
    
    def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> List[Dict]:
        """Fetch historical bars from MT5."""
        try:
            # Map timeframe string to MT5 constant
            tf_map = {
                "M1": 1, "M5": 5, "M15": 15, "M30": 30,
                "H1": 16385, "H4": 16388, "D1": 16408
            }
            mt5_tf = tf_map.get(timeframe, 16385)  # Default H1
            
            bars = self.mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
            return bars
        except Exception as e:
            print(f"Error fetching bars: {e}")
            return []
    
    def _generate_facts(self, bars: List[Dict], indicators: Dict, config) -> Dict[str, bool]:
        """Generate boolean facts from indicator values."""
        facts = {}
        closes = [b['close'] for b in bars]
        
        # EMA facts
        if 'ema_fast' in indicators and 'ema_slow' in indicators:
            facts['ema_fast_gt_slow'] = indicators['ema_fast'] > indicators['ema_slow']
            facts['ema_fast_lt_slow'] = indicators['ema_fast'] < indicators['ema_slow']
            facts['price_above_ema_fast'] = closes[-1] > indicators['ema_fast']
            facts['price_close_lt_ema_slow'] = closes[-1] < indicators['ema_slow']
        
        # RSI facts
        if 'rsi' in indicators:
            rsi = indicators['rsi']
            facts['rsi_lt_30'] = rsi < 30
            facts['rsi_gt_70'] = rsi > 70
            facts['rsi_between_40_60'] = 40 <= rsi <= 60
        
        # MACD facts
        if 'macd_hist' in indicators:
            facts['macd_hist_gt_0'] = indicators['macd_hist'] > 0
            facts['macd_hist_lt_0'] = indicators['macd_hist'] < 0
        
        # ATR facts
        if 'atr' in indicators and 'atr_median' in indicators:
            facts['atr_above_median'] = indicators['atr'] > indicators['atr_median']
            facts['atr_below_median'] = indicators['atr'] < indicators['atr_median']
        
        # Candlestick facts
        last = bars[-1]
        body = abs(last['close'] - last['open'])
        upper_wick = last['high'] - max(last['open'], last['close'])
        lower_wick = min(last['open'], last['close']) - last['low']
        
        facts['long_upper_wick'] = upper_wick > body * 2
        facts['long_lower_wick'] = lower_wick > body * 2
        
        return facts
    
    def _calculate_sl_tp(self, price: float, atr: float, direction: str, rr_target: float):
        """Calculate stop loss and take profit based on ATR."""
        if not atr:
            return None, None, 0
        
        atr_mult = 1.5  # From profile
        
        if direction == "long":
            sl = price - (atr * atr_mult)
            tp = price + (atr * atr_mult * rr_target)
        else:  # short
            sl = price + (atr * atr_mult)
            tp = price - (atr * atr_mult * rr_target)
        
        risk = abs(price - sl)
        reward = abs(tp - price)
        rr = reward / risk if risk > 0 else 0
        
        return sl, tp, rr
    
    def _get_current_session(self) -> str:
        """Determine current trading session based on UTC time."""
        from datetime import datetime
        import pytz
        
        # Convert UTC to SAST (UTC+2)
        utc_now = datetime.now(pytz.UTC)
        sast_now = utc_now.astimezone(pytz.timezone('Africa/Johannesburg'))
        hour_min = sast_now.strftime("%H:%M")
        
        # Session windows (SAST)
        if "09:00" <= hour_min <= "17:30":
            return "London"
        elif "14:30" <= hour_min <= "22:00":
            return "NewYork"
        elif "02:00" <= hour_min <= "10:00":
            return "Tokyo"
        elif "00:00" <= hour_min <= "08:00":
            return "Sydney"
        else:
            return "None"
    
    def _check_news_embargo(self, symbol: str, embargo_minutes: int) -> int:
        """
        Check if we're in a news embargo window.
        Returns negative penalty value.
        """
        # TODO: Integrate with economic calendar API
        # For now, return 0 (no penalty)
        return 0
    
    def _create_trade_idea(self, symbol, timeframe, confidence, exec_plan,
                          direction, price, sl, tp, rr, emnr_flags, indicators):
        """Create a TradeIdea object."""
        import uuid
        
        # Calculate volume based on risk
        account = self.mt5.account_info()
        balance = account.get('balance', 10000)
        risk_pct = float(exec_plan.riskPct)
        
        volume = self._calculate_volume(balance, risk_pct, price, sl, symbol)
        
        return TradeIdea(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            timeframe=timeframe,
            confidence=confidence,
            action=exec_plan.action,
            direction=direction,
            entry_price=price,
            stop_loss=sl,
            take_profit=tp,
            volume=volume,
            rr_ratio=rr,
            emnr_flags=emnr_flags,
            indicators=IndicatorValues(**indicators),
            execution_plan=exec_plan,
            status="pending_approval"
        )
    
    def _calculate_volume(self, balance: float, risk_pct: float, 
                         entry: float, sl: float, symbol: str) -> float:
        """Calculate position size based on risk."""
        # Get symbol info
        symbol_info = self.mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.01  # Default minimum
        
        risk_amount = balance * risk_pct
        price_distance = abs(entry - sl)
        
        contract_size = symbol_info.get('trade_contract_size', 100000)
        tick_value = symbol_info.get('trade_tick_value', 1.0)
        tick_size = symbol_info.get('trade_tick_size', 0.00001)
        
        ticks = price_distance / tick_size
        risk_per_lot = ticks * tick_value
        volume = risk_amount / risk_per_lot if risk_per_lot > 0 else 0.01
        
        # Round to min/step
        min_vol = symbol_info.get('volume_min', 0.01)
        vol_step = symbol_info.get('volume_step', 0.01)
        volume = max(min_vol, round(volume / vol_step) * vol_step)
        
        return volume
    
    def _get_action_message(self, action: str, confidence: int) -> str:
        """Generate human-readable message for action."""
        messages = {
            "observe": f"Confidence {confidence} below threshold. Observing only.",
            "pending_only": f"Confidence {confidence}. Pending orders allowed.",
            "open_or_scale": f"Confidence {confidence}. Trade idea generated.",
            "wait_rr": "RR ratio below minimum. Waiting for better setup."
        }
        return messages.get(action, "Unknown action")
```

---

## 3. API Route Examples

**File:** `backend/ai_routes.py`

```python
"""
AI Trading API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional

from .models import (
    EMNRRules, SymbolProfile, EvaluateRequest, EvaluateResponse,
    AIStatusResponse, EnableAIRequest, TradeIdea, AIDecision
)
from .ai.engine import AIEngine
from .ai.rules_manager import load_rules, save_rules, delete_rules
from .ai.symbol_profiles import load_profile, save_profile, delete_profile
from .ai.ai_logger import log_decision, get_decisions
from .config import CONFIG_DIR
from .mt5_client import MT5Client
from .app import require_api_key

router = APIRouter(prefix="/api/ai", tags=["AI Trading"])
limiter = Limiter(key_func=get_remote_address)

# Initialize AI engine (singleton)
mt5 = MT5Client()
ai_engine = AIEngine(CONFIG_DIR, mt5)

# Strategy Management
@router.get("/strategies")
@limiter.limit("100/minute")
async def list_strategies(request: Request):
    """List all configured strategies."""
    # TODO: Implement
    return []

@router.get("/strategies/{symbol}")
@limiter.limit("100/minute")
async def get_strategy(request: Request, symbol: str, timeframe: str = "H1"):
    """Get strategy for a symbol."""
    rules = load_rules(CONFIG_DIR / "ai" / "strategies", symbol, timeframe)
    if not rules:
        raise HTTPException(404, detail=f"No strategy found for {symbol} {timeframe}")
    return rules

@router.post("/strategies/{symbol}", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def save_strategy_route(request: Request, symbol: str, rules: EMNRRules):
    """Create or update strategy for a symbol."""
    save_rules(CONFIG_DIR / "ai" / "strategies", symbol, rules)
    return {"status": "success", "message": f"Strategy saved for {symbol}"}

# Evaluation
@router.post("/evaluate/{symbol}", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def evaluate_symbol(request: Request, symbol: str, req: EvaluateRequest):
    """Run AI evaluation for a symbol."""
    try:
        result = ai_engine.evaluate(symbol, req.timeframe)
        return EvaluateResponse(**result)
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# Status & Control
@router.get("/status")
@limiter.limit("100/minute")
async def get_ai_status(request: Request):
    """Get AI engine status."""
    return AIStatusResponse(
        enabled=len(ai_engine.enabled_symbols) > 0,
        mode="semi-auto",  # TODO: Load from settings
        enabled_symbols=list(ai_engine.enabled_symbols.keys()),
        active_trade_ideas=0,  # TODO: Count from storage
        autonomy_loop_running=False  # TODO: Check loop status
    )

@router.post("/enable/{symbol}", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def enable_ai(request: Request, symbol: str, req: EnableAIRequest):
    """Enable AI trading for a symbol."""
    ai_engine.enabled_symbols[symbol] = {
        "timeframe": req.timeframe,
        "auto_execute": req.auto_execute
    }
    return {"status": "success", "message": f"AI enabled for {symbol}"}

@router.post("/disable/{symbol}", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def disable_ai(request: Request, symbol: str):
    """Disable AI trading for a symbol."""
    if symbol in ai_engine.enabled_symbols:
        del ai_engine.enabled_symbols[symbol]
    return {"status": "success", "message": f"AI disabled for {symbol}"}

@router.post("/kill-switch", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def kill_switch(request: Request):
    """Emergency stop all AI trading."""
    disabled = list(ai_engine.enabled_symbols.keys())
    ai_engine.enabled_symbols.clear()
    
    # TODO: Cancel pending trade ideas
    # TODO: Optionally close AI positions
    
    log_decision({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": "ALL",
        "action": "kill_switch",
        "status": "executed",
        "result": f"Disabled {len(disabled)} symbols"
    })
    
    return {
        "status": "success",
        "message": "AI trading disabled for all symbols",
        "disabled_symbols": disabled,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Decisions
@router.get("/decisions")
@limiter.limit("100/minute")
async def get_ai_decisions_route(request: Request, symbol: Optional[str] = None, limit: int = 50):
    """Get recent AI decisions."""
    decisions = get_decisions(symbol, limit)
    return decisions
```

---

## 4. Frontend Component Examples

### 4.1 AI Control Panel

**File:** `src/components/ai/AIControlPanel.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { AlertCircle, Power, PowerOff } from 'lucide-react';
import { getAIStatus, triggerKillSwitch } from '@/lib/api';
import { toast } from '@/hooks/use-toast';

interface AIStatus {
  enabled: boolean;
  mode: string;
  enabled_symbols: string[];
  active_trade_ideas: number;
  autonomy_loop_running: boolean;
}

const AIControlPanel: React.FC = () => {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  async function loadStatus() {
    try {
      const data = await getAIStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to load AI status:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleKillSwitch() {
    if (!confirm('Are you sure you want to disable all AI trading?')) {
      return;
    }

    try {
      await triggerKillSwitch('Manual kill switch activation');
      toast({
        title: 'AI Trading Disabled',
        description: 'All AI trading has been stopped.',
        variant: 'destructive',
      });
      loadStatus();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to trigger kill switch',
        variant: 'destructive',
      });
    }
  }

  if (loading) {
    return <div className="animate-pulse">Loading AI status...</div>;
  }

  return (
    <div className="trading-panel">
      <div className="trading-header flex items-center justify-between">
        <h3 className="font-medium">AI Control Panel</h3>
        <Button
          variant="destructive"
          size="sm"
          onClick={handleKillSwitch}
          className="gap-2"
        >
          <PowerOff className="w-4 h-4" />
          KILL SWITCH
        </Button>
      </div>

      <div className="trading-content space-y-4">
        {/* Status Indicator */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Engine Status:</span>
          <div className="flex items-center gap-2">
            {status?.enabled ? (
              <>
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-sm text-green-400">ACTIVE</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-sm text-red-400">DISABLED</span>
              </>
            )}
          </div>
        </div>

        {/* Enabled Symbols */}
        <div>
          <span className="text-sm font-medium">Enabled Symbols:</span>
          <div className="mt-2 flex flex-wrap gap-2">
            {status?.enabled_symbols.length === 0 ? (
              <span className="text-xs text-text-muted">None</span>
            ) : (
              status?.enabled_symbols.map((sym) => (
                <span
                  key={sym}
                  className="px-2 py-1 bg-primary/20 text-primary text-xs rounded"
                >
                  {sym}
                </span>
              ))
            )}
          </div>
        </div>

        {/* Mode */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Mode:</span>
          <span className="text-sm text-text-secondary uppercase">
            {status?.mode || 'N/A'}
          </span>
        </div>

        {/* Active Trade Ideas */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Active Trade Ideas:</span>
          <span className="text-sm font-mono">{status?.active_trade_ideas || 0}</span>
        </div>
      </div>
    </div>
  );
};

export default AIControlPanel;
```

---

## 5. Testing Examples

### 5.1 Backend Unit Test

**File:** `tests/test_ai_confidence.py`

```python
import pytest
from backend.ai.confidence import confidence_score
from backend.models import EMNRFlags

def test_confidence_entry_only():
    """Test confidence with only entry flag."""
    flags = EMNRFlags(entry=True, exit=False, strong=False, weak=False)
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    assert score == 30  # Entry weight

def test_confidence_entry_strong():
    """Test confidence with entry and strong flags."""
    flags = EMNRFlags(entry=True, exit=False, strong=True, weak=False)
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    assert score == 55  # Entry (30) + Strong (25)

def test_confidence_with_alignment():
    """Test confidence with alignment bonus."""
    flags = EMNRFlags(entry=True, exit=False, strong=True, weak=False)
    score = confidence_score(flags, align_ok=True, news_penalty=0)
    assert score == 65  # Entry (30) + Strong (25) + Align (10)

def test_confidence_with_news_penalty():
    """Test confidence with news penalty."""
    flags = EMNRFlags(entry=True, exit=False, strong=True, weak=False)
    score = confidence_score(flags, align_ok=True, news_penalty=-20)
    assert score == 45  # 65 - 20

def test_confidence_clamping():
    """Test that confidence is clamped to 0-100."""
    flags = EMNRFlags(entry=False, exit=True, strong=False, weak=True)
    score = confidence_score(flags, align_ok=False, news_penalty=-50)
    # Exit (-40) + Weak (-15) + Penalty (-50) = -105, clamped to 0
    assert score == 0
```

---

## 6. Manual Testing Checklist

### 6.1 Backend API Testing

```bash
# 1. Test health check
curl http://127.0.0.1:5001/api/health

# 2. Test AI status
curl http://127.0.0.1:5001/api/ai/status

# 3. Test evaluation (requires strategy file)
curl -X POST http://127.0.0.1:5001/api/ai/evaluate/EURUSD \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"timeframe": "H1", "force": false}'

# 4. Test enable AI
curl -X POST http://127.0.0.1:5001/api/ai/enable/EURUSD \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"timeframe": "H1", "auto_execute": false}'

# 5. Test kill switch
curl -X POST http://127.0.0.1:5001/api/ai/kill-switch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"reason": "Testing"}'
```

### 6.2 Frontend Testing

1. Navigate to http://localhost:3000/ai
2. Verify AI Control Panel displays
3. Check status indicator shows correct state
4. Enable AI for EURUSD
5. Trigger manual evaluation
6. View trade idea if generated
7. Test kill switch button
8. Verify all symbols disabled

---

## 7. Troubleshooting Guide

### 7.1 Common Issues

**Issue:** "No strategy found for EURUSD H1"
- **Solution:** Create `config/ai/strategies/EURUSD_H1.json` with valid strategy

**Issue:** "Failed to fetch historical data"
- **Solution:** Ensure MT5 terminal is running and symbol is in Market Watch

**Issue:** Confidence always 0
- **Solution:** Check indicator calculations, verify bars data is valid

**Issue:** AI page shows "Loading..." forever
- **Solution:** Check browser console for API errors, verify backend is running

**Issue:** Kill switch doesn't work
- **Solution:** Check API key is set, verify backend logs for errors

---

**End of Examples Document**

*This document provides practical code examples and quick-start instructions. Refer to the main blueprint for architecture and the technical specs for detailed schemas.*

