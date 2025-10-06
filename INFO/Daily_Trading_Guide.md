# Daily Trading Research & Execution Guide

## Overview
This document consolidates all trading-related instructions, prompts, and rules tailored for Garrison's trading setup. The objective is to grow a $70 equity account towards $200 (approx. R2,000) within a week, by executing **one high-quality trade per day** with strict risk management.

---

## Account Setup & Goals
- **Starting Equity:** $70 (≈ R1,300)
- **Weekly Goal:** $200 (≈ R2,000)
- **Trading Frequency:** 1 trade per day at a fixed time (recommended: 09:30–10:00 SA time, before NY open).
- **Target Risk:** 2–5% per trade ($1.40–$3.50 maximum risk).
- **Position Sizing:** Adjust lot size so stop loss = risk.
- **Trade Filter:** Only take setups with Risk/Reward ≥ 1:2.

---

## Target Symbols
Focus only on instruments with sufficient volatility and affordability given margin constraints:
- **Gold (XAUUSD):** High volatility, strong daily moves ($5–10 per session).
- **EURUSD / GBPUSD:** Affordable margin, smaller daily ranges, good for tight stops.
- **US500 (S&P 500 Index):** Moves steadily on macro and sentiment shifts.
- **BTCUSD / ETHUSD:** Only if stop loss distance is small relative to risk budget.

---

## Daily Perplexity Prompt
Run this prompt once a day to generate market research and the trade setup:

```
You are my trading research assistant. Today’s trading equity is $70. My target for the end of the week is $200. I want one trade today, only if the risk/reward ratio is at least 1:2, and if the stop loss is reasonable relative to my account size.

Please:
1. Analyse today’s market conditions (include: DXY, US10Y yields, VIX, gold, major FX pairs like EURUSD, GBPUSD, indices like US500, and BTC/ETH).
2. Summarize global sentiment (risk-on/risk-off).
3. Identify the single best trade opportunity for today that matches my range (low margin, affordable with $70 equity).
4. Provide exact levels:
   - Entry price
   - Stop loss price
   - Take profit price
5. Justify the trade with both technicals (EMA, RSI, MACD, pivot points, trendlines) and fundamentals (news, macro data, central bank sentiment).
6. Keep the position sizing to risk max 2–5% of account ($1.50–$3.50).
7. Present output in this structured JSON:

{
  "symbol": "",
  "direction": "buy/sell",
  "entry": "",
  "stop_loss": "",
  "take_profit": "",
  "risk_reward": "",
  "reasoning": {
    "technicals": "",
    "fundamentals": "",
    "sentiment": ""
  }
}
```

---

## Execution Rulebook
1. **Run Research:** At set time, run the Perplexity prompt.
2. **Check JSON Output:** Confirm the symbol, entry, SL, TP, RR ≥ 1:2.
3. **Position Size:** Calculate lot size so that stop loss = $1.40–$3.50 risk.
4. **Confirm Trade:** Ensure fundamentals don’t contradict technical setup.
5. **Place Order in MT5.**
6. **Log Trade:** Record in tracker (symbol, entry, SL, TP, RR, result).

---

## Capital Preservation
- **No trade is better than a bad trade.** If no valid setup appears, SKIP.
- Avoid widening stops. If SL is hit, accept the loss.
- Reassess daily – focus on survival.

---

## Aggression vs Safety Modes
- **Safety Mode:** 2% risk per trade, focus on survival and slow compounding.
- **Aggressive Mode:** Up to 5% per trade. If first trades of the week win, scale risk slightly higher to accelerate growth.
- **Caution:** Growing $70 → $200 in one week requires extreme performance (approx. 3x). This carries high blow-up risk.

---

## Logging Template (Spreadsheet Example)
| Date | Symbol | Direction | Entry | Stop Loss | Take Profit | RR | Risk % | Result | Notes |
|------|---------|-----------|-------|-----------|-------------|----|--------|--------|-------|
| 2025-10-02 | XAUUSD | Buy | 1850.50 | 1845.00 | 1861.00 | 1:2.1 | 3% | -3% | SL Hit |

---

## Final Notes
- Consistency and discipline are critical.
- This guide gives structure for research, execution, and risk control.
- Short-term aggressive goals are high risk – capital preservation must remain a priority.
