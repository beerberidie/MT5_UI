# Pending Orders UI Enhancement Plan

## Problem Statement
Pending orders are currently hidden in the Activity tab, requiring users to navigate away from the main trading view to see them. This is suboptimal for active traders who need to monitor both open positions and pending orders simultaneously.

## Proposed Solution
Add a "Pending Orders" section directly below "Open Positions" in the right panel, making both types of trading activity visible at all times.

## Implementation Plan

### Step 1: Add State for Pending Orders
```typescript
// In TradingDashboard.tsx, add state near line 60
const [pendingOrders, setPendingOrders] = useState<any[]>([]);
```

### Step 2: Fetch Pending Orders in useEffect
```typescript
// In the main useEffect (around line 200), add:
useEffect(() => {
  const fetchData = async () => {
    try {
      // Existing code for account, symbols, positions...
      
      // Add pending orders fetch
      const pend = await getPendingOrders();
      setPendingOrders(pend || []);
    } catch (err) {
      console.error('Error fetching data:', err);
    }
  };
  
  fetchData();
  const interval = setInterval(fetchData, 2000); // Refresh every 2s
  return () => clearInterval(interval);
}, []);
```

### Step 3: Add Pending Orders Section to Right Panel

**Location:** After the "Open Positions" section (after line 1388)

```tsx
{/* Pending Orders Section - NEW */}
<div className="border-b border-border">
  <div className="px-4 py-3 border-b border-border flex items-center justify-between">
    <h3 className="font-medium text-text-primary">
      Pending Orders
      {pendingOrders.length > 0 && (
        <span className="ml-2 text-xs text-text-muted">({pendingOrders.length})</span>
      )}
    </h3>
  </div>
  <div className="p-4 max-h-64 overflow-auto">
    <table className="trading-table w-full text-xs">
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Type</th>
          <th>Volume</th>
          <th>Price</th>
          <th className="w-8"><span className="sr-only">Actions</span></th>
        </tr>
      </thead>
      <tbody>
        {pendingOrders.length === 0 ? (
          <tr>
            <td colSpan={5} className="text-center text-text-muted py-4">
              No pending orders
            </td>
          </tr>
        ) : (
          pendingOrders.map((order) => {
            const orderType = getOrderTypeLabel(order.type);
            const price = order.price_open ?? order.price ?? order.price_current ?? 0;
            
            return (
              <tr key={order.ticket || order.order || Math.random()}>
                <td>{order.symbol ?? ''}</td>
                <td className="text-xs">
                  <span className={`px-1.5 py-0.5 rounded ${
                    orderType.includes('BUY') ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'
                  }`}>
                    {orderType}
                  </span>
                </td>
                <td className="text-right">{Number(order.volume || 0).toFixed(2)}</td>
                <td className="text-right">{Number(price).toFixed(5)}</td>
                <td className="text-center">
                  <button
                    type="button"
                    onClick={() => handleCancelPendingOrder(order)}
                    className="p-1 hover:bg-destructive/10 rounded transition-colors text-text-muted hover:text-destructive"
                    title="Cancel pending order"
                    aria-label={`Cancel order ${order.ticket}`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </td>
              </tr>
            );
          })
        )}
      </tbody>
    </table>
  </div>
</div>
```

### Step 4: Add Helper Function for Order Type Labels

```typescript
// Add near other helper functions (around line 400)
function getOrderTypeLabel(type: number | string): string {
  const typeNum = typeof type === 'string' ? parseInt(type) : type;
  const labels: Record<number, string> = {
    0: 'BUY',
    1: 'SELL',
    2: 'BUY LIMIT',
    3: 'SELL LIMIT',
    4: 'BUY STOP',
    5: 'SELL STOP',
    6: 'BUY STOP LIMIT',
    7: 'SELL STOP LIMIT',
  };
  return labels[typeNum] || `TYPE ${typeNum}`;
}
```

### Step 5: Add Cancel Pending Order Handler

```typescript
// Add near other handlers (around line 450)
async function handleCancelPendingOrder(order: any) {
  const ticket = order.ticket ?? order.order;
  if (!ticket) {
    toast({
      title: "Error",
      description: "Invalid order ticket",
      variant: "destructive",
    });
    return;
  }

  try {
    setOut(`Cancelling pending order ${ticket}...`);
    const result = await cancelPendingOrder(ticket);
    
    if (result && (result.result_code || 0) >= 10000) {
      toast({
        title: "Success",
        description: `Pending order ${ticket} cancelled`,
      });
      setOut(`Order ${ticket} cancelled successfully`);
      
      // Refresh pending orders
      const pend = await getPendingOrders();
      setPendingOrders(pend || []);
    } else {
      toast({
        title: "Failed",
        description: result?.error?.message || "Failed to cancel order",
        variant: "destructive",
      });
      setOut(`Cancel failed: ${result?.error?.message || 'Unknown error'}`);
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    toast({
      title: "Error",
      description: msg,
      variant: "destructive",
    });
    setOut(`Cancel error: ${msg}`);
  }
}
```

## Visual Mockup

```
┌─────────────────────────────────────┐
│ Right Panel (w-96)                  │
├─────────────────────────────────────┤
│ Open Positions                      │
│ ┌─────────────────────────────────┐ │
│ │ EURUSD  BUY   0.10  +5.20  [X] │ │
│ │ GBPUSD  SELL  0.05  -2.10  [X] │ │
│ │ GOLD    BUY   0.01  +12.5  [X] │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ Pending Orders (2)          ← NEW   │
│ ┌─────────────────────────────────┐ │
│ │ EURUSD  BUY LIMIT  0.10  1.100 │ │
│ │ GOLD    SELL STOP  0.01  2050  │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ Activity                            │
│ ┌─────────────────────────────────┐ │
│ │ [Deals] [Orders] [Analysis]     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Benefits

1. **Immediate Visibility**: Traders see both positions and pending orders without tab switching
2. **Consistent UX**: Same layout pattern as positions (table with action buttons)
3. **Quick Actions**: Cancel pending orders with one click
4. **Real-time Updates**: Auto-refresh every 2 seconds with positions
5. **Space Efficient**: Collapsible section, scrollable if many orders

## Alternative: Collapsible Section

If space is a concern, make it collapsible:

```tsx
const [showPendingOrders, setShowPendingOrders] = useState(true);

// In the header:
<div className="px-4 py-3 border-b border-border flex items-center justify-between">
  <h3 className="font-medium text-text-primary">
    Pending Orders ({pendingOrders.length})
  </h3>
  <button
    onClick={() => setShowPendingOrders(!showPendingOrders)}
    className="text-text-muted hover:text-text-primary"
  >
    {showPendingOrders ? <ChevronDown /> : <ChevronRight />}
  </button>
</div>

{showPendingOrders && (
  <div className="p-4 max-h-64 overflow-auto">
    {/* Table content */}
  </div>
)}
```

## Testing Checklist

- [ ] Pending orders display correctly when present
- [ ] "No pending orders" message shows when empty
- [ ] Order type labels are correct (BUY LIMIT, SELL STOP, etc.)
- [ ] Cancel button works and refreshes the list
- [ ] Auto-refresh updates pending orders every 2 seconds
- [ ] Scrolling works when many pending orders
- [ ] No performance issues with frequent updates
- [ ] Error handling for failed API calls

## Files to Modify

1. `tradecraft-console-main/tradecraft-console-main/src/components/TradingDashboard.tsx`
   - Add `pendingOrders` state
   - Add pending orders fetch in useEffect
   - Add pending orders section to right panel
   - Add `getOrderTypeLabel` helper
   - Add `handleCancelPendingOrder` handler

## Estimated Effort

- **Time**: 30-45 minutes
- **Complexity**: Low (reusing existing patterns)
- **Risk**: Low (additive change, no breaking changes)

