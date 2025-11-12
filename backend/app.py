import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Union

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import (
    API_HOST,
    API_PORT,
    FRONTEND_ORIGIN,
    FRONTEND_ORIGINS,
    DATA_DIR,
    LOG_DIR,
    AUGMENT_API_KEY,
)
from .csv_io import append_csv, utcnow_iso, read_csv_rows
from .mt5_client import MT5Client
from .models import (
    OrderRequest,
    PendingOrderRequest,
    HistoricalBarsRequest,
    HistoricalTicksRequest,
    TradingHistoryRequest,
)
from .risk import risk_limits, symbol_map, sessions_map
from . import ai_routes
from . import settings_routes
from . import data_routes
from . import monitoring_routes
from . import celery_routes
from . import decision_history_routes
from . import trade_approval_routes
from . import strategy_routes
from .monitoring_middleware import MonitoringMiddleware
from .monitoring import metrics_collector

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Augment MT5 Local API",
    version="1.0.0",
    description="Local MetaTrader 5 trading workstation API with CSV data storage",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_origin_regex=None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization", "Accept"],
    expose_headers=["Content-Type", "X-Response-Time"],
    max_age=3600,
)

# Mount AI routes
app.include_router(ai_routes.router)

# Mount Settings routes
app.include_router(settings_routes.router)

# Mount Data routes
app.include_router(data_routes.router)

# Mount Monitoring routes
app.include_router(monitoring_routes.router)

# Mount Celery routes
app.include_router(celery_routes.router)

# Mount Decision History routes
app.include_router(decision_history_routes.router)

# Mount Trade Approval routes
app.include_router(trade_approval_routes.router)

# Mount Strategy Management routes
app.include_router(strategy_routes.router)

mt5 = MT5Client()


# --- Security dependency (optional API key) ---


def require_api_key(request: Request):
    if not AUGMENT_API_KEY:
        return

    provided_key = request.headers.get("X-API-Key")
    client_ip = (
        getattr(request.client, "host", "unknown") if request.client else "unknown"
    )

    if provided_key != AUGMENT_API_KEY:
        _log_security_event(
            "invalid_api_key_attempt",
            f"Invalid API key attempt from {client_ip}",
            client_ip,
        )
        raise HTTPException(status_code=401, detail="invalid_api_key")

    # Log successful authentication for high-value operations
    _log_security_event(
        "api_key_authenticated",
        f"Successful API key authentication from {client_ip}",
        client_ip,
    )


# --- Helpers ---


def _canonical_to_broker(canonical: str) -> str:
    for row in symbol_map():
        if row.get("canonical") == canonical:
            if row.get("enabled", "true").lower() != "true":
                raise HTTPException(400, detail="symbol_disabled")
            return row.get("broker_symbol") or canonical
    raise HTTPException(404, detail="symbol_not_found")


def _calculate_daily_pnl() -> float:
    """Calculate today's realized P&L from orders log."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    orders_log = os.path.join(LOG_DIR, "orders.csv")

    if not os.path.exists(orders_log):
        return 0.0

    daily_pnl = 0.0
    rows = read_csv_rows(orders_log)

    for row in rows:
        # Check if order is from today
        ts_utc = row.get("ts_utc", "")
        if ts_utc.startswith(today):
            # For now, we'll track based on successful orders
            # In a real implementation, you'd need position tracking and closing prices
            result_code = row.get("result_code", "0")
            if result_code and int(result_code) >= 10000:
                # This is a placeholder - real P&L calculation would require
                # tracking position opens/closes and current market prices
                # For now, we'll assume small losses per trade for demonstration
                volume = float(row.get("volume", "0") or "0")
                # Simulate small loss per lot (this should be replaced with real P&L calculation)
                daily_pnl -= volume * 10  # Assume 10 currency units loss per lot

    return daily_pnl


def _calculate_symbol_success_rates() -> Dict[str, Dict[str, Union[float, int]]]:
    """Calculate trading success rates for each symbol from orders log."""
    orders_log = os.path.join(LOG_DIR, "orders.csv")

    if not os.path.exists(orders_log):
        return {}

    symbol_stats = {}
    rows = read_csv_rows(orders_log)

    for row in rows:
        canonical = row.get("canonical", "")
        result_code = row.get("result_code", "0")

        if not canonical:
            continue

        if canonical not in symbol_stats:
            symbol_stats[canonical] = {
                "total_trades": 0,
                "successful_trades": 0,
                "win_rate": 0.0,
                "last_trade": "",
            }

        symbol_stats[canonical]["total_trades"] += 1

        # Consider trades with result code >= 10000 as successful
        if result_code and int(result_code) >= 10000:
            symbol_stats[canonical]["successful_trades"] += 1

        # Update last trade timestamp
        ts_utc = row.get("ts_utc", "")
        if ts_utc > symbol_stats[canonical]["last_trade"]:
            symbol_stats[canonical]["last_trade"] = ts_utc

    # Calculate win rates
    for symbol, stats in symbol_stats.items():
        if stats["total_trades"] > 0:
            stats["win_rate"] = stats["successful_trades"] / stats["total_trades"]

    return symbol_stats


def _check_daily_loss_limit() -> None:
    """Check if daily loss limit would be exceeded."""
    limits = risk_limits()
    daily_limit = float(limits.get("daily_loss_limit_r", 0) or 0)

    if daily_limit <= 0:
        return  # No limit set

    current_pnl = _calculate_daily_pnl()

    # If current P&L is already at or below the limit, block trading
    if current_pnl <= -abs(daily_limit):
        raise HTTPException(
            409,
            detail={
                "error": {
                    "code": "DAILY_LOSS_LIMIT_EXCEEDED",
                    "message": f"Daily loss limit of {daily_limit} exceeded. Current P&L: {current_pnl}",
                    "details": {"current_pnl": current_pnl, "limit": daily_limit},
                }
            },
        )


def _validate_and_round_volume(canonical: str, volume: float) -> float:
    """Validate and round volume according to symbol specifications."""
    import math

    # Get symbol configuration
    symbol_config = None
    for row in symbol_map():
        if row.get("canonical") == canonical:
            symbol_config = row
            break

    if not symbol_config:
        raise HTTPException(404, detail="symbol_not_found")

    # Get volume constraints
    min_vol = float(symbol_config.get("min_vol", "0.01") or "0.01")
    vol_step = float(symbol_config.get("vol_step", "0.01") or "0.01")

    # Validate minimum volume
    if volume < min_vol:
        raise HTTPException(
            400,
            detail={
                "error": {
                    "code": "VOLUME_TOO_SMALL",
                    "message": f"Volume {volume} is below minimum {min_vol} for {canonical}",
                    "details": {"volume": volume, "min_volume": min_vol},
                }
            },
        )

    # Round to nearest valid step
    steps = round((volume - min_vol) / vol_step)
    rounded_volume = min_vol + (steps * vol_step)

    # Round to appropriate decimal places to avoid floating point issues
    decimal_places = len(str(vol_step).split(".")[-1]) if "." in str(vol_step) else 0
    rounded_volume = round(rounded_volume, decimal_places)

    return rounded_volume


# --- Routes ---


@app.get("/api/health")
@limiter.limit("100/minute")
def health(request: Request):
    return {"status": "ok", "time_utc": utcnow_iso()}


@app.get("/api/symbols")
@limiter.limit("100/minute")
def get_symbols(request: Request, live: bool = True):
    """
    Get trading symbols.
    - If live=True (default): Get symbols from MT5 Market Watch with real-time data
    - If live=False: Get symbols from configuration file
    """
    try:
        if live:
            # Get symbols directly from MT5 Market Watch
            mt5_symbols = mt5.symbols_get_market_watch()

            if not mt5_symbols:
                # Fallback to configuration if MT5 Market Watch is empty
                _log_error(
                    "symbols",
                    "MT5 Market Watch is empty, falling back to configuration",
                )
                return symbol_map()

            # Transform MT5 symbols to match our API format
            symbols = []
            for symbol in mt5_symbols:
                symbols.append(
                    {
                        "canonical": symbol["name"],
                        "broker_symbol": symbol["name"],
                        "enabled": True,
                        "description": symbol.get("description", symbol["name"]),
                        "currency_base": symbol.get("currency_base", ""),
                        "currency_profit": symbol.get("currency_profit", ""),
                        "currency_margin": symbol.get("currency_margin", ""),
                        "digits": symbol.get("digits", 5),
                        "point": symbol.get("point", 0.00001),
                        "spread": symbol.get("spread", 0),
                        "bid": symbol.get("bid", 0.0),
                        "ask": symbol.get("ask", 0.0),
                        "last": symbol.get("last", 0.0),
                        "volume": symbol.get("volume", 0),
                        "time": symbol.get("time", 0),
                        "trade_mode": symbol.get("trade_mode", 0),
                        "min_lot": symbol.get("volume_min", 0.01),
                        "max_lot": symbol.get("volume_max", 100.0),
                        "lot_step": symbol.get("volume_step", 0.01),
                        "margin_initial": symbol.get("margin_initial", 0.0),
                        "margin_maintenance": symbol.get("margin_maintenance", 0.0),
                    }
                )

            _log_info("symbols", f"Loaded {len(symbols)} symbols from MT5 Market Watch")
            return symbols

        else:
            # Return configuration-based symbols
            return symbol_map()

    except Exception as e:
        _log_error("symbols", f"Failed to get symbols from MT5: {str(e)}")
        # Fallback to configuration
        return symbol_map()


@app.get("/api/symbols/market-watch")
@app.get("/api/market-watch")  # Alias for convenience
@limiter.limit("100/minute")
def get_market_watch_symbols(request: Request):
    """Get symbols currently visible in MT5 Market Watch with real-time prices."""
    try:
        symbols = mt5.symbols_get_market_watch()
        _log_info("market_watch", f"Retrieved {len(symbols)} symbols from Market Watch")
        return symbols
    except Exception as e:
        _log_error("market_watch", f"Failed to get Market Watch symbols: {str(e)}")
        raise HTTPException(
            503, detail={"error": {"code": "MT5_UNAVAILABLE", "message": str(e)}}
        )


@app.get("/api/symbols/{symbol}/tick")
@limiter.limit("200/minute")
def get_symbol_tick(request: Request, symbol: str):
    """Get current tick data for a specific symbol."""
    try:
        tick_data = mt5.symbol_info_tick(symbol)
        if not tick_data:
            raise HTTPException(
                404,
                detail={
                    "error": {
                        "code": "SYMBOL_NOT_FOUND",
                        "message": f"No tick data for symbol {symbol}",
                    }
                },
            )

        return tick_data
    except HTTPException:
        raise
    except Exception as e:
        _log_error("tick_data", f"Failed to get tick data for {symbol}: {str(e)}")
        raise HTTPException(
            503, detail={"error": {"code": "MT5_UNAVAILABLE", "message": str(e)}}
        )


@app.get("/api/symbols/priority")
@limiter.limit("100/minute")
def get_priority_symbols(request: Request, limit: int = 5):
    """Get symbols prioritized by trading success rate."""
    try:
        # Get symbol success rates
        success_rates = _calculate_symbol_success_rates()

        # Get current symbols from MT5 or config
        current_symbols = []
        try:
            mt5_symbols = mt5.symbols_get_market_watch()
            if mt5_symbols:
                current_symbols = [s.name for s in mt5_symbols]
            else:
                current_symbols = [
                    row.get("canonical", "")
                    for row in symbol_map()
                    if row.get("enabled", "true").lower() == "true"
                ]
        except Exception:
            current_symbols = [
                row.get("canonical", "")
                for row in symbol_map()
                if row.get("enabled", "true").lower() == "true"
            ]

        # Filter success rates to only include currently available symbols
        filtered_stats = {
            symbol: stats
            for symbol, stats in success_rates.items()
            if symbol in current_symbols
            and stats["total_trades"] >= 3  # Minimum 3 trades for reliability
        }

        # Sort by win rate (descending) and then by total trades (descending)
        priority_symbols = sorted(
            filtered_stats.items(),
            key=lambda x: (x[1]["win_rate"], x[1]["total_trades"]),
            reverse=True,
        )[:limit]

        # Format response
        result = []
        for symbol, stats in priority_symbols:
            result.append(
                {
                    "symbol": symbol,
                    "win_rate": round(
                        stats["win_rate"] * 100, 1
                    ),  # Convert to percentage
                    "total_trades": stats["total_trades"],
                    "successful_trades": stats["successful_trades"],
                    "last_trade": stats["last_trade"],
                }
            )

        return result

    except Exception as e:
        _log_error("priority_symbols", f"Failed to get priority symbols: {str(e)}")
        return []


@app.get("/api/symbols/{symbol}/info")
@app.get("/api/symbol/{symbol}")  # Alias for convenience
@limiter.limit("100/minute")
def get_symbol_info(request: Request, symbol: str):
    """Get detailed information about a specific symbol."""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise HTTPException(
                404,
                detail={
                    "error": {
                        "code": "SYMBOL_NOT_FOUND",
                        "message": f"Symbol {symbol} not found",
                    }
                },
            )

        return symbol_info
    except HTTPException:
        raise
    except Exception as e:
        _log_error("symbol_info", f"Failed to get symbol info for {symbol}: {str(e)}")
        raise HTTPException(
            503, detail={"error": {"code": "MT5_UNAVAILABLE", "message": str(e)}}
        )


# === HEALTH & STATUS ENDPOINTS ===


@app.get("/health")
@limiter.limit("100/minute")
def health_check(request: Request):
    """Health check endpoint for monitoring."""
    try:
        # Check MT5 connection
        mt5_connected = False
        mt5_error = None
        try:
            account = mt5.account_info()
            mt5_connected = account is not None and account.get("login") is not None
        except Exception as e:
            mt5_error = str(e)

        # Record MT5 status
        metrics_collector.record_mt5_status(mt5_connected)

        # Check if we can access data directories
        data_accessible = os.path.exists(DATA_DIR) and os.path.exists(LOG_DIR)

        # Overall health status
        healthy = mt5_connected and data_accessible

        return {
            "status": "healthy" if healthy else "degraded",
            "timestamp": utcnow_iso(),
            "checks": {
                "mt5_connected": mt5_connected,
                "mt5_error": mt5_error,
                "data_directories": data_accessible,
            },
            "version": "1.1.0",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": utcnow_iso(),
            "error": str(e),
            "version": "1.1.0",
        }


# === ACCOUNT & MARKET DATA ENDPOINTS ===


@app.get("/api/account")
@limiter.limit("60/minute")
def get_account(request: Request):
    # Try MT5; if unavailable, fall back to last CSV snapshot or a default payload
    path = os.path.join(
        DATA_DIR,
        "account",
        datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".csv",
    )
    header = [
        "ts_utc",
        "balance",
        "equity",
        "margin",
        "margin_free",
        "margin_level",
        "leverage",
        "currency",
    ]
    try:
        info = mt5.account_info()
        append_csv(
            path,
            {
                "ts_utc": utcnow_iso(),
                "balance": info.get("balance"),
                "equity": info.get("equity"),
                "margin": info.get("margin"),
                "margin_free": info.get("margin_free"),
                "margin_level": info.get("margin_level"),
                "leverage": info.get("leverage"),
                "currency": info.get("currency"),
            },
            header,
        )
        return info
    except Exception as e:
        _log_error("account", str(e))
        # Try to serve last known snapshot for the day
        rows = read_csv_rows(path)
        if rows:
            last = rows[-1]
            return {
                "balance": float(last.get("balance") or 0),
                "equity": float(last.get("equity") or 0),
                "margin": float(last.get("margin") or 0),
                "margin_free": float(last.get("margin_free") or 0),
                "margin_level": float(last.get("margin_level") or 0),
                "leverage": float(last.get("leverage") or 0),
                "currency": last.get("currency") or "",
            }
        # As a final fallback, return zeros payload (200) so the UI doesn't break
        return {
            "balance": 0,
            "equity": 0,
            "margin": 0,
            "margin_free": 0,
            "margin_level": 0,
            "leverage": 0,
            "currency": "",
        }


@app.get("/api/positions")
@limiter.limit("60/minute")
def get_positions(request: Request):
    try:
        return mt5.positions()
    except Exception as e:
        _log_error("positions", str(e))
        # Fall back to empty list with 200 so UI remains functional
        return []


@app.post("/api/order", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
def post_order(request: Request, req: OrderRequest):
    # Risk: Check daily loss limit first
    _check_daily_loss_limit()

    # Risk: sessions window
    sess = sessions_map().get(req.canonical)
    if sess:
        start, end, block_flag = sess
        now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")
        if not (start <= now_utc <= end) and block_flag.lower() == "true":
            return _error(409, "RISK_BLOCK", f"Outside session window {start}-{end}")

    # Map symbol and validate volume
    broker_symbol = _canonical_to_broker(req.canonical)
    validated_volume = _validate_and_round_volume(req.canonical, req.volume)

    # Send order with validated volume
    try:
        result = mt5.order_send(
            symbol=broker_symbol,
            side=req.side,
            volume=validated_volume,
            sl=req.sl,
            tp=req.tp,
            deviation=req.deviation,
            comment=req.comment,
            magic=req.magic,
        )
    except Exception as e:
        _log_error("order_send", str(e))
        return _error(
            503,
            "MT5_UNAVAILABLE",
            "MetaTrader5 module not available or terminal not connected",
        )

    # Log order attempt
    orders_log = os.path.join(LOG_DIR, "orders.csv")
    append_csv(
        orders_log,
        {
            "ts_utc": utcnow_iso(),
            "action": f"market_{req.side}",
            "canonical": req.canonical,
            "broker_symbol": broker_symbol,
            "req_json": json.dumps(req.model_dump()),
            "result_code": result.get("retcode"),
            "order": result.get("order"),
            "position": result.get("position"),
            "price": None,
            "volume": validated_volume,
            "sl": req.sl or "",
            "tp": req.tp or "",
            "comment": result.get("comment", ""),
        },
        [
            "ts_utc",
            "action",
            "canonical",
            "broker_symbol",
            "req_json",
            "result_code",
            "order",
            "position",
            "price",
            "volume",
            "sl",
            "tp",
            "comment",
        ],
    )

    if int(result.get("retcode", 0)) > 10000:
        # Record successful order
        metrics_collector.record_order(success=True)
        metrics_collector.record_position_opened()
        return {
            "order": result.get("order"),
            "position": result.get("position"),
            "result_code": result.get("retcode"),
        }
    else:
        # Record failed order
        metrics_collector.record_order(success=False)
        return _error(
            409,
            "BROKER_REJECT",
            f"MT5 retcode {result.get('retcode')}",
            details={"last_error": result.get("last_error")},
        )


@app.get("/api/ticks")
@limiter.limit("30/minute")
def get_ticks(request: Request, canonical: str, limit: int = 200):
    # Validate canonical symbol to prevent path traversal
    if not canonical.replace("_", "").replace("-", "").isalnum() or len(canonical) > 20:
        raise HTTPException(400, detail="invalid_symbol_format")

    # Read today's ticks CSV: data/ticks/{SYMBOL}/{YYYY-MM-DD}.csv
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(DATA_DIR, "ticks", canonical, f"{today}.csv")
    rows = read_csv_rows(path)
    return rows[-limit:]


@app.get("/api/bars")
@limiter.limit("30/minute")
def get_bars(
    request: Request,
    canonical: str,
    tf: str = "M1",
    from_: Union[str, None] = None,
    to: Union[str, None] = None,
):
    # Validate inputs to prevent path traversal
    if not canonical.replace("_", "").replace("-", "").isalnum() or len(canonical) > 20:
        raise HTTPException(400, detail="invalid_symbol_format")
    if tf not in ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]:
        raise HTTPException(400, detail="invalid_timeframe")

    # Read monthly bars CSV: data/bars/{TF}/{SYMBOL}/{YYYY-MM}.csv
    # For simplicity, this loads the current month only if range unspecified
    now = datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")
    path = os.path.join(DATA_DIR, "bars", tf, canonical, f"{month}.csv")
    rows = read_csv_rows(path)
    # Basic filter on ts_utc if provided
    if from_ or to:

        def in_range(ts: str) -> bool:
            if from_ and ts < from_:
                return False
            if to and ts > to:
                return False
            return True

        rows = [r for r in rows if in_range(r.get("ts_utc", ""))]
    return rows


@app.get("/events")
@limiter.limit("5/minute")
async def events(request: Request):
    async def gen():
        while True:
            if await request.is_disconnected():
                break
            payload = json.dumps({"t": utcnow_iso(), "kind": "heartbeat"})
            yield {"event": "heartbeat", "data": payload}
            await asyncio.sleep(5)

    return EventSourceResponse(gen())


# === PHASE 1 ENDPOINTS: PENDING ORDERS ===


@app.get("/api/orders")
@limiter.limit("60/minute")
def get_pending_orders(request: Request, symbol: str = None, ticket: int = None):
    """Get active pending orders with optional filtering."""
    try:
        orders = mt5.orders_get(symbol=symbol, ticket=ticket)

        # Log pending orders for audit trail
        if orders:
            path = os.path.join(LOG_DIR, "pending_orders.csv")
            header = [
                "ts_utc",
                "ticket",
                "symbol",
                "type",
                "volume",
                "price_open",
                "sl",
                "tp",
                "price_current",
                "comment",
                "magic",
            ]

            for order in orders:
                append_csv(
                    path,
                    {
                        "ts_utc": utcnow_iso(),
                        "ticket": order.get("ticket"),
                        "symbol": order.get("symbol"),
                        "type": order.get("type"),
                        "volume": order.get("volume"),
                        "price_open": order.get("price_open"),
                        "sl": order.get("sl"),
                        "tp": order.get("tp"),
                        "price_current": order.get("price_current"),
                        "comment": order.get("comment"),
                        "magic": order.get("magic"),
                    },
                    header,
                )

        return orders
    except Exception as e:
        _log_error("pending_orders", str(e))
        return []


@app.post("/api/orders/pending", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
def create_pending_order(request: Request, req: PendingOrderRequest):
    """Create a new pending order."""
    # Risk checks (reuse existing logic)
    _check_daily_loss_limit()

    # Session window check
    sess = sessions_map().get(req.canonical)
    if sess:
        start, end, block_flag = sess
        now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S")
        if not (start <= now_utc <= end) and block_flag.lower() == "true":
            return _error(409, "RISK_BLOCK", f"Outside session window {start}-{end}")

    # Map symbol and validate volume
    broker_symbol = _canonical_to_broker(req.canonical)
    validated_volume = _validate_and_round_volume(req.canonical, req.volume)

    # Send pending order
    try:
        result = mt5.order_send_pending(
            symbol=broker_symbol,
            order_type=req.order_type,
            volume=validated_volume,
            price=req.price,
            sl=req.sl,
            tp=req.tp,
            deviation=req.deviation,
            comment=req.comment,
            magic=req.magic,
        )
    except Exception as e:
        _log_error("pending_order_send", str(e))
        return _error(
            503,
            "MT5_UNAVAILABLE",
            "MetaTrader5 module not available or terminal not connected",
        )

    # Log pending order attempt
    orders_log = os.path.join(LOG_DIR, "orders.csv")
    append_csv(
        orders_log,
        {
            "ts_utc": utcnow_iso(),
            "action": f"pending_{req.order_type}",
            "canonical": req.canonical,
            "broker_symbol": broker_symbol,
            "req_json": json.dumps(req.model_dump()),
            "result_code": result.get("retcode"),
            "order": result.get("order"),
            "position": 0,  # Pending orders don't have positions
            "price": req.price,
            "volume": validated_volume,
            "sl": req.sl or "",
            "tp": req.tp or "",
            "comment": result.get("comment", ""),
        },
        [
            "ts_utc",
            "action",
            "canonical",
            "broker_symbol",
            "req_json",
            "result_code",
            "order",
            "position",
            "price",
            "volume",
            "sl",
            "tp",
            "comment",
        ],
    )

    if int(result.get("retcode", 0)) >= 10000:
        return {
            "order": result.get("order"),
            "result_code": result.get("retcode"),
            "comment": result.get("comment"),
        }
    else:
        return _error(
            409,
            "BROKER_REJECT",
            f"MT5 retcode {result.get('retcode')}",
            details={"last_error": result.get("last_error")},
        )


@app.delete("/api/orders/{order_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("20/minute")
def cancel_pending_order(request: Request, order_id: int):
    """Cancel a pending order by ticket number."""
    try:
        result = mt5.order_cancel(ticket=order_id)

        # Log cancellation attempt
        orders_log = os.path.join(LOG_DIR, "orders.csv")
        append_csv(
            orders_log,
            {
                "ts_utc": utcnow_iso(),
                "action": "cancel_pending",
                "canonical": "",
                "broker_symbol": "",
                "req_json": json.dumps({"ticket": order_id}),
                "result_code": result.get("retcode"),
                "order": result.get("order"),
                "position": 0,
                "price": "",
                "volume": "",
                "sl": "",
                "tp": "",
                "comment": result.get("comment", ""),
            },
            [
                "ts_utc",
                "action",
                "canonical",
                "broker_symbol",
                "req_json",
                "result_code",
                "order",
                "position",
                "price",
                "volume",
                "sl",
                "tp",
                "comment",
            ],
        )

        if int(result.get("retcode", 0)) >= 10000:
            return {
                "order": result.get("order"),
                "result_code": result.get("retcode"),
                "comment": result.get("comment"),
            }
        else:
            return _error(
                409,
                "BROKER_REJECT",
                f"MT5 retcode {result.get('retcode')}",
                details={"last_error": result.get("last_error")},
            )
    except Exception as e:
        _log_error("cancel_pending_order", str(e))
        return _error(
            503,
            "MT5_UNAVAILABLE",
            "MetaTrader5 module not available or terminal not connected",
        )


@app.patch("/api/orders/{order_id}", dependencies=[Depends(require_api_key)])
@limiter.limit("20/minute")
def modify_pending_order(request: Request, order_id: int, body: dict):
    """Modify an existing pending order. Accepts price and/or sl/tp."""
    try:
        price = body.get("price") if isinstance(body, dict) else None
        sl = body.get("sl") if isinstance(body, dict) else None
        tp = body.get("tp") if isinstance(body, dict) else None
        expiration = body.get("expiration") if isinstance(body, dict) else None
        result = mt5.order_modify(
            order_id, price=price, sl=sl, tp=tp, expiration=expiration
        )
        if int(result.get("retcode", 0)) >= 10000:
            return {
                "order": result.get("order"),
                "result_code": result.get("retcode"),
                "comment": result.get("comment"),
            }
        else:
            return _error(
                409,
                "BROKER_REJECT",
                f"MT5 retcode {result.get('retcode')}",
                details={"last_error": result.get("last_error")},
            )
    except Exception as e:
        _log_error("modify_pending_order", str(e))
        return _error(
            503,
            "MT5_UNAVAILABLE",
            "MetaTrader5 module not available or terminal not connected",
        )


@app.post("/api/positions/{ticket}/close", dependencies=[Depends(require_api_key)])
@limiter.limit("20/minute")
def close_position(request: Request, ticket: int):
    """Close an open position by ticket."""
    try:
        result = mt5.position_close(ticket)
        if int(result.get("retcode", 0)) >= 10000:
            # Record position closed
            metrics_collector.record_position_closed()
            return {
                "order": result.get("order"),
                "result_code": result.get("retcode"),
                "comment": result.get("comment"),
            }
        else:
            return _error(
                409,
                "BROKER_REJECT",
                f"MT5 retcode {result.get('retcode')}",
                details={"last_error": result.get("last_error")},
            )
    except Exception as e:
        _log_error("close_position", str(e))
        return _error(
            503,
            "MT5_UNAVAILABLE",
            "MetaTrader5 module not available or terminal not connected",
        )


# === PHASE 1 ENDPOINTS: HISTORICAL DATA ===


@app.get("/api/history/bars")
@limiter.limit("30/minute")
def get_historical_bars(
    request: Request,
    symbol: str,
    timeframe: str = "M1",
    date_from: str = None,
    date_to: str = None,
    count: int = 1000,
):
    """Get historical price bars for a symbol."""
    # Validate timeframe
    try:
        import MetaTrader5 as mt5_module

        valid_timeframes = {
            "M1": mt5_module.TIMEFRAME_M1,
            "M5": mt5_module.TIMEFRAME_M5,
            "M15": mt5_module.TIMEFRAME_M15,
            "M30": mt5_module.TIMEFRAME_M30,
            "H1": mt5_module.TIMEFRAME_H1,
            "H4": mt5_module.TIMEFRAME_H4,
            "D1": mt5_module.TIMEFRAME_D1,
        }
    except ImportError:
        # Fallback for testing
        valid_timeframes = {
            "M1": 1,
            "M5": 5,
            "M15": 15,
            "M30": 30,
            "H1": 16385,
            "H4": 16388,
            "D1": 16408,
        }

    if timeframe not in valid_timeframes:
        raise HTTPException(400, detail="invalid_timeframe")

    try:
        from datetime import datetime

        if date_from and date_to:
            # Parse dates
            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

            # Get historical data for date range
            rates = mt5.copy_rates_range(
                symbol, valid_timeframes[timeframe], dt_from, dt_to
            )
        else:
            # Get most recent bars
            rates = mt5.copy_rates_from_pos(
                symbol, valid_timeframes[timeframe], 0, count
            )

        if rates is None:
            return []

        # Convert to list of dictionaries for JSON serialization
        bars_data = []
        for rate in rates:
            bars_data.append(
                {
                    "time": int(rate[0]),  # timestamp
                    "open": float(rate[1]),
                    "high": float(rate[2]),
                    "low": float(rate[3]),
                    "close": float(rate[4]),
                    "tick_volume": int(rate[5]),
                    "spread": int(rate[6]),
                    "real_volume": int(rate[7]) if len(rate) > 7 else 0,
                }
            )

        # Cache historical data to CSV
        if bars_data:
            today = datetime.now(timezone.utc).strftime("%Y-%m")
            path = os.path.join(
                DATA_DIR, "history", "bars", timeframe, symbol, f"{today}.csv"
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)

            header = [
                "ts_utc",
                "time",
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                "spread",
                "real_volume",
            ]
            for bar in bars_data[-100:]:  # Cache last 100 bars to avoid huge files
                append_csv(
                    path,
                    {
                        "ts_utc": utcnow_iso(),
                        "time": bar["time"],
                        "open": bar["open"],
                        "high": bar["high"],
                        "low": bar["low"],
                        "close": bar["close"],
                        "tick_volume": bar["tick_volume"],
                        "spread": bar["spread"],
                        "real_volume": bar["real_volume"],
                    },
                    header,
                )

        return bars_data

    except Exception as e:
        _log_error(
            "historical_bars", f"Failed to get historical bars for {symbol}: {str(e)}"
        )
        return []


@app.get("/api/history/ticks")
@limiter.limit("20/minute")
def get_historical_ticks(
    request: Request,
    symbol: str,
    date_from: str,
    date_to: str,
    flags: str = "ALL",
    count: int = 10000,
):
    """Get historical tick data for a symbol.

    Valid flags:
    - ALL: All ticks (default)
    - INFO: Ticks with price changes
    - TRADE: Trade ticks only

    Note: MetaTrader5 v5.0.45 only supports these three flag types.
    Legacy flags (BID, ASK, LAST, VOLUME) are not available in this version.
    """
    # Map flags to MT5 constants (only valid constants for MT5 v5.0.45)
    try:
        import MetaTrader5 as mt5_module

        flag_map = {
            "ALL": mt5_module.COPY_TICKS_ALL,  # -1: All ticks
            "INFO": mt5_module.COPY_TICKS_INFO,  # 1: Ticks with price changes
            "TRADE": mt5_module.COPY_TICKS_TRADE,  # 2: Trade ticks only
        }
    except ImportError:
        # Fallback for testing (when MT5 module not available)
        flag_map = {
            "ALL": -1,
            "INFO": 1,
            "TRADE": 2,
        }

    if flags not in flag_map:
        raise HTTPException(
            400,
            detail=f"invalid_flags: '{flags}' not supported. Valid flags: {', '.join(flag_map.keys())}",
        )

    try:
        # Parse dates
        from datetime import datetime

        dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        # Get historical tick data
        ticks = mt5.copy_ticks_range(symbol, dt_from, dt_to, flag_map[flags])

        if not ticks:
            return []

        # Convert to list of dictionaries and limit count
        ticks_data = []
        for tick in ticks[:count]:
            tick_dict = tick._asdict()
            ticks_data.append(
                {
                    "time": int(tick_dict["time"]),
                    "bid": float(tick_dict["bid"]),
                    "ask": float(tick_dict["ask"]),
                    "last": float(tick_dict["last"]),
                    "volume": int(tick_dict["volume"]),
                    "time_msc": int(tick_dict["time_msc"]),
                    "flags": int(tick_dict["flags"]),
                    "volume_real": float(tick_dict["volume_real"]),
                }
            )

        # Cache tick data to CSV
        if ticks_data:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            path = os.path.join(DATA_DIR, "history", "ticks", symbol, f"{today}.csv")
            os.makedirs(os.path.dirname(path), exist_ok=True)

            header = [
                "ts_utc",
                "time",
                "bid",
                "ask",
                "last",
                "volume",
                "time_msc",
                "flags",
                "volume_real",
            ]
            for tick in ticks_data[-1000:]:  # Cache last 1000 ticks
                append_csv(
                    path,
                    {
                        "ts_utc": utcnow_iso(),
                        "time": tick["time"],
                        "bid": tick["bid"],
                        "ask": tick["ask"],
                        "last": tick["last"],
                        "volume": tick["volume"],
                        "time_msc": tick["time_msc"],
                        "flags": tick["flags"],
                        "volume_real": tick["volume_real"],
                    },
                    header,
                )

        return ticks_data

    except Exception as e:
        _log_error(
            "historical_ticks", f"Failed to get historical ticks for {symbol}: {str(e)}"
        )
        return []


# === PHASE 1 ENDPOINTS: TRADING HISTORY ===


@app.get("/api/history/deals")
@limiter.limit("30/minute")
def get_trading_deals(
    request: Request, date_from: str = None, date_to: str = None, symbol: str = None
):
    """Get trading deals history with P&L calculations."""
    try:
        # Parse dates with defaults (last 30 days if not provided)
        from datetime import datetime, timedelta

        if not date_to:
            dt_to = datetime.now()
            date_to = dt_to.isoformat()
        else:
            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        if not date_from:
            dt_from = dt_to - timedelta(days=30)
            date_from = dt_from.isoformat()
        else:
            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))

        # Get deals from MT5
        deals = mt5.history_deals_get(dt_from, dt_to, symbol=symbol)

        if not deals:
            # Return consistent format even when no deals found
            return {
                "deals": [],
                "summary": {
                    "total_deals": 0,
                    "total_profit": 0.0,
                    "total_commission": 0.0,
                    "total_swap": 0.0,
                    "net_profit": 0.0,
                    "date_from": date_from,
                    "date_to": date_to,
                    "symbol_filter": symbol,
                },
            }

        # Convert to list and calculate statistics
        deals_data = []
        total_profit = 0.0
        total_commission = 0.0
        total_swap = 0.0

        for deal in deals:
            deal_dict = deal._asdict()
            profit = float(deal_dict.get("profit", 0))
            commission = float(deal_dict.get("commission", 0))
            swap = float(deal_dict.get("swap", 0))

            total_profit += profit
            total_commission += commission
            total_swap += swap

            deals_data.append(
                {
                    "ticket": int(deal_dict["ticket"]),
                    "order": int(deal_dict["order"]),
                    "time": int(deal_dict["time"]),
                    "time_msc": int(deal_dict["time_msc"]),
                    "type": int(deal_dict["type"]),
                    "entry": int(deal_dict["entry"]),
                    "magic": int(deal_dict["magic"]),
                    "position_id": int(deal_dict["position_id"]),
                    "reason": int(deal_dict["reason"]),
                    "volume": float(deal_dict["volume"]),
                    "price": float(deal_dict["price"]),
                    "commission": commission,
                    "swap": swap,
                    "profit": profit,
                    "symbol": deal_dict["symbol"],
                    "comment": deal_dict["comment"],
                    "external_id": deal_dict["external_id"],
                }
            )

        # Log deals to CSV
        if deals_data:
            path = os.path.join(LOG_DIR, "deals.csv")
            header = [
                "ts_utc",
                "ticket",
                "order",
                "time",
                "type",
                "entry",
                "magic",
                "position_id",
                "volume",
                "price",
                "commission",
                "swap",
                "profit",
                "symbol",
                "comment",
            ]

            for deal in deals_data[-100:]:  # Log last 100 deals
                append_csv(
                    path,
                    {
                        "ts_utc": utcnow_iso(),
                        "ticket": deal["ticket"],
                        "order": deal["order"],
                        "time": deal["time"],
                        "type": deal["type"],
                        "entry": deal["entry"],
                        "magic": deal["magic"],
                        "position_id": deal["position_id"],
                        "volume": deal["volume"],
                        "price": deal["price"],
                        "commission": deal["commission"],
                        "swap": deal["swap"],
                        "profit": deal["profit"],
                        "symbol": deal["symbol"],
                        "comment": deal["comment"],
                    },
                    header,
                )

        # Return deals with summary statistics
        return {
            "deals": deals_data,
            "summary": {
                "total_deals": len(deals_data),
                "total_profit": round(total_profit, 2),
                "total_commission": round(total_commission, 2),
                "total_swap": round(total_swap, 2),
                "net_profit": round(total_profit + total_commission + total_swap, 2),
                "date_from": date_from,
                "date_to": date_to,
                "symbol_filter": symbol,
            },
        }

    except Exception as e:
        _log_error("trading_deals", f"Failed to get trading deals: {str(e)}")
        return {"deals": [], "summary": {}}


@app.get("/api/history/orders")
@limiter.limit("30/minute")
def get_trading_orders(
    request: Request, date_from: str = None, date_to: str = None, symbol: str = None
):
    """Get trading orders history."""
    try:
        # Parse dates with defaults (last 30 days if not provided)
        from datetime import datetime, timedelta

        if not date_to:
            dt_to = datetime.now()
            date_to = dt_to.isoformat()
        else:
            dt_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        if not date_from:
            dt_from = dt_to - timedelta(days=30)
            date_from = dt_from.isoformat()
        else:
            dt_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))

        # Get orders from MT5
        orders = mt5.history_orders_get(dt_from, dt_to, symbol=symbol)

        if not orders:
            # Return consistent format even when no orders found
            return {
                "orders": [],
                "summary": {
                    "total_orders": 0,
                    "order_types": {},
                    "date_from": date_from,
                    "date_to": date_to,
                    "symbol_filter": symbol,
                },
            }

        # Convert to list and categorize
        orders_data = []
        order_types = {}

        for order in orders:
            order_dict = order._asdict()
            order_type = order_dict.get("type", 0)

            # Count order types
            order_types[order_type] = order_types.get(order_type, 0) + 1

            orders_data.append(
                {
                    "ticket": int(order_dict["ticket"]),
                    "time_setup": int(order_dict["time_setup"]),
                    "time_setup_msc": int(order_dict["time_setup_msc"]),
                    "time_done": int(order_dict["time_done"]),
                    "time_done_msc": int(order_dict["time_done_msc"]),
                    "time_expiration": int(order_dict["time_expiration"]),
                    "type": order_type,
                    "type_filling": int(order_dict["type_filling"]),
                    "type_time": int(order_dict["type_time"]),
                    "state": int(order_dict["state"]),
                    "magic": int(order_dict["magic"]),
                    "position_id": int(order_dict["position_id"]),
                    "position_by_id": int(order_dict["position_by_id"]),
                    "reason": int(order_dict["reason"]),
                    "volume_initial": float(order_dict["volume_initial"]),
                    "volume_current": float(order_dict["volume_current"]),
                    "price_open": float(order_dict["price_open"]),
                    "sl": float(order_dict["sl"]),
                    "tp": float(order_dict["tp"]),
                    "price_current": float(order_dict["price_current"]),
                    "price_stoplimit": float(order_dict["price_stoplimit"]),
                    "symbol": order_dict["symbol"],
                    "comment": order_dict["comment"],
                    "external_id": order_dict["external_id"],
                }
            )

        # Return orders with summary
        return {
            "orders": orders_data,
            "summary": {
                "total_orders": len(orders_data),
                "order_types": order_types,
                "date_from": date_from,
                "date_to": date_to,
                "symbol_filter": symbol,
            },
        }

    except Exception as e:
        _log_error("trading_orders", f"Failed to get trading orders: {str(e)}")
        return {"orders": [], "summary": {}}


# --- Error helpers ---


def _error(status: int, code: str, msg: str, *, details: Union[Dict, None] = None):
    body = {"error": {"code": code, "message": msg, "details": details or {}}}
    _log_error(code.lower(), msg)
    raise HTTPException(status_code=status, detail=body)


def _sanitize_message(message: str) -> str:
    """Sanitize error messages to remove sensitive information."""
    import re

    # Remove potential API keys, passwords, and other sensitive patterns
    patterns = [
        (r'[Aa]pi[_-]?[Kk]ey["\s]*[:=]["\s]*[A-Za-z0-9]{8,}', "API_KEY=***"),
        (r'[Pp]assword["\s]*[:=]["\s]*[^\s"]+', "password=***"),
        (r'[Tt]oken["\s]*[:=]["\s]*[A-Za-z0-9]{8,}', "token=***"),
        (r'[Aa]uthorization["\s]*[:=]["\s]*[^\s"]+', "Authorization=***"),
        (r'X-API-Key["\s]*[:=]["\s]*[A-Za-z0-9]{8,}', "X-API-Key=***"),
    ]

    sanitized = message
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    # Truncate very long messages to prevent log bloat
    if len(sanitized) > 500:
        sanitized = sanitized[:497] + "..."

    return sanitized


def _log_error(scope: str, message: str, details: str = ""):
    """Log errors with sanitization to prevent sensitive data exposure."""
    path = os.path.join(LOG_DIR, "errors.csv")
    sanitized_message = _sanitize_message(message)
    sanitized_details = _sanitize_message(details) if details else ""

    append_csv(
        path,
        {
            "ts_utc": utcnow_iso(),
            "scope": scope,
            "message": sanitized_message,
            "last_error": "",
            "details": sanitized_details,
        },
        ["ts_utc", "scope", "message", "last_error", "details"],
    )


def _log_info(category: str, message: str) -> None:
    """Log informational messages."""
    try:
        sanitized_message = _sanitize_message(message)
        print(f"[INFO] {category}: {sanitized_message}")
    except Exception as e:
        print(f"Failed to log info: {e}")


def _log_security_event(event_type: str, details: str, client_ip: str = "unknown"):
    """Log security-related events for monitoring."""
    path = os.path.join(LOG_DIR, "security.csv")
    append_csv(
        path,
        {
            "ts_utc": utcnow_iso(),
            "event_type": event_type,
            "client_ip": client_ip,
            "details": _sanitize_message(details),
        },
        ["ts_utc", "event_type", "client_ip", "details"],
    )
