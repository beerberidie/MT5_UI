# Strategy Edge & Daily Execution

## Core Rules
- Exactly **1 trade/day** at **09:30–10:00 SAST**.
- Risk per trade: **2–5%** of equity (micro accounts start at 2%).
- **Minimum 1:2** risk/reward; skip if not available.
- Confirm technicals **and** fundamentals; avoid trading into high-impact releases unless explicitly planned.

## Daily Perplexity Prompt
```text
You are my trading research assistant. Equity = $70. Target = $200 by week’s end.
Give one trade today with ≥1:2 risk/reward.

Analyse: DXY, US10Y, VIX, gold, EURUSD, GBPUSD, US500, BTC/ETH.
Return JSON:
{ "symbol": "", "direction": "buy/sell", "entry": "", "stop_loss": "", "take_profit": "", "risk_reward": "", "reasoning": { "technicals": "", "fundamentals": "", "sentiment": "" } }
```

## Gold Trading Times (SAST)
- **Best:** 09:00–10:30 and 14:00–18:00 (London/NY overlap).
- **Worst:** 00:00–07:00; after 20:00 (NY fade).
- **Sizing:** Prefer **0.001 lots** for $100 balance; 0.01 lots only at strong S/R with tight stops.
- **Targets:** Aim for **1:2** or **1:3** R:R.
