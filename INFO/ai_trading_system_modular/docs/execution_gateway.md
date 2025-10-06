# Execution & Order Routing (FastAPI + MT5)

## Sample FastAPI Order Endpoint
```python
from fastapi import FastAPI
from pydantic import BaseModel
import MetaTrader5 as mt5

app = FastAPI()

class OrderRequest(BaseModel):
    symbol: str
    volume: float
    action: str  # "buy" or "sell"
    sl: float
    tp: float

@app.post("/order")
def place_order(req: OrderRequest):
    if not mt5.initialize():
        return {"status": "error", "msg": "MT5 init failed"}
    type_f = mt5.ORDER_TYPE_BUY if req.action=="buy" else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": req.symbol,
        "volume": req.volume,
        "type": type_f,
        "sl": req.sl,
        "tp": req.tp,
        "deviation": 20,
        "magic": 12345
    }
    result = mt5.order_send(request)
    mt5.shutdown()
    return {"status": int(result.retcode), "msg": str(result)}
```
