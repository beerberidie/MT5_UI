from typing import Optional, Union

try:
    import MetaTrader5 as mt5
except Exception:  # pragma: no cover - allow running without MT5 installed
    mt5 = None  # type: ignore

from .config import MT5_PATH


class MT5Client:
    def __init__(self) -> None:
        self.initialized = False

    def init(self) -> None:
        if self.initialized:
            return
        if mt5 is None:
            raise RuntimeError("MetaTrader5 module not available")
        if not mt5.initialize(path=MT5_PATH):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        self.initialized = True

    def shutdown(self) -> None:
        if self.initialized and mt5 is not None:
            mt5.shutdown()
            self.initialized = False

    def account_info(self):
        self.init()
        return mt5.account_info()._asdict()

    def positions(self):
        self.init()
        res = mt5.positions_get()
        return [p._asdict() for p in res] if res else []

    def symbols_get(self, group: str = "*") -> list:
        """Get all available symbols from MT5 terminal."""
        self.init()
        symbols = mt5.symbols_get(group)
        return [s._asdict() for s in symbols] if symbols else []

    def symbols_get_market_watch(self) -> list:
        """Get symbols currently visible in MT5 Market Watch window."""
        self.init()
        # Get all symbols and filter for those visible in Market Watch
        all_symbols = mt5.symbols_get()
        if not all_symbols:
            return []

        market_watch_symbols = []
        for symbol in all_symbols:
            symbol_dict = symbol._asdict()
            # Check if symbol is visible in Market Watch
            if symbol_dict.get("visible", False):
                # Get current tick data for the symbol
                tick = mt5.symbol_info_tick(symbol.name)
                if tick:
                    tick_dict = tick._asdict()
                    symbol_dict.update(
                        {
                            "bid": tick_dict.get("bid", 0.0),
                            "ask": tick_dict.get("ask", 0.0),
                            "last": tick_dict.get("last", 0.0),
                            "spread": tick_dict.get("ask", 0.0)
                            - tick_dict.get("bid", 0.0),
                            "time": tick_dict.get("time", 0),
                            "volume": tick_dict.get("volume", 0),
                        }
                    )
                market_watch_symbols.append(symbol_dict)

        return market_watch_symbols

    def symbol_info(self, symbol: str) -> dict:
        """Get detailed information about a specific symbol."""
        self.init()
        info = mt5.symbol_info(symbol)
        if info is None:
            return {}
        return info._asdict()

    def symbol_info_tick(self, symbol: str) -> dict:
        """Get current tick data for a symbol."""
        self.init()
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {}
        return tick._asdict()

    def copy_rates_from_pos(
        self, symbol: str, timeframe, start_pos: int, count: int
    ) -> list:
        """Get historical rates data."""
        self.init()
        rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        return rates.tolist() if rates is not None else []

    def copy_ticks_from(self, symbol: str, date_from, count: int, flags=None) -> list:
        """Get tick data from specified date."""
        self.init()
        if flags is None:
            flags = mt5.COPY_TICKS_ALL
        ticks = mt5.copy_ticks_from(symbol, date_from, count, flags)
        return [tick._asdict() for tick in ticks] if ticks is not None else []

    def order_send(
        self,
        *,
        symbol: str,
        side: str,
        volume: float,
        sl: Union[float, None],
        tp: Union[float, None],
        deviation: int,
        comment: str,
        magic: int,
    ) -> dict:
        self.init()
        order_type = mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            # Try to enable/select the symbol and retry
            mt5.symbol_select(symbol, True)
            tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(
                f"No tick data for symbol '{symbol}'. Ensure the symbol is visible/selected in MT5 and that market data is available."
            )
        price = tick.ask if side == "buy" else tick.bid
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "magic": magic,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl or 0.0,
            "tp": tp or 0.0,
            "deviation": deviation,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": comment,
        }
        result = mt5.order_send(request)
        return {
            "retcode": result.retcode,
            "order": getattr(result, "order", 0),
            "position": getattr(result, "position", 0),
            "request": request,
            "comment": getattr(result, "comment", ""),
            "last_error": mt5.last_error(),
        }

    # === PHASE 1 ENHANCEMENTS: PENDING ORDERS ===

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

    def order_send_pending(
        self,
        *,
        symbol: str,
        order_type: str,
        volume: float,
        price: float,
        sl: Union[float, None],
        tp: Union[float, None],
        deviation: int,
        comment: str,
        magic: int,
    ) -> dict:
        """Send a pending order (Buy Stop, Sell Stop, Buy Limit, Sell Limit)."""
        self.init()

        # Map order type strings to MT5 constants
        order_type_map = {
            "buy_stop": mt5.ORDER_TYPE_BUY_STOP,
            "sell_stop": mt5.ORDER_TYPE_SELL_STOP,
            "buy_limit": mt5.ORDER_TYPE_BUY_LIMIT,
            "sell_limit": mt5.ORDER_TYPE_SELL_LIMIT,
        }

        if order_type not in order_type_map:
            raise ValueError(
                f"Invalid order type: {order_type}. Must be one of: {list(order_type_map.keys())}"
            )

        # Ensure symbol is selected
        mt5.symbol_select(symbol, True)

        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "magic": magic,
            "symbol": symbol,
            "volume": volume,
            "type": order_type_map[order_type],
            "price": price,
            "sl": sl or 0.0,
            "tp": tp or 0.0,
            "deviation": deviation,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": comment,
        }

        result = mt5.order_send(request)
        return {
            "retcode": result.retcode,
            "order": getattr(result, "order", 0),
            "request": request,
            "comment": getattr(result, "comment", ""),
            "last_error": mt5.last_error(),
        }

    def order_cancel(self, ticket: int) -> dict:
        """Cancel a pending order by ticket number."""
        self.init()

        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket,
        }

        result = mt5.order_send(request)
        return {
            "retcode": result.retcode,
            "order": getattr(result, "order", 0),
            "request": request,
            "comment": getattr(result, "comment", ""),
            "last_error": mt5.last_error(),
        }

    def position_close(self, ticket: int) -> dict:
        """Close an open position by ticket using a market deal in the opposite direction."""
        self.init()
        pos_list = mt5.positions_get(ticket=ticket)
        if not pos_list:
            return {
                "retcode": -1,
                "order": 0,
                "comment": f"Position {ticket} not found",
                "last_error": mt5.last_error(),
            }
        pos = pos_list[0]._asdict()
        symbol = pos.get("symbol")
        volume = float(pos.get("volume") or 0)
        ptype = int(pos.get("type") or 0)  # 0 buy, 1 sell
        # Determine opposite order type and price
        mt5.symbol_select(symbol, True)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {
                "retcode": -2,
                "order": 0,
                "comment": f"No tick data for {symbol}",
                "last_error": mt5.last_error(),
            }
        if ptype == mt5.POSITION_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = float(tick.bid)
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = float(tick.ask)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 10,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": "CLOSE_POSITION",
        }
        result = mt5.order_send(request)
        return {
            "retcode": result.retcode,
            "order": getattr(result, "order", 0),
            "request": request,
            "comment": getattr(result, "comment", ""),
            "last_error": mt5.last_error(),
        }

    def order_modify(
        self,
        ticket: int,
        *,
        price: float | None = None,
        sl: float | None = None,
        tp: float | None = None,
        expiration: int | None = None,
    ) -> dict:
        """Modify an existing pending order's price and/or SL/TP."""
        self.init()
        req = {
            "action": mt5.TRADE_ACTION_MODIFY,
            "order": ticket,
            "type_time": mt5.ORDER_TIME_GTC,
            "expiration": int(expiration or 0),
        }
        if price is not None:
            req["price"] = float(price)
        # Use 0.0 if not provided (MT5 expects numbers)
        if sl is not None:
            req["sl"] = float(sl)
        if tp is not None:
            req["tp"] = float(tp)
        result = mt5.order_send(req)
        return {
            "retcode": result.retcode,
            "order": getattr(result, "order", 0),
            "request": req,
            "comment": getattr(result, "comment", ""),
            "last_error": mt5.last_error(),
        }

    # === PHASE 1 ENHANCEMENTS: HISTORICAL DATA ===

    def copy_rates_range(self, symbol: str, timeframe, date_from, date_to) -> list:
        """Get historical rates data for a specific date range."""
        self.init()
        rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if rates is None:
            return []
        # Handle both numpy arrays and lists
        return rates.tolist() if hasattr(rates, "tolist") else list(rates)

    def copy_ticks_range(self, symbol: str, date_from, date_to, flags=None) -> list:
        """Get tick data for a specific date range."""
        self.init()
        if flags is None:
            flags = mt5.COPY_TICKS_ALL
        ticks = mt5.copy_ticks_range(symbol, date_from, date_to, flags)
        return [tick._asdict() for tick in ticks] if ticks is not None else []

    # === PHASE 1 ENHANCEMENTS: TRADING HISTORY ===

    def history_deals_get(self, date_from, date_to, symbol: str = None) -> list:
        """Get deals from trading history within specified date range."""
        self.init()
        if symbol:
            deals = mt5.history_deals_get(date_from, date_to, symbol=symbol)
        else:
            deals = mt5.history_deals_get(date_from, date_to)

        return [deal._asdict() for deal in deals] if deals else []

    def history_deals_total(self, date_from, date_to) -> int:
        """Get total number of deals in trading history within specified date range."""
        self.init()
        return mt5.history_deals_total(date_from, date_to)

    def history_orders_get(self, date_from, date_to, symbol: str = None) -> list:
        """Get orders from trading history within specified date range."""
        self.init()
        if symbol:
            orders = mt5.history_orders_get(date_from, date_to, symbol=symbol)
        else:
            orders = mt5.history_orders_get(date_from, date_to)

        return [order._asdict() for order in orders] if orders else []

    def history_orders_total(self, date_from, date_to) -> int:
        """Get total number of orders in trading history within specified date range."""
        self.init()
        return mt5.history_orders_total(date_from, date_to)
