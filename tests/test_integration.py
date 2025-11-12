"""
Integration tests for MT5 Trading Workstation API with authentication and security scenarios.
"""

import os
import json
import tempfile
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

import backend.app as app_module
import backend.config as config_module


class TestAuthenticationIntegration:
    """Test authentication flows and security scenarios."""

    def test_order_without_api_key_when_required(self, temp_dirs, fake_mt5):
        """Test that orders are rejected when API key is required but not provided."""
        # Clear any existing dependency overrides
        app_module.app.dependency_overrides.clear()

        # Set API key requirement
        with patch.object(app_module, "AUGMENT_API_KEY", "test-key-123"):
            # Create client without dependency override
            client = TestClient(app_module.app)

            payload = {
                "canonical": "EURUSD",
                "side": "buy",
                "volume": 0.01,
                "deviation": 10,
                "comment": "test",
                "magic": 1,
            }

            response = client.post("/api/order", json=payload)
            assert response.status_code == 401
            assert "invalid_api_key" in response.json()["detail"]

    def test_order_with_valid_api_key(self, temp_dirs, fake_mt5):
        """Test that orders succeed with valid API key."""
        # Clear any existing dependency overrides
        app_module.app.dependency_overrides.clear()

        # Patch the AUGMENT_API_KEY at the app module level
        with patch.object(app_module, "AUGMENT_API_KEY", "test-key-123"):
            client = TestClient(app_module.app)

            payload = {
                "canonical": "EURUSD",
                "side": "buy",
                "volume": 0.01,
                "deviation": 10,
                "comment": "test",
                "magic": 1,
            }

            headers = {"X-API-Key": "test-key-123"}
            response = client.post("/api/order", json=payload, headers=headers)
            assert response.status_code == 200
            assert "result_code" in response.json()

    def test_order_with_invalid_api_key(self, temp_dirs, fake_mt5):
        """Test that orders are rejected with invalid API key."""
        # Clear any existing dependency overrides
        app_module.app.dependency_overrides.clear()

        with patch.object(app_module, "AUGMENT_API_KEY", "test-key-123"):
            client = TestClient(app_module.app)

            payload = {
                "canonical": "EURUSD",
                "side": "buy",
                "volume": 0.01,
                "deviation": 10,
                "comment": "test",
                "magic": 1,
            }

            headers = {"X-API-Key": "wrong-key"}
            response = client.post("/api/order", json=payload, headers=headers)
            assert response.status_code == 401
            assert "invalid_api_key" in response.json()["detail"]


class TestRateLimitingIntegration:
    """Test rate limiting functionality."""

    def test_rate_limit_exceeded_on_order_endpoint(self, temp_dirs, fake_mt5):
        """Test that rate limiting works on order endpoint."""
        # Clear any existing rate limits first
        app_module.limiter.reset()

        client = TestClient(app_module.app)
        # Override API key dependency for testing
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.01,
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        # Make requests up to the limit (10/minute)
        success_count = 0
        rate_limited_count = 0

        for i in range(12):  # Exceed the limit
            response = client.post("/api/order", json=payload)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1

        # We should have some successful requests and some rate limited
        assert success_count > 0, "Should have some successful requests"
        assert rate_limited_count > 0, "Should have some rate limited requests"

        # Clean up
        app_module.app.dependency_overrides.clear()


class TestVolumeValidationIntegration:
    """Test volume validation and rounding."""

    def test_volume_too_small_rejection(self, temp_dirs, fake_mt5):
        """Test that volumes below minimum are rejected."""
        # Clear rate limits for this test
        app_module.limiter.reset()

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.001,  # Below minimum of 0.01
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 400
        assert "VOLUME_TOO_SMALL" in str(response.json())

        app_module.app.dependency_overrides.clear()

    def test_volume_rounding(self, temp_dirs, fake_mt5):
        """Test that volumes are properly rounded to valid steps."""
        # Clear rate limits for this test
        app_module.limiter.reset()

        client = TestClient(app_module.app)
        app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None

        payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.015,  # Should round to 0.02 (step 0.01)
            "deviation": 10,
            "comment": "test",
            "magic": 1,
        }

        response = client.post("/api/order", json=payload)
        assert response.status_code == 200

        app_module.app.dependency_overrides.clear()


class TestInputValidationIntegration:
    """Test input validation for security."""

    def test_path_traversal_protection_ticks(self, temp_dirs, fake_mt5):
        """Test that path traversal attempts are blocked in ticks endpoint."""
        client = TestClient(app_module.app)

        # Attempt path traversal
        response = client.get("/api/ticks?canonical=../../../etc/passwd")
        assert response.status_code == 400
        assert "invalid_symbol_format" in response.json()["detail"]

    def test_path_traversal_protection_bars(self, temp_dirs, fake_mt5):
        """Test that path traversal attempts are blocked in bars endpoint."""
        client = TestClient(app_module.app)

        # Attempt path traversal
        response = client.get("/api/bars?canonical=../../../etc/passwd")
        assert response.status_code == 400
        assert "invalid_symbol_format" in response.json()["detail"]

    def test_invalid_timeframe_rejection(self, temp_dirs, fake_mt5):
        """Test that invalid timeframes are rejected."""
        client = TestClient(app_module.app)

        response = client.get("/api/bars?canonical=EURUSD&tf=INVALID")
        assert response.status_code == 400
        assert "invalid_timeframe" in response.json()["detail"]


class TestErrorHandlingIntegration:
    """Test error handling and logging."""

    def test_mt5_unavailable_error_handling(self, temp_dirs):
        """Test proper error handling when MT5 is unavailable."""
        # Clear rate limits for this test
        app_module.limiter.reset()

        # Create a fake MT5 client that raises exceptions
        class FailingMT5Client:
            def order_send(self, **kwargs):
                raise RuntimeError("MT5 not connected")

        with patch.object(app_module, "mt5", FailingMT5Client()):
            client = TestClient(app_module.app)
            app_module.app.dependency_overrides[app_module.require_api_key] = (
                lambda: None
            )

            payload = {
                "canonical": "EURUSD",
                "side": "buy",
                "volume": 0.01,
                "deviation": 10,
                "comment": "test",
                "magic": 1,
            }

            response = client.post("/api/order", json=payload)
            assert response.status_code == 503
            assert "MT5_UNAVAILABLE" in str(response.json())

            app_module.app.dependency_overrides.clear()


class TestSecurityLoggingIntegration:
    """Test security event logging."""

    def test_security_events_logged(self, temp_dirs, fake_mt5):
        """Test that security events are properly logged."""
        # Clear rate limits for this test
        app_module.limiter.reset()

        with patch.object(app_module, "AUGMENT_API_KEY", "test-key-123"):
            client = TestClient(app_module.app)

            payload = {
                "canonical": "EURUSD",
                "side": "buy",
                "volume": 0.01,
                "deviation": 10,
                "comment": "test",
                "magic": 1,
            }

            # Make request with wrong API key
            headers = {"X-API-Key": "wrong-key"}
            response = client.post("/api/order", json=payload, headers=headers)
            assert response.status_code == 401

            # Check that security log was created
            security_log_path = os.path.join(temp_dirs["logs"], "security.csv")
            assert os.path.exists(security_log_path)

            # Read and verify log content
            from backend.csv_io import read_csv_rows

            log_entries = read_csv_rows(security_log_path)
            assert len(log_entries) > 0
            assert any(
                "invalid_api_key_attempt" in entry.get("event_type", "")
                for entry in log_entries
            )
