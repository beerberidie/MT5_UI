"""
Tests for Phase 1 MT5Client enhancements.
Tests pending orders, historical data, and trading history functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.mt5_client import MT5Client


class TestMT5ClientPhase1:
    """Test Phase 1 enhancements to MT5Client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = MT5Client()

    @patch("backend.mt5_client.mt5")
    def test_orders_get_all(self, mock_mt5):
        """Test getting all pending orders."""
        # Mock MT5 orders
        mock_order = Mock()
        mock_order._asdict.return_value = {
            "ticket": 12345,
            "symbol": "EURUSD",
            "type": 2,  # Buy Limit
            "volume": 0.1,
            "price_open": 1.1000,
            "sl": 1.0950,
            "tp": 1.1100,
            "comment": "Test order",
        }

        mock_mt5.orders_get.return_value = [mock_order]
        mock_mt5.initialize.return_value = True

        # Test
        result = self.client.orders_get()

        # Assertions
        assert len(result) == 1
        assert result[0]["ticket"] == 12345
        assert result[0]["symbol"] == "EURUSD"
        mock_mt5.orders_get.assert_called_once_with()

    @patch("backend.mt5_client.mt5")
    def test_orders_get_by_symbol(self, mock_mt5):
        """Test getting pending orders filtered by symbol."""
        mock_mt5.orders_get.return_value = []
        mock_mt5.initialize.return_value = True

        result = self.client.orders_get(symbol="EURUSD")

        mock_mt5.orders_get.assert_called_once_with(symbol="EURUSD")
        assert result == []

    @patch("backend.mt5_client.mt5")
    def test_orders_total(self, mock_mt5):
        """Test getting total number of pending orders."""
        mock_mt5.orders_total.return_value = 5
        mock_mt5.initialize.return_value = True

        result = self.client.orders_total()

        assert result == 5
        mock_mt5.orders_total.assert_called_once()

    @patch("backend.mt5_client.mt5")
    def test_order_send_pending_buy_limit(self, mock_mt5):
        """Test sending a buy limit pending order."""
        mock_result = Mock()
        mock_result.retcode = 10009  # Success
        mock_result.order = 12345
        mock_result.comment = "Order placed"

        mock_mt5.order_send.return_value = mock_result
        mock_mt5.initialize.return_value = True
        mock_mt5.symbol_select.return_value = True
        mock_mt5.ORDER_TYPE_BUY_LIMIT = 2
        mock_mt5.TRADE_ACTION_PENDING = 1
        mock_mt5.ORDER_FILLING_FOK = 0
        mock_mt5.ORDER_TIME_GTC = 0
        mock_mt5.last_error.return_value = (0, "Success")

        result = self.client.order_send_pending(
            symbol="EURUSD",
            order_type="buy_limit",
            volume=0.1,
            price=1.1000,
            sl=1.0950,
            tp=1.1100,
            deviation=10,
            comment="Test order",
            magic=123456,
        )

        assert result["retcode"] == 10009
        assert result["order"] == 12345
        mock_mt5.order_send.assert_called_once()

    @patch("backend.mt5_client.mt5")
    def test_order_send_pending_invalid_type(self, mock_mt5):
        """Test sending pending order with invalid type."""
        mock_mt5.initialize.return_value = True

        with pytest.raises(ValueError, match="Invalid order type"):
            self.client.order_send_pending(
                symbol="EURUSD",
                order_type="invalid_type",
                volume=0.1,
                price=1.1000,
                sl=None,
                tp=None,
                deviation=10,
                comment="Test",
                magic=0,
            )

    @patch("backend.mt5_client.mt5")
    def test_order_cancel(self, mock_mt5):
        """Test cancelling a pending order."""
        mock_result = Mock()
        mock_result.retcode = 10009
        mock_result.order = 12345
        mock_result.comment = "Order cancelled"

        mock_mt5.order_send.return_value = mock_result
        mock_mt5.initialize.return_value = True
        mock_mt5.TRADE_ACTION_REMOVE = 2
        mock_mt5.last_error.return_value = (0, "Success")

        result = self.client.order_cancel(12345)

        assert result["retcode"] == 10009
        assert result["order"] == 12345
        mock_mt5.order_send.assert_called_once()

    @patch("backend.mt5_client.mt5")
    def test_copy_rates_range(self, mock_mt5):
        """Test getting historical rates for date range."""
        # Mock rates data as list (numpy not required for test)
        mock_rates = [
            [1640995200, 1.1300, 1.1350, 1.1290, 1.1340, 1000, 2, 0],
            [1640995260, 1.1340, 1.1360, 1.1330, 1.1355, 1200, 3, 0],
        ]

        mock_mt5.copy_rates_range.return_value = mock_rates
        mock_mt5.initialize.return_value = True
        mock_mt5.TIMEFRAME_M1 = 1

        date_from = datetime(2022, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2022, 1, 2, tzinfo=timezone.utc)

        result = self.client.copy_rates_range(
            "EURUSD", mock_mt5.TIMEFRAME_M1, date_from, date_to
        )

        assert len(result) == 2
        assert result[0][1] == 1.1300  # Open price
        mock_mt5.copy_rates_range.assert_called_once_with(
            "EURUSD", mock_mt5.TIMEFRAME_M1, date_from, date_to
        )

    @patch("backend.mt5_client.mt5")
    def test_copy_ticks_range(self, mock_mt5):
        """Test getting historical ticks for date range."""
        mock_tick = Mock()
        mock_tick._asdict.return_value = {
            "time": 1640995200,
            "bid": 1.1300,
            "ask": 1.1305,
            "last": 1.1302,
            "volume": 100,
            "time_msc": 1640995200000,
            "flags": 6,
            "volume_real": 100.0,
        }

        mock_mt5.copy_ticks_range.return_value = [mock_tick]
        mock_mt5.initialize.return_value = True
        mock_mt5.COPY_TICKS_ALL = 7

        date_from = datetime(2022, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2022, 1, 2, tzinfo=timezone.utc)

        result = self.client.copy_ticks_range("EURUSD", date_from, date_to)

        assert len(result) == 1
        assert result[0]["bid"] == 1.1300
        mock_mt5.copy_ticks_range.assert_called_once()

    @patch("backend.mt5_client.mt5")
    def test_history_deals_get(self, mock_mt5):
        """Test getting trading deals history."""
        mock_deal = Mock()
        mock_deal._asdict.return_value = {
            "ticket": 54321,
            "order": 12345,
            "time": 1640995200,
            "type": 0,  # Buy
            "entry": 0,  # In
            "volume": 0.1,
            "price": 1.1300,
            "commission": -0.50,
            "swap": 0.0,
            "profit": 10.0,
            "symbol": "EURUSD",
            "comment": "Test deal",
        }

        mock_mt5.history_deals_get.return_value = [mock_deal]
        mock_mt5.initialize.return_value = True

        date_from = datetime(2022, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2022, 1, 2, tzinfo=timezone.utc)

        result = self.client.history_deals_get(date_from, date_to)

        assert len(result) == 1
        assert result[0]["ticket"] == 54321
        assert result[0]["profit"] == 10.0
        mock_mt5.history_deals_get.assert_called_once_with(date_from, date_to)

    @patch("backend.mt5_client.mt5")
    def test_history_deals_total(self, mock_mt5):
        """Test getting total number of deals in history."""
        mock_mt5.history_deals_total.return_value = 25
        mock_mt5.initialize.return_value = True

        date_from = datetime(2022, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2022, 1, 2, tzinfo=timezone.utc)

        result = self.client.history_deals_total(date_from, date_to)

        assert result == 25
        mock_mt5.history_deals_total.assert_called_once_with(date_from, date_to)

    @patch("backend.mt5_client.mt5")
    def test_history_orders_get(self, mock_mt5):
        """Test getting trading orders history."""
        mock_order = Mock()
        mock_order._asdict.return_value = {
            "ticket": 12345,
            "time_setup": 1640995200,
            "time_done": 1640995260,
            "symbol": "EURUSD",
            "type": 0,  # Buy
            "state": 4,  # Filled
            "volume_initial": 0.1,
            "price_open": 1.1300,
            "sl": 1.1250,
            "tp": 1.1400,
        }

        mock_mt5.history_orders_get.return_value = [mock_order]
        mock_mt5.initialize.return_value = True

        date_from = datetime(2022, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2022, 1, 2, tzinfo=timezone.utc)

        result = self.client.history_orders_get(date_from, date_to, symbol="EURUSD")

        assert len(result) == 1
        assert result[0]["ticket"] == 12345
        assert result[0]["state"] == 4
        mock_mt5.history_orders_get.assert_called_once_with(
            date_from, date_to, symbol="EURUSD"
        )

    @patch("backend.mt5_client.mt5")
    def test_history_orders_total(self, mock_mt5):
        """Test getting total number of orders in history."""
        mock_mt5.history_orders_total.return_value = 15
        mock_mt5.initialize.return_value = True

        date_from = datetime(2022, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2022, 1, 2, tzinfo=timezone.utc)

        result = self.client.history_orders_total(date_from, date_to)

        assert result == 15
        mock_mt5.history_orders_total.assert_called_once_with(date_from, date_to)
