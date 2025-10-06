# Per‑Symbol Knowledge Profile — JSON Template

Fill this once per symbol. The engine and UI use it to filter sessions, set default styles, and apply management rules.

```json
{
  "symbol": "XAUUSD",
  "bestSessions": ["London","NewYork"],
  "bestTimeframes": ["M15","H1","H4"],
  "externalDrivers": ["DXY","US10Y","VIX","FedSpeeches"],
  "style": {"bias": "trend-follow", "rrTarget": 2.0, "maxRiskPct": 0.03},
  "management": {
    "breakevenAfterRR": 1.0,
    "partialAtRR": 1.5,
    "trailUsingATR": true,
    "atrMultiplier": 1.5
  },
  "invalidations": ["close_below_ema_slow", "macro_contra_surge"]
}
```
