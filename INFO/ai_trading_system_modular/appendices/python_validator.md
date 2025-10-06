# Python Validator & CSV Writer

```python
import json, uuid, csv, os

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
    fieldnames = list(rows[0].keys())
    mode = "a" if os.path.exists(path) else "w"
    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode=="w": writer.writeheader()
        writer.writerows(rows)
```
