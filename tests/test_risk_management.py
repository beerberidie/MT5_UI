"""
Tests for risk management functionality including daily loss limits and volume validation.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

import backend.app as app_module
import backend.config as config_module
from backend.csv_io import append_csv, utcnow_iso


class TestDailyLossLimit:
    """Test daily loss limit enforcement."""

    def test_daily_loss_limit_enforcement(self, temp_dirs, fake_mt5):
        """Test that trading is blocked when daily loss limit is exceeded."""
        # Set up risk limits with daily loss limit
        risk_limits_path = os.path.join(temp_dirs["config"], "risk_limits.csv")
        with open(risk_limits_path, "w", encoding="utf-8") as f:
            f.write("key,value,notes\n")
            f.write("daily_loss_limit_r,100,Daily loss limit in currency units\n")

        # Create fake orders log with losses exceeding the limit
        orders_log_path = os.path.join(temp_dirs["logs"], "orders.csv")
        today = utcnow_iso()[:10]  # Get today's date

        # Simulate previous losing trades
        for i in range(
            15
        ):  # 15 trades * 10 loss per lot = 150 loss (exceeds 100 limit)
            append_csv(
                orders_log_path,
                {
                    "ts_utc": f"{today}T10:0{i:02d}:00.000Z",
                    "action": "market_buy",
                    "canonical": "EURUSD",
                    "broker_symbol": "EURUSD",
                    "req_json": '{"volume": 1.0}',
                    "result_code": "10009",
                    "order": str(1000 + i),
                    "position": str(2000 + i),
                    "price": None,
                    "volume": "1.0",
                    "sl": "",
                    "tp": "",
                    "comment": "test trade",
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

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.01,
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 409
        response_data = response.json()
        assert "DAILY_LOSS_LIMIT_EXCEEDED" in str(response_data)

        app_module.app.dependency_overrides.clear()

    def test_daily_loss_limit_disabled_when_zero(self, temp_dirs, fake_mt5):
        """Test that daily loss limit is disabled when set to 0."""
        # Set up risk limits with disabled daily loss limit
        risk_limits_path = os.path.join(temp_dirs["config"], "risk_limits.csv")
        with open(risk_limits_path, "w", encoding="utf-8") as f:
            f.write("key,value,notes\n")
            f.write("daily_loss_limit_r,0,Disabled\n")

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.01,
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 200  # Should succeed even with losses

        app_module.app.dependency_overrides.clear()


class TestVolumeValidation:
    """Test volume validation and rounding functionality."""

    def test_volume_validation_with_custom_symbol_config(self, temp_dirs, fake_mt5):
        """Test volume validation with custom symbol configuration."""
        # Set up symbol map with custom volume constraints
        symbol_map_path = os.path.join(temp_dirs["config"], "symbol_map.csv")
        with open(symbol_map_path, "w", encoding="utf-8") as f:
            f.write("canonical,broker_symbol,enabled,min_vol,vol_step,comment\n")
            f.write("EURUSD,EURUSD,true,0.1,0.1,Custom volume settings\n")

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        # Test volume below minimum
        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.05,  # Below minimum of 0.1
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 400
        response_data = response.json()
        assert "VOLUME_TOO_SMALL" in str(response_data)

        app_module.app.dependency_overrides.clear()

    def test_volume_rounding_precision(self, temp_dirs, fake_mt5):
        """Test that volume rounding maintains proper precision."""
        # Set up symbol map with fine-grained volume steps
        symbol_map_path = os.path.join(temp_dirs["config"], "symbol_map.csv")
        with open(symbol_map_path, "w", encoding="utf-8") as f:
            f.write("canonical,broker_symbol,enabled,min_vol,vol_step,comment\n")
            f.write("EURUSD,EURUSD,true,0.01,0.01,Standard settings\n")

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        # Test volume that needs rounding
        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.016,  # Should round to 0.02 (0.016-0.01)/0.01 = 0.6, round(0.6) = 1
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 200

        # Verify the volume was rounded correctly in the logs
        orders_log_path = os.path.join(temp_dirs["logs"], "orders.csv")
        assert os.path.exists(orders_log_path)

        from backend.csv_io import read_csv_rows

        log_entries = read_csv_rows(orders_log_path)
        assert len(log_entries) > 0

        # Check that the logged volume is the rounded value
        latest_entry = log_entries[-1]
        assert float(latest_entry["volume"]) == 0.02

        app_module.app.dependency_overrides.clear()


class TestSessionValidation:
    """Test trading session validation."""

    def test_session_blocking_outside_hours(self, temp_dirs, fake_mt5):
        """Test that trading is blocked outside session hours."""
        # Set up sessions with restrictive hours
        sessions_path = os.path.join(temp_dirs["config"], "sessions.csv")
        with open(sessions_path, "w", encoding="utf-8") as f:
            f.write("canonical,trade_start_utc,trade_end_utc,block_on_closed,notes\n")
            f.write("EURUSD,08:00:00,16:00:00,true,Restrictive hours\n")

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.01,
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        # Mock current time to be outside session hours
        from datetime import datetime, timezone

        mock_time = datetime(2024, 1, 1, 20, 0, 0, tzinfo=timezone.utc)  # 20:00 UTC

        with patch("backend.app.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time
            mock_datetime.strftime = datetime.strftime

            response = client.post("/api/order", json=payload)
            assert response.status_code == 409
            response_data = response.json()
            assert "RISK_BLOCK" in str(response_data)
            assert "Outside session window" in str(response_data)

        app_module.app.dependency_overrides.clear()

    def test_session_allowing_during_hours(self, temp_dirs, fake_mt5):
        """Test that trading is allowed during session hours."""
        # Set up sessions with current time within hours
        sessions_path = os.path.join(temp_dirs["config"], "sessions.csv")
        with open(sessions_path, "w", encoding="utf-8") as f:
            f.write("canonical,trade_start_utc,trade_end_utc,block_on_closed,notes\n")
            f.write("EURUSD,00:00:00,23:59:59,true,Always open\n")

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.01,
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 200

        app_module.app.dependency_overrides.clear()


class TestErrorSanitization:
    """Test that error messages are properly sanitized."""

    def test_api_key_sanitization_in_logs(self, temp_dirs, fake_mt5):
        """Test that API keys are sanitized in error logs."""
        # Test the sanitization function directly
        message_with_key = "Authentication failed with API_KEY=AC135782469AD for user"
        sanitized = app_module._sanitize_message(message_with_key)

        # Verify the message was sanitized
        assert "API_KEY=***" in sanitized
        assert "AC135782469AD" not in sanitized

    def test_password_sanitization_in_logs(self, temp_dirs, fake_mt5):
        """Test that passwords are sanitized in error logs."""
        # Test the sanitization function directly
        message_with_password = "Database connection failed: password=secret123"
        sanitized = app_module._sanitize_message(message_with_password)

        # Verify the message was sanitized
        assert "password=***" in sanitized
        assert "secret123" not in sanitized
