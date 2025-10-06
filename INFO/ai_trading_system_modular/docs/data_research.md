# Data & Research Layer

## Daily Market Data JSON Schema
```json
{
  "schemaVersion": "1.0.1",
  "asOf": "YYYY-MM-DDTHH:MM:SS+02:00",
  "symbols": [
    {
      "symbol": "EURUSD",
      "last": 1.1001,
      "changePct": -0.2,
      "pivot": {"P": 1.1010, "S1": 1.0980, "R1": 1.1040},
      "technicals": {"ema1h": "up", "ema4h": "flat", "rsi": 52, "macd": "bullish"},
      "calendar": [{"timeISO": "2025-10-02T14:30:00+02:00", "event": "US CPI", "impact": "high"}],
      "headlines": ["Fed cautious on inflation"],
      "sentiment": {"retail": "60% long", "bias": "bearish"},
      "strategyBias": "short below 1.1000"
    }
  ],
  "macro": {
    "dxy": {"last": 106.5, "changePct": 0.2, "trend1h": "up", "trend4h": "up"},
    "us10y": {"last": 4.2, "changeBp": 2, "trend1h": "up", "trend4h": "flat"},
    "vix": 18.2
  },
  "themes": ["Fed hawkish tone", "Oil supply risks"],
  "selfAudit": {
    "expectedSymbolCount": 23,
    "actualSymbolCount": 23,
    "missingSymbols": [],
    "nullCriticalFields": {"last": 0, "changePct": 0, "pivotP": 0, "pivotS1": 0, "pivotR1": 0}
  }
}
```

## Symbol Alias Map (MT5)
```json
{
  "EURUSD": ["EURUSD","EURUSDm","EURUSD.pro"],
  "USDJPY": ["USDJPY","USDJPYm","USDJPY.pro"],
  "GBPUSD": ["GBPUSD","GBPUSDm","GBPUSD.pro"],
  "USDCHF": ["USDCHF","USDCHFm","USDCHF.pro"],
  "USDCAD": ["USDCAD","USDCADm","USDCAD.pro"],
  "AUDUSD": ["AUDUSD","AUDUSDm","AUDUSD.pro"],
  "NZDUSD": ["NZDUSD","NZDUSDm","NZDUSD.pro"],
  "EURGBP": ["EURGBP","EURGBPm","EURGBP.pro"],
  "EURCHF": ["EURCHF","EURCHFm","EURCHF.pro"],
  "EURJPY": ["EURJPY","EURJPYm","EURJPY.pro"],
  "GOLD": ["XAUUSD","GOLD","XAUUSDm","XAUUSD.pro"],
  "SILVER": ["XAGUSD","SILVER","XAGUSDm","XAGUSD.pro"],
  "CrudeOIL": ["WTICOUSD","USOIL","OIL","OILm"],
  "BTCUSD": ["BTCUSD","BTCUSDm","BTCUSD.pro"],
  "ETHUSD": ["ETHUSD","ETHUSDm","ETHUSD.pro"],
  "US_500": ["US500","SPX500","SP500","SPX500m"],
  "US_30": ["US30","DJ30","DOW30","US30m"],
  "US_TECH100": ["NAS100","US100","NDX100","NAS100m"],
  "GERMANY_40": ["GER40","DAX40","DE40","GER40m"],
  "UK_100": ["UK100","FTSE100","GB100","UK100m"],
  "FRANCE_40": ["FRA40","CAC40","FR40","FRA40m"],
  "ITALY_40": ["ITA40","MIB40","IT40","ITA40m"],
  "JAPAN_225": ["JPN225","NIK225","JP225","JPN225m"]
}
```

## Ingest Pipeline (Zero/Low-Cost)
- Sources: Yahoo, Stooq, Dukascopy, FRED, TradingEconomics, RSS/NewsAPI.
- Storage: CSV or Parquet partitioned by symbol/date; UTC timestamps.
- Validation: monotonic time, non-negative volume, outlier clamps; self-audit.
- Retention & Backups: ZIP with checksums.

## Perplexity (Zero-Cost) Workflow
- Quick searches/Spaces unlimited; capped Pro/Deep daily — plan prompts.
- Clone yesterday’s Space, change date, paste URLs for context.
- Cron: 07:00 SAST calendar pull; cache answers to avoid rate limits.
