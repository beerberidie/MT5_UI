# Daily Market Data System for AI Trader

This document consolidates the full setup, prompt, schema, and alias mapping for generating, validating, and storing structured daily market data for your AI trading system. It ensures efficiency, repeatability, and consistency when integrating with MT5.

---

## 1. Supported Symbols

These are the instruments you require every day:

- EURUSD  
- USDJPY  
- GBPUSD  
- USDCHF  
- USDCAD  
- AUDUSD  
- NZDUSD  
- EURGBP  
- EURCHF  
- EURJPY  
- GOLD (XAUUSD)  
- SILVER (XAGUSD)  
- CrudeOIL (WTICOUSD/USOIL)  
- BTCUSD  
- ETHUSD  
- US_500 (SPX500)  
- US_30 (DJ30)  
- US_TECH100 (NAS100)  
- GERMANY_40 (DAX40)  
- UK_100 (FTSE100)  
- FRANCE_40 (CAC40)  
- ITALY_40 (MIB40)  
- JAPAN_225 (NIK225)

---

## 2. Daily Data Categories

Each symbol requires:

1. **Market Snapshot** – last price, % change, pivots, volatility.  
2. **Technicals** – EMA trends, RSI, MACD.  
3. **Calendar Events** – top 1–2 relevant upcoming releases.  
4. **Headlines** – top 1–2 news items.  
5. **Sentiment** – retail positioning, bias.  
6. **Strategy Bias** – concise trade condition (≤140 chars).  
7. **Macro Section** – DXY, US10Y, VIX.  
8. **Themes** – 1–2 daily macro themes.  
9. **Self-Audit** – ensures no symbol omissions and validates critical fields.

---

## 3. Master Daily Prompt

```text
You are a Financial Data Generator.

Return valid JSON only. Do not include markdown fences, comments, explanations, links, or citations. 
If you are unsure about a value, use `null` (numbers) or "N/A" (strings). Never omit a required field or symbol.

REQUIRED SYMBOLS (order must be preserved; exactly 23):
EURUSD, USDJPY, GBPUSD, USDCHF, USDCAD, AUDUSD, NZDUSD, EURGBP, EURCHF, EURJPY, GOLD, SILVER, CrudeOIL, BTCUSD, ETHUSD, US_500, US_30, US_TECH100, GERMANY_40, UK_100, FRANCE_40, ITALY_40, JAPAN_225

SCHEMA (strict):
{
  "schemaVersion": "1.0.1",
  "asOf": "YYYY-MM-DDTHH:MM:SS+02:00",
  "symbols": [
    {
      "symbol": "string",
      "last": number,
      "changePct": number,
      "pivot": {"P": number, "S1": number, "R1": number},
      "technicals": {
        "ema1h": "up|down|flat",
        "ema4h": "up|down|flat",
        "rsi": number|null,
        "macd": "bullish|bearish|neutral"
      },
      "calendar": [
        {"timeISO": "YYYY-MM-DDTHH:MM:SS+02:00", "event": "string", "impact": "high|medium|low"}
      ],
      "headlines": ["string"],
      "sentiment": {"retail": "string", "bias": "bullish|bearish|neutral"},
      "strategyBias": "string"
    }
  ],
  "macro": {
    "dxy": {"last": number, "changePct": number, "trend1h": "up|down|flat", "trend4h": "up|down|flat"},
    "us10y": {"last": number, "changeBp": number, "trend1h": "up|down|flat", "trend4h": "up|down|flat"},
    "vix": number
  },
  "themes": ["string", "string"],
  "selfAudit": {
    "expectedSymbolCount": 23,
    "actualSymbolCount": number,
    "missingSymbols": ["string"],
    "nullCriticalFields": {"last": number, "changePct": number, "pivotP": number, "pivotS1": number, "pivotR1": number}
  }
}
```

---

## 4. Symbol Alias Map for MT5

```json
{
  "EURUSD": ["EURUSD", "EURUSDm", "EURUSD.pro"],
  "USDJPY": ["USDJPY", "USDJPYm", "USDJPY.pro"],
  "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD.pro"],
  "USDCHF": ["USDCHF", "USDCHFm", "USDCHF.pro"],
  "USDCAD": ["USDCAD", "USDCADm", "USDCAD.pro"],
  "AUDUSD": ["AUDUSD", "AUDUSDm", "AUDUSD.pro"],
  "NZDUSD": ["NZDUSD", "NZDUSDm", "NZDUSD.pro"],
  "EURGBP": ["EURGBP", "EURGBPm", "EURGBP.pro"],
  "EURCHF": ["EURCHF", "EURCHFm", "EURCHF.pro"],
  "EURJPY": ["EURJPY", "EURJPYm", "EURJPY.pro"],
  "GOLD": ["XAUUSD", "GOLD", "XAUUSDm", "XAUUSD.pro"],
  "SILVER": ["XAGUSD", "SILVER", "XAGUSDm", "XAGUSD.pro"],
  "CrudeOIL": ["WTICOUSD", "USOIL", "OIL", "OILm"],
  "BTCUSD": ["BTCUSD", "BTCUSDm", "BTCUSD.pro"],
  "ETHUSD": ["ETHUSD", "ETHUSDm", "ETHUSD.pro"],
  "US_500": ["US500", "SPX500", "SP500", "SPX500m"],
  "US_30": ["US30", "DJ30", "DOW30", "US30m"],
  "US_TECH100": ["NAS100", "US100", "NDX100", "NAS100m"],
  "GERMANY_40": ["GER40", "DAX40", "DE40", "GER40m"],
  "UK_100": ["UK100", "FTSE100", "GB100", "UK100m"],
  "FRANCE_40": ["FRA40", "CAC40", "FR40", "FRA40m"],
  "ITALY_40": ["ITA40", "MIB40", "IT40", "ITA40m"],
  "JAPAN_225": ["JPN225", "NIK225", "JP225", "JPN225m"]
}
```

---

## 5. Validator & CSV Writer (Python)

Use this after fetching JSON to validate, flatten, and save data into a CSV.

```python
import json, uuid, csv

REQUIRED = ["EURUSD","USDJPY","GBPUSD","USDCHF","USDCAD","AUDUSD","NZDUSD",
            "EURGBP","EURCHF","EURJPY","GOLD","SILVER","CrudeOIL",
            "BTCUSD","ETHUSD","US_500","US_30","US_TECH100",
            "GERMANY_40","UK_100","FRANCE_40","ITALY_40","JAPAN_225"]

def validate_payload(payload: dict):
    assert payload.get("schemaVersion") in ("1.0.1","1.0.0")
    symbols = payload.get("symbols"); assert len(symbols)==23
    for i,s in enumerate(symbols):
        assert s["symbol"] == REQUIRED[i]
        assert isinstance(s["last"], (int,float))
        assert isinstance(s["pivot"]["P"], (int,float))
    sa = payload["selfAudit"]
    assert sa["actualSymbolCount"]==23
    assert all(v==0 for v in sa["nullCriticalFields"].values())
    return True

def flatten_rows(payload: dict):
    run_id = str(uuid.uuid4())
    return [
        {
            "runId": run_id, "asOf": payload["asOf"], "symbol": s["symbol"],
            "last": s["last"], "changePct": s["changePct"],
            "pivot_P": s["pivot"]["P"], "pivot_S1": s["pivot"]["S1"], "pivot_R1": s["pivot"]["R1"],
            "ema1h": s["technicals"]["ema1h"], "ema4h": s["technicals"]["ema4h"],
            "rsi": s["technicals"]["rsi"], "macd": s["technicals"]["macd"],
            "headline": s["headlines"][0] if s["headlines"] else "",
            "cal_event": s["calendar"][0]["event"] if s["calendar"] else "",
            "cal_impact": s["calendar"][0]["impact"] if s["calendar"] else "",
            "retail": s["sentiment"]["retail"], "bias": s["sentiment"]["bias"],
            "strategyBias": s["strategyBias"]
        }
        for s in payload["symbols"]
    ]

def write_csv(rows, path="daily_symbols.csv"):
    import os
    fieldnames = list(rows[0].keys())
    mode = "a" if os.path.exists(path) else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode=="w": writer.writeheader()
        writer.writerows(rows)
```

---

## 6. Workflow Summary

1. Run the **Master Prompt** daily (10:00 SA time recommended).  
2. Validate JSON against schema & audit block.  
3. Map symbols to broker aliases (see alias map).  
4. Store into CSV/DB with `validate_payload` + `flatten_rows`.  
5. Use DB rows for AI trader signals, backtests, and risk dashboards.  

This creates a **repeatable, consistent, database-ready feed** to elevate your AI trader's accuracy and reliability.
