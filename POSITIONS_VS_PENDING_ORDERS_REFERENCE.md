# Positions vs Pending Orders - Technical Reference

## Quick Comparison Table

| Aspect | **Open Positions** | **Pending Orders** |
|--------|-------------------|-------------------|
| **Definition** | Active trades already in the market | Orders waiting to be triggered at a specific price |
| **MT5 API Method** | `mt5.positions_get()` | `mt5.orders_get()` |
| **Backend Method** | `MT5Client.positions()` | `MT5Client.orders_get()` |
| **API Endpoint** | `GET /api/positions` | `GET /api/orders` |
| **Frontend Method** | `getPositions()` | `getPendingOrders()` |
| **Current UI Location** | Right panel (always visible) | Activity tab → Orders (hidden) |
| **Status** | Filled/Active | Pending/Waiting |
| **Has P/L** | ✅ Yes (real-time) | ❌ No (not executed yet) |
| **Price Field** | `price_open` (entry price) | `price_open` (trigger price) |
| **Can be Modified** | ✅ SL/TP only | ✅ Price, SL, TP, expiration |
| **Can be Closed** | ✅ Via `position_close()` | ✅ Via `order_cancel()` |
| **Affects Margin** | ✅ Yes (uses margin) | ❌ No (no margin until triggered) |
| **Affects Equity** | ✅ Yes (P/L affects equity) | ❌ No |

## Order Type Constants

### Position Types (Active Trades)
```python
# From MetaTrader5 module
POSITION_TYPE_BUY = 0   # Long position
POSITION_TYPE_SELL = 1  # Short position
```

### Order Types (Pending Orders)
```python
# From MetaTrader5 module
ORDER_TYPE_BUY = 0              # Market buy (instant execution)
ORDER_TYPE_SELL = 1             # Market sell (instant execution)
ORDER_TYPE_BUY_LIMIT = 2        # Buy when price drops to level
ORDER_TYPE_SELL_LIMIT = 3       # Sell when price rises to level
ORDER_TYPE_BUY_STOP = 4         # Buy when price rises to level
ORDER_TYPE_SELL_STOP = 5        # Sell when price drops to level
ORDER_TYPE_BUY_STOP_LIMIT = 6   # Combination order
ORDER_TYPE_SELL_STOP_LIMIT = 7  # Combination order
```

## Data Structure Examples

### Position Object (from `mt5.positions_get()`)
```python
{
    'ticket': 123456789,           # Position ticket
    'time': 1640995200,            # Open time (Unix timestamp)
    'time_msc': 1640995200000,     # Open time (milliseconds)
    'time_update': 1640995260,     # Last update time
    'time_update_msc': 1640995260000,
    'type': 0,                     # 0=BUY, 1=SELL
    'magic': 0,                    # Expert Advisor ID
    'identifier': 123456789,       # Position identifier
    'reason': 0,                   # Position open reason
    'volume': 0.1,                 # Position volume (lots)
    'price_open': 1.1300,          # Open price
    'sl': 1.1250,                  # Stop Loss
    'tp': 1.1400,                  # Take Profit
    'price_current': 1.1320,       # Current price
    'swap': -0.50,                 # Swap (overnight fee)
    'profit': 20.00,               # Current profit/loss
    'symbol': 'EURUSD',            # Trading symbol
    'comment': 'Tradecraft Console',
    'external_id': ''
}
```

### Pending Order Object (from `mt5.orders_get()`)
```python
{
    'ticket': 987654321,           # Order ticket
    'time_setup': 1640995200,      # Order placement time
    'time_setup_msc': 1640995200000,
    'time_expiration': 0,          # Expiration time (0 = GTC)
    'type': 2,                     # Order type (2=BUY_LIMIT)
    'type_time': 0,                # Order lifetime type
    'type_filling': 0,             # Order filling type
    'state': 1,                    # Order state (1=PLACED)
    'magic': 0,                    # Expert Advisor ID
    'position_id': 0,              # Related position ID
    'position_by_id': 0,           # Opposite position ID
    'reason': 0,                   # Order placement reason
    'volume_initial': 0.1,         # Initial volume
    'volume_current': 0.1,         # Current volume
    'price_open': 1.1000,          # Order trigger price
    'sl': 1.0950,                  # Stop Loss
    'tp': 1.1100,                  # Take Profit
    'price_current': 1.1320,       # Current market price
    'price_stoplimit': 0.0,        # Stop limit price
    'symbol': 'EURUSD',            # Trading symbol
    'comment': 'Pending order',
    'external_id': ''
}
```

## Backend Implementation

### MT5Client Methods

```python
# backend/mt5_client.py

def positions(self):
    """Get all active positions (filled orders)."""
    self.init()
    res = mt5.positions_get()
    return [p._asdict() for p in res] if res else []

def orders_get(self, symbol: str = None, ticket: int = None) -> list:
    """Get active pending orders with optional filtering."""
    self.init()
    if ticket:
        orders = mt5.orders_get(ticket=ticket)
    elif symbol:
        orders = mt5.orders_get(symbol=symbol)
    else:
        orders = mt5.orders_get()
    return [order._asdict() for order in orders] if orders else []

def orders_total(self) -> int:
    """Get total number of active pending orders."""
    self.init()
    return mt5.orders_total()
```

### API Endpoints

```python
# backend/app.py

@app.get("/api/positions")
@limiter.limit("60/minute")
def get_positions(request: Request):
    """Get all active positions."""
    try:
        return mt5.positions()
    except Exception as e:
        _log_error("positions", str(e))
        return []

@app.get("/api/orders")
@limiter.limit("60/minute")
def get_pending_orders(request: Request, symbol: str = None, ticket: int = None):
    """Get active pending orders with optional filtering."""
    try:
        orders = mt5.orders_get(symbol=symbol, ticket=ticket)
        # Log to CSV for audit trail
        if orders:
            for order in orders:
                append_csv(
                    os.path.join(LOG_DIR, "orders_get.csv"),
                    ["ts_utc", "ticket", "symbol", "type", "volume", "price"],
                    [utcnow_iso(), order.get("ticket"), order.get("symbol"), 
                     order.get("type"), order.get("volume_current"), order.get("price_open")]
                )
        return orders
    except Exception as e:
        _log_error("orders_get", str(e))
        return []
```

## Frontend Implementation

### API Client Methods

```typescript
// tradecraft-console-main/src/lib/api.ts

export async function getPositions(): Promise<Position[]> {
  const rows = await apiCall<PositionResponse[]>(`/api/positions`);
  return (rows || []).map((p: any) => ({
    ticket: p.ticket ?? p.position ?? undefined,
    symbol: p.symbol,
    type: p.type,
    volume: Number(p.volume || 0),
    profit: Number(p.profit || 0),  // Only positions have P/L
  }));
}

export async function getPendingOrders(): Promise<any[]> {
  return apiCall(`/api/orders`);
}

export async function cancelPendingOrder(ticket: number | string): Promise<any> {
  return apiCall(`/api/orders/${ticket}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  });
}

export async function modifyPendingOrder(
  ticket: number | string,
  payload: { price?: number; sl?: number; tp?: number; expiration?: number }
): Promise<any> {
  return apiCall(`/api/orders/${ticket}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
```

## Trading Lifecycle

### Scenario 1: Market Order → Position
```
1. User clicks "BUY" button
2. Frontend calls postOrder({ side: 'buy', ... })
3. Backend calls mt5.order_send() with ORDER_TYPE_BUY
4. Order executes immediately at market price
5. Position appears in mt5.positions_get()
6. Frontend displays in "Open Positions" panel
```

### Scenario 2: Pending Order → Position
```
1. User clicks "Place Pending" button
2. Frontend calls createPendingOrder({ order_type: 'buy_limit', price: 1.1000, ... })
3. Backend calls mt5.order_send() with ORDER_TYPE_BUY_LIMIT
4. Order appears in mt5.orders_get() (pending)
5. Frontend displays in "Pending Orders" section
6. When market price reaches 1.1000:
   - Order triggers automatically
   - Order disappears from mt5.orders_get()
   - Position appears in mt5.positions_get()
   - Frontend moves from "Pending Orders" to "Open Positions"
```

### Scenario 3: Cancel Pending Order
```
1. User clicks "Cancel" button on pending order
2. Frontend calls cancelPendingOrder(ticket)
3. Backend calls mt5.order_cancel(ticket)
4. Order disappears from mt5.orders_get()
5. Frontend removes from "Pending Orders" section
```

## Common Pitfalls

### ❌ Mistake 1: Mixing Position and Order Tickets
```python
# WRONG: Trying to close a pending order as a position
mt5.position_close(pending_order_ticket)  # Will fail!

# CORRECT: Cancel pending order
mt5.order_cancel(pending_order_ticket)
```

### ❌ Mistake 2: Expecting P/L on Pending Orders
```typescript
// WRONG: Pending orders don't have profit
const profit = pendingOrder.profit;  // undefined!

// CORRECT: Only positions have profit
const profit = position.profit;  // Works!
```

### ❌ Mistake 3: Using Wrong Price Field
```typescript
// WRONG: Using price_current for pending order trigger price
const triggerPrice = pendingOrder.price_current;  // This is market price!

// CORRECT: Use price_open for trigger price
const triggerPrice = pendingOrder.price_open;  // This is the trigger price
```

## Best Practices

### ✅ Always Separate Positions and Orders in UI
- Use distinct visual sections
- Different color schemes (green for positions, yellow for pending)
- Clear labels ("Open Positions" vs "Pending Orders")

### ✅ Show Relevant Actions for Each Type
- **Positions**: Close, Modify SL/TP
- **Pending Orders**: Cancel, Modify Price/SL/TP

### ✅ Auto-Refresh Both Lists
```typescript
useEffect(() => {
  const fetchData = async () => {
    const [positions, orders] = await Promise.all([
      getPositions(),
      getPendingOrders()
    ]);
    setPositions(positions);
    setPendingOrders(orders);
  };
  
  fetchData();
  const interval = setInterval(fetchData, 2000);
  return () => clearInterval(interval);
}, []);
```

### ✅ Handle State Transitions
When a pending order triggers:
- It disappears from `orders_get()`
- It appears in `positions_get()`
- UI should reflect this automatically via polling

## Testing Scenarios

### Test 1: Create and Cancel Pending Order
```
1. Place BUY LIMIT at 1.1000 (current price 1.1050)
2. Verify order appears in pending orders list
3. Verify order does NOT appear in positions list
4. Cancel the order
5. Verify order disappears from pending orders list
```

### Test 2: Pending Order Triggers
```
1. Place BUY STOP at 1.1100 (current price 1.1050)
2. Wait for price to reach 1.1100
3. Verify order disappears from pending orders list
4. Verify position appears in positions list
5. Verify position has P/L
```

### Test 3: Modify Pending Order
```
1. Place SELL LIMIT at 1.1100
2. Modify price to 1.1150
3. Verify updated price in pending orders list
4. Modify SL/TP
5. Verify updated SL/TP in pending orders list
```

## References

- **MT5 Python Documentation**: https://www.mql5.com/en/docs/python_metatrader5
- **Order Types**: https://www.mql5.com/en/docs/constants/tradingconstants/orderproperties
- **Position Properties**: https://www.mql5.com/en/docs/constants/tradingconstants/positionproperties

