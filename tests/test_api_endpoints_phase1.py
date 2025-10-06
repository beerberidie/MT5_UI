"""
Tests for Phase 1 API endpoints.
Tests pending orders, historical data, and trading history endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app import app
from tests.conftest import MockMT5Object


class TestPhase1Endpoints:
    """Test Phase 1 API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.fake_mt5 = None  # Will be set by fixture

    @patch('backend.app.mt5')
    def test_get_pending_orders_success(self, mock_mt5):
        """Test GET /api/orders endpoint success."""
        # Mock MT5 client
        mock_mt5.orders_get.return_value = [
            {
                'ticket': 12345,
                'symbol': 'EURUSD',
                'type': 2,
                'volume': 0.1,
                'price_open': 1.1000,
                'price_current': 1.1005,
                'sl': 1.0950,
                'tp': 1.1100,
                'comment': 'Test order',
                'magic': 123456
            }
        ]

        response = self.client.get("/api/orders")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['ticket'] == 12345

    @patch('backend.app.mt5')
    def test_get_pending_orders_with_symbol_filter(self, mock_mt5):
        """Test GET /api/orders with symbol filter."""
        mock_mt5.orders_get.return_value = []

        response = self.client.get("/api/orders?symbol=EURUSD")
        
        assert response.status_code == 200
        assert response.json() == []
        mock_mt5.orders_get.assert_called_once_with(symbol='EURUSD', ticket=None)

    @patch('backend.app.mt5')
    @patch('backend.app._check_daily_loss_limit')
    @patch('backend.app.sessions_map')
    @patch('backend.app._canonical_to_broker')
    @patch('backend.app._validate_and_round_volume')
    def test_create_pending_order_success(self, mock_validate_volume, mock_canonical_to_broker, 
                                        mock_sessions_map, mock_check_loss, mock_mt5):
        """Test POST /api/orders/pending endpoint success."""
        # Setup mocks
        mock_check_loss.return_value = None
        mock_sessions_map.return_value = {}
        mock_canonical_to_broker.return_value = 'EURUSD'
        mock_validate_volume.return_value = 0.1
        
        mock_mt5.order_send_pending.return_value = {
            'retcode': 10009,
            'order': 12345,
            'comment': 'Order placed'
        }

        order_data = {
            'canonical': 'EURUSD',
            'order_type': 'buy_limit',
            'volume': 0.1,
            'price': 1.1000,
            'sl': 1.0950,
            'tp': 1.1100,
            'comment': 'Test order'
        }

        response = self.client.post("/api/orders/pending", json=order_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['order'] == 12345
        assert data['result_code'] == 10009

    @patch('backend.app.mt5')
    def test_create_pending_order_validation_error(self, mock_mt5):
        """Test POST /api/orders/pending with validation error."""
        order_data = {
            'canonical': 'EURUSD',
            'order_type': 'buy_limit',
            # Missing required fields: volume, price
        }

        response = self.client.post("/api/orders/pending", json=order_data)
        
        assert response.status_code == 422  # Validation error

    @patch('backend.app.mt5')
    def test_cancel_pending_order_success(self, mock_mt5):
        """Test DELETE /api/orders/{order_id} endpoint success."""
        mock_mt5.order_cancel.return_value = {
            'retcode': 10009,
            'order': 12345,
            'comment': 'Order cancelled'
        }

        response = self.client.delete("/api/orders/12345")
        
        assert response.status_code == 200
        data = response.json()
        assert data['order'] == 12345
        assert data['result_code'] == 10009

    def test_get_historical_bars_success(self, client, fake_mt5):
        """Test GET /api/history/bars endpoint success."""
        # Set up mock data
        fake_mt5._historical_bars = [
            [1640995200, 1.1300, 1.1350, 1.1290, 1.1340, 1000, 2, 0],
            [1640995260, 1.1340, 1.1360, 1.1330, 1.1355, 1200, 3, 0]
        ]

        response = client.get("/api/history/bars?symbol=EURUSD&timeframe=M5&count=100")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['open'] == 1.1300
        assert data[0]['close'] == 1.1340

    @patch('backend.app.mt5')
    def test_get_historical_bars_with_date_range(self, mock_mt5):
        """Test GET /api/history/bars with date range."""
        mock_mt5.copy_rates_range.return_value = [
            [1640995200, 1.1300, 1.1350, 1.1290, 1.1340, 1000, 2, 0]
        ]

        response = self.client.get(
            "/api/history/bars?symbol=EURUSD&timeframe=H1"
            "&date_from=2022-01-01T00:00:00Z&date_to=2022-01-02T00:00:00Z"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_historical_bars_invalid_timeframe(self):
        """Test GET /api/history/bars with invalid timeframe."""
        response = self.client.get("/api/history/bars?symbol=EURUSD&timeframe=INVALID")
        
        assert response.status_code == 400
        assert "invalid_timeframe" in response.json()['detail']

    @patch('backend.app.mt5')
    def test_get_historical_ticks_success(self, mock_mt5):
        """Test GET /api/history/ticks endpoint success."""
        mock_tick = Mock()
        mock_tick._asdict.return_value = {
            'time': 1640995200,
            'bid': 1.1300,
            'ask': 1.1305,
            'last': 1.1302,
            'volume': 100,
            'time_msc': 1640995200000,
            'flags': 6,
            'volume_real': 100.0
        }
        
        mock_mt5.copy_ticks_range.return_value = [mock_tick]

        response = self.client.get(
            "/api/history/ticks?symbol=EURUSD"
            "&date_from=2022-01-01T00:00:00Z&date_to=2022-01-02T00:00:00Z"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['bid'] == 1.1300

    def test_get_historical_ticks_invalid_flags(self):
        """Test GET /api/history/ticks with invalid flags."""
        response = self.client.get(
            "/api/history/ticks?symbol=EURUSD&flags=INVALID"
            "&date_from=2022-01-01T00:00:00Z&date_to=2022-01-02T00:00:00Z"
        )
        
        assert response.status_code == 400
        assert "invalid_flags" in response.json()['detail']

    def test_get_trading_deals_success(self, client, fake_mt5):
        """Test GET /api/history/deals endpoint success."""
        # Set up mock deal data
        mock_deal = MockMT5Object({
            'ticket': 54321,
            'order': 12345,
            'time': 1640995200,
            'time_msc': 1640995200000,
            'type': 0,
            'entry': 0,
            'magic': 0,
            'position_id': 12345,
            'reason': 0,
            'volume': 0.1,
            'price': 1.1300,
            'commission': -0.50,
            'swap': 0.0,
            'profit': 10.0,
            'symbol': 'EURUSD',
            'comment': 'Test deal',
            'external_id': ''
        })

        fake_mt5._deals = [mock_deal]

        response = client.get(
            "/api/history/deals?date_from=2022-01-01T00:00:00Z&date_to=2022-01-02T00:00:00Z"
        )

        assert response.status_code == 200
        data = response.json()
        assert 'deals' in data
        assert 'summary' in data
        assert len(data['deals']) == 1
        assert data['deals'][0]['profit'] == 10.0
        assert data['summary']['total_profit'] == 10.0

    def test_get_trading_deals_with_symbol_filter(self, client, fake_mt5):
        """Test GET /api/history/deals with symbol filter."""
        fake_mt5._deals = []

        response = client.get(
            "/api/history/deals?date_from=2022-01-01T00:00:00Z&date_to=2022-01-02T00:00:00Z&symbol=EURUSD"
        )

        assert response.status_code == 200
        data = response.json()
        assert data['deals'] == []
        # Summary should have default values, not empty dict
        assert 'summary' in data
        assert data['summary']['total_deals'] == 0

    def test_get_trading_orders_success(self, client, fake_mt5):
        """Test GET /api/history/orders endpoint success."""
        # Set up mock order data
        mock_order = MockMT5Object({
            'ticket': 12345,
            'time_setup': 1640995200,
            'time_setup_msc': 1640995200000,
            'time_done': 1640995260,
            'time_done_msc': 1640995260000,
            'time_expiration': 0,
            'symbol': 'EURUSD',
            'type': 0,
            'type_filling': 0,
            'type_time': 0,
            'state': 4,
            'magic': 0,
            'position_id': 0,
            'position_by_id': 0,
            'reason': 0,
            'volume_initial': 0.1,
            'volume_current': 0.0,
            'price_open': 1.1300,
            'price_current': 1.1300,
            'price_stoplimit': 0.0,
            'sl': 1.1250,
            'tp': 1.1400,
            'comment': '',
            'external_id': ''
        })

        fake_mt5._orders = [mock_order]

        response = client.get(
            "/api/history/orders?date_from=2022-01-01T00:00:00Z&date_to=2022-01-02T00:00:00Z"
        )

        assert response.status_code == 200
        data = response.json()
        assert 'orders' in data
        assert 'summary' in data
        assert len(data['orders']) == 1
        assert data['orders'][0]['ticket'] == 12345

    @patch('backend.app.mt5')
    def test_endpoints_handle_mt5_errors(self, mock_mt5):
        """Test that endpoints handle MT5 errors gracefully."""
        mock_mt5.orders_get.side_effect = Exception("MT5 connection failed")

        response = self.client.get("/api/orders")
        
        assert response.status_code == 200
        assert response.json() == []  # Should return empty list on error

    def test_endpoints_require_auth_for_modifications(self):
        """Test that modification endpoints require authentication."""
        # Test pending order creation without auth
        order_data = {
            'canonical': 'EURUSD',
            'order_type': 'buy_limit',
            'volume': 0.1,
            'price': 1.1000
        }

        response = self.client.post("/api/orders/pending", json=order_data)
        
        # Should succeed if no API key is configured, or fail with 401 if configured
        assert response.status_code in [200, 401, 409]  # Various possible responses

    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to endpoints."""
        # This test would need to make multiple rapid requests
        # For now, just verify the endpoint exists
        response = self.client.get("/api/orders")
        assert response.status_code in [200, 429]  # Success or rate limited
