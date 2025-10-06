# EMNR Rules Store — JSON Schema (Entry/Exit/Strong/Weak)

Use this schema to define indicator-based conditions for each symbol/timeframe/session.
The engine evaluates these into booleans and a combined strategy flag.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EMNR Strategy Rules",
  "type": "object",
  "properties": {
    "symbol": {"type": "string"},
    "timeframe": {"type": "string", "enum": ["M5","M15","H1","H4","D1"]},
    "sessions": {
      "type": "array",
      "items": {"type": "string", "enum": ["London","NewYork","Tokyo","Sydney"]}
    },
    "indicators": {
      "type": "object",
      "properties": {
        "ema": {"type": "object", "properties": {"fast": {"type":"integer"}, "slow":{"type":"integer"}}},
        "rsi": {"type": "object", "properties": {"period":{"type":"integer"}, "overbought":{"type":"number"}, "oversold":{"type":"number"}}},
        "macd": {"type":"object", "properties": {"fast":{"type":"integer"}, "slow":{"type":"integer"}, "signal":{"type":"integer"}}},
        "atr": {"type":"object", "properties": {"period":{"type":"integer"}, "multiplier":{"type":"number"}}}
      }
    },
    "conditions": {
      "type": "object",
      "properties": {
        "entry":   {"type":"array","items":{"type":"string"}},
        "exit":    {"type":"array","items":{"type":"string"}},
        "strong":  {"type":"array","items":{"type":"string"}},
        "weak":    {"type":"array","items":{"type":"string"}}
      },
      "description": "Each item is a mini-expression referencing indicator facts, e.g., 'ema_fast_gt_slow', 'rsi_lt_30'."
    },
    "strategy": {
      "type":"object",
      "properties": {
        "direction": {"type":"string","enum":["long","short","both"]},
        "min_rr": {"type":"number", "default": 2.0},
        "news_embargo_minutes": {"type":"integer", "default": 30}
      }
    }
  },
  "required": ["symbol","timeframe","sessions","indicators","conditions","strategy"]
}
```

**Example (XAUUSD/H1/London+NY):**
```json
{
  "symbol": "XAUUSD",
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
    "exit": ["rsi_gt_70", "price_close_lt_ema_slow"],
    "strong": ["macd_hist_gt_0", "atr_above_median"],
    "weak": ["long_upper_wick", "divergence_bearish"]
  },
  "strategy": {"direction": "long", "min_rr": 2.0, "news_embargo_minutes": 30}
}
```