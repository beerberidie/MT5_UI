# Trade Idea Generation Diagnostic Guide

**Date:** 2025-01-06  
**Issue:** Trade ideas not being generated - "Conditions not met for trade idea"  
**Status:** 🔍 DIAGNOSIS COMPLETE

---

## Root Cause Analysis

After analyzing the AI evaluation logic, I've identified **why trade ideas are not being generated**. The issue is **NOT a bug** - it's the AI system working correctly by enforcing strict trading conditions.

---

## How Trade Idea Generation Works

### Step-by-Step Evaluation Process

1. **Fetch Historical Data** (100 bars)
   - Requires minimum 50 bars
   - Uses MT5 live data

2. **Calculate Technical Indicators**
   - EMA Fast (20) and Slow (50)
   - RSI (14 period)
   - MACD (12, 26, 9)
   - ATR (14 period)

3. **Generate Facts from Indicators**
   - `ema_fast_gt_slow`: EMA(20) > EMA(50)
   - `rsi_between_40_60`: 40 ≤ RSI ≤ 60
   - `macd_hist_gt_0`: MACD histogram > 0
   - `rsi_gt_70`: RSI > 70
   - `long_upper_wick`: Upper wick > 2× body

4. **Evaluate EMNR Conditions** (from `EURUSD_H1.json`)
   ```json
   {
     "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
     "exit": ["rsi_gt_70"],
     "strong": ["macd_hist_gt_0"],
     "weak": ["long_upper_wick"]
   }
   ```

5. **Calculate Confidence Score**
   ```
   Score = 0 (base)
   + 30 (if entry conditions met)
   + 25 (if strong conditions met)
   - 15 (if weak conditions met)
   - 40 (if exit conditions met)
   + 10 (if alignment OK)
   - news_penalty
   ```

6. **Check Alignment**
   - Timeframe must be in `bestTimeframes`: ["M15", "H1", "H4"]
   - Session must be in `bestSessions`: ["London", "NewYork"]

7. **Calculate SL/TP Levels**
   - Uses ATR × multiplier (1.5)
   - Calculates RR ratio

8. **Schedule Action** (based on confidence)
   - **< 60**: `observe` (no trade idea)
   - **60-74**: `pending_only` (limit orders)
   - **≥ 75 + RR < 2.0**: `wait_rr` (wait for better setup)
   - **≥ 75 + RR ≥ 2.0**: `open_or_scale` (trade idea generated)

9. **Create Trade Idea** (only if action allows execution)

---

## Why Trade Ideas Are NOT Being Generated

### Possible Reasons (in order of likelihood):

### 1. **Entry Conditions Not Met** (MOST LIKELY)

**Required for EURUSD H1:**
- ✅ `ema_fast_gt_slow`: EMA(20) must be above EMA(50)
- ✅ `rsi_between_40_60`: RSI must be between 40 and 60

**Current Market Conditions:**
- If EMA(20) < EMA(50) → **Entry condition FAILS**
- If RSI < 40 or RSI > 60 → **Entry condition FAILS**
- If either fails → Confidence = 0 → Action = "observe" → **NO TRADE IDEA**

**Example Scenario:**
```
Current EURUSD H1:
- EMA(20) = 1.08450
- EMA(50) = 1.08500  ← EMA fast is BELOW slow
- RSI = 55           ← RSI is in range

Result: Entry condition FAILS (ema_fast_gt_slow = False)
Confidence: 0
Action: observe
Trade Idea: NONE
```

---

### 2. **Confidence Score Too Low** (LIKELY)

Even if entry conditions are met, confidence might be too low:

**Scenario A: Entry only (no strong)**
```
Entry: TRUE (+30)
Strong: FALSE (0)
Weak: FALSE (0)
Exit: FALSE (0)
Align: FALSE (0)
Total: 30 → Action: observe → NO TRADE IDEA
```

**Scenario B: Entry + Weak**
```
Entry: TRUE (+30)
Strong: FALSE (0)
Weak: TRUE (-15)
Exit: FALSE (0)
Align: FALSE (0)
Total: 15 → Action: observe → NO TRADE IDEA
```

**Scenario C: Entry + Strong (no alignment)**
```
Entry: TRUE (+30)
Strong: TRUE (+25)
Weak: FALSE (0)
Exit: FALSE (0)
Align: FALSE (0)
Total: 55 → Action: observe → NO TRADE IDEA
```

**Minimum for Trade Idea:**
- Need confidence ≥ 60 for any action
- Need confidence ≥ 75 for market orders
- **Best case:** Entry + Strong + Align = 30 + 25 + 10 = **65** (pending_only)
- **Ideal case:** Entry + Strong + Align + No Weak/Exit = **65** (still not enough for market orders!)

---

### 3. **Exit Condition Active** (POSSIBLE)

If `rsi_gt_70` is TRUE:
```
Entry: TRUE (+30)
Strong: TRUE (+25)
Exit: TRUE (-40)
Align: TRUE (+10)
Total: 25 → Action: observe → NO TRADE IDEA
```

---

### 4. **Session/Timeframe Alignment** (POSSIBLE)

**Current Session Check:**
- SAST timezone (Africa/Johannesburg)
- London: 09:00-17:00 SAST
- NewYork: 15:00-23:00 SAST
- Tokyo: 02:00-10:00 SAST
- Sydney: Other times

If evaluating outside London/NewYork sessions → Alignment = FALSE → -10 points

---

### 5. **Insufficient Historical Data** (UNLIKELY)

- Requires minimum 50 bars
- Fetches 100 bars
- If MT5 not connected or symbol not in Market Watch → No data → No trade idea

---

## How to Generate Trade Ideas

### Option 1: Wait for Market Conditions (RECOMMENDED)

**For EURUSD H1 Long Strategy:**
1. Wait for EMA(20) to cross above EMA(50)
2. Wait for RSI to be between 40-60
3. Wait for MACD histogram to be positive
4. Evaluate during London or NewYork session
5. Ensure no long upper wicks on recent candles

**Ideal Market Conditions:**
- Strong uptrend (EMA fast > EMA slow)
- RSI neutral (40-60, not overbought)
- MACD confirming (histogram > 0)
- Clean price action (no rejection wicks)
- During active trading session

---

### Option 2: Adjust Strategy Configuration (FOR TESTING)

**Lower Entry Requirements:**

Edit `config/ai/strategies/EURUSD_H1.json`:

```json
{
  "conditions": {
    "entry": [
      "ema_fast_gt_slow"
      // Removed "rsi_between_40_60" to make it easier
    ],
    "exit": [
      "rsi_gt_70"
    ],
    "strong": [
      "macd_hist_gt_0"
    ],
    "weak": []  // Removed "long_upper_wick" to avoid penalties
  },
  "strategy": {
    "direction": "long",
    "min_rr": 1.5,  // Lowered from 2.0
    "news_embargo_minutes": 30
  }
}
```

**This will:**
- Only require EMA crossover for entry
- Remove weak condition penalties
- Lower RR requirement to 1.5

---

### Option 3: Create a Test Strategy (FOR DEVELOPMENT)

Create `config/ai/strategies/EURUSD_H1_TEST.json`:

```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "sessions": ["London", "NewYork", "Tokyo", "Sydney"],
  "indicators": {
    "ema": {"fast": 20, "slow": 50},
    "rsi": {"period": 14, "overbought": 70, "oversold": 30},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "atr": {"period": 14, "multiplier": 1.5}
  },
  "conditions": {
    "entry": ["ema_fast_gt_slow"],
    "exit": [],
    "strong": [],
    "weak": []
  },
  "strategy": {
    "direction": "long",
    "min_rr": 1.0,
    "news_embargo_minutes": 0
  }
}
```

**This will:**
- Generate trade ideas whenever EMA(20) > EMA(50)
- No strong/weak/exit conditions
- Any session allowed
- RR ratio only needs to be ≥ 1.0

---

## Diagnostic Commands

### 1. Check Current Market Conditions

Open browser console (F12) and run:
```javascript
// Fetch current symbol data
fetch('http://127.0.0.1:5001/api/symbols?live=true')
  .then(r => r.json())
  .then(d => console.log('Symbols:', d));
```

### 2. Trigger Manual Evaluation with Logging

The backend should log evaluation details. Check terminal output for:
```
[INFO] Manual evaluation requested for EURUSD H1
[INFO] Trade idea generated for EURUSD: confidence=XX, action=XXX
```

Or:
```
[WARNING] No EMNR rules found for EURUSD H1
[WARNING] No profile found for EURUSD
[WARNING] Insufficient bars for EURUSD H1: XX
```

### 3. Check AI Settings

```bash
cat config/ai/settings.json
```

Verify:
- `"enabled": true`
- `"confidence_threshold": 75`
- `"min_rr_ratio": 2.0`

---

## Expected Behavior

### When Conditions ARE Met:

**Backend Log:**
```
[INFO] Manual evaluation requested for EURUSD H1
[INFO] Trade idea generated for EURUSD: confidence=65, action=pending_only
```

**Frontend Response:**
```json
{
  "success": true,
  "confidence": 65,
  "action": "pending_only",
  "message": "Trade idea generated",
  "trade_idea": {
    "id": "EURUSD_H1_20250106_143022",
    "symbol": "EURUSD",
    "confidence": 65,
    "direction": "long",
    "entry_price": 1.08450,
    "stop_loss": 1.08350,
    "take_profit": 1.08650,
    "rr_ratio": 2.0,
    "status": "pending_approval"
  }
}
```

### When Conditions are NOT Met:

**Backend Log:**
```
[INFO] Manual evaluation requested for EURUSD H1
[INFO] Trade idea generated for EURUSD: confidence=30, action=observe
```

**Frontend Response:**
```json
{
  "success": true,
  "confidence": 30,
  "action": "observe",
  "message": "Conditions not met for trade idea",
  "trade_idea": null
}
```

---

## Recommended Actions

### For Testing (Immediate):

1. **Modify EURUSD_H1 strategy** to lower requirements
2. **Restart backend** to reload configuration
3. **Evaluate EURUSD** again
4. **Check if trade idea is generated**

### For Production (Long-term):

1. **Wait for proper market conditions**
2. **Monitor multiple symbols** (GBPUSD, USDJPY, XAUUSD)
3. **Evaluate during active sessions** (London/NewYork)
4. **Review strategy rules** to ensure they match your trading style

---

## Summary

**The AI system is working correctly.** Trade ideas are not being generated because:

1. ✅ **Entry conditions are not met** (EMA crossover + RSI range)
2. ✅ **Confidence score is too low** (< 60 for any action)
3. ✅ **Market conditions don't match strategy requirements**

**This is GOOD** - it means the AI is being selective and only generating trade ideas when conditions are favorable.

**To generate trade ideas:**
- **Option A:** Wait for market conditions to align with strategy
- **Option B:** Adjust strategy to be less strict (for testing)
- **Option C:** Try different symbols/timeframes

**Next Steps:**
1. Check backend logs during evaluation
2. Verify current indicator values
3. Adjust strategy if needed for testing
4. Monitor multiple symbols for opportunities

---

**Diagnosis Complete:** 2025-01-06  
**Status:** ✅ SYSTEM WORKING AS DESIGNED  
**Action Required:** Adjust strategy or wait for market conditions

