"""
Integration tests for AI API endpoints.

Tests the full AI evaluation cycle through the API:
- AI status endpoint
- Manual evaluation trigger
- Enable/disable AI for symbols
- Strategy management
- Decision history
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from backend.app import app
from backend.models import TradeIdea, EMNRFlags, IndicatorValues, ExecutionPlan


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_mt5_client():
    """Mock MT5Client for testing."""
    mock = Mock()
    mock.get_bars = Mock(return_value=[
        {"time": 1000000 + i*60, "open": 1.1000 + i*0.0001, "high": 1.1005 + i*0.0001,
         "low": 1.0995 + i*0.0001, "close": 1.1002 + i*0.0001, "tick_volume": 100}
        for i in range(100)
    ])
    return mock


@pytest.fixture
def mock_trade_idea():
    """Create a mock trade idea for testing."""
    return TradeIdea(
        id="EURUSD_H1_20250101_120000",
        timestamp="2025-01-01T12:00:00+02:00",
        symbol="EURUSD",
        timeframe="H1",
        confidence=85,
        action="open_or_scale",
        direction="long",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        volume=0.01,
        rr_ratio=2.0,
        emnr_flags=EMNRFlags(entry=True, exit=False, strong=True, weak=False),
        indicators=IndicatorValues(
            ema_fast=1.1005,
            ema_slow=1.0995,
            rsi=55.0,
            macd=0.0005,
            macd_signal=0.0003,
            macd_hist=0.0002,
            atr=0.0025,
            atr_median=0.0020
        ),
        execution_plan=ExecutionPlan(action="open_or_scale", riskPct="0.010"),
        status="pending_approval"
    )


class TestAIStatusEndpoint:
    """Test AI status endpoint."""
    
    def test_get_ai_status_success(self, client):
        """Test getting AI status."""
        response = client.get("/api/ai/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "enabled" in data
        assert "mode" in data
        assert "enabled_symbols" in data
        assert "active_trade_ideas" in data
        assert "autonomy_loop_running" in data
    
    def test_ai_status_default_values(self, client):
        """Test AI status returns correct default values."""
        response = client.get("/api/ai/status")
        data = response.json()
        
        assert data["enabled"] is True
        assert data["mode"] == "semi-auto"
        assert isinstance(data["enabled_symbols"], list)
        assert isinstance(data["active_trade_ideas"], int)


class TestEvaluateEndpoint:
    """Test AI evaluation endpoint."""

    def test_evaluate_symbol_success(self, client, mock_trade_idea):
        """Test successful symbol evaluation."""
        # Mock the engine's evaluate method using dependency override
        mock_engine = Mock()
        mock_engine.evaluate = Mock(return_value=mock_trade_idea)

        # Override the dependency
        from backend import ai_routes
        app.dependency_overrides[ai_routes.get_ai_engine] = lambda: mock_engine

        try:
            response = client.post(
                "/api/ai/evaluate/EURUSD",
                json={"timeframe": "H1", "force": False}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["confidence"] == 85
            assert data["action"] == "open_or_scale"
            assert "trade_idea" in data
            assert data["trade_idea"]["symbol"] == "EURUSD"
        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_evaluate_symbol_no_idea(self, client):
        """Test evaluation when no trade idea is generated."""
        mock_engine = Mock()
        mock_engine.evaluate = Mock(return_value=None)

        # Override the dependency
        from backend import ai_routes
        app.dependency_overrides[ai_routes.get_ai_engine] = lambda: mock_engine

        try:
            response = client.post(
                "/api/ai/evaluate/EURUSD",
                json={"timeframe": "H1", "force": False}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["confidence"] == 0
            assert data["action"] == "observe"
            assert data["trade_idea"] is None
            assert "conditions not met" in data["message"].lower()
        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_evaluate_invalid_timeframe(self, client):
        """Test evaluation with invalid timeframe."""
        response = client.post(
            "/api/ai/evaluate/EURUSD",
            json={"timeframe": "INVALID", "force": False}
        )

        # Should return 422 for validation error
        assert response.status_code == 422


class TestEnableDisableEndpoints:
    """Test enable/disable AI endpoints."""
    
    def test_enable_ai_for_symbol(self, client):
        """Test enabling AI for a symbol."""
        response = client.post(
            "/api/ai/enable/EURUSD",
            json={"timeframe": "H1", "auto_execute": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "EURUSD" in data["message"]
        assert "config" in data
        assert data["config"]["timeframe"] == "H1"
        assert data["config"]["auto_execute"] is False
    
    def test_disable_ai_for_symbol(self, client):
        """Test disabling AI for a symbol."""
        # First enable it
        client.post(
            "/api/ai/enable/EURUSD",
            json={"timeframe": "H1", "auto_execute": False}
        )
        
        # Then disable it
        response = client.post("/api/ai/disable/EURUSD")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "disabled" in data["message"].lower()
    
    def test_disable_ai_not_enabled(self, client):
        """Test disabling AI for a symbol that's not enabled."""
        response = client.post("/api/ai/disable/GBPUSD")
        
        assert response.status_code == 404


class TestKillSwitchEndpoint:
    """Test emergency kill switch endpoint."""
    
    def test_kill_switch_activation(self, client):
        """Test activating the emergency kill switch."""
        # First enable AI for a symbol
        client.post(
            "/api/ai/enable/EURUSD",
            json={"timeframe": "H1", "auto_execute": False}
        )
        
        # Activate kill switch
        response = client.post(
            "/api/ai/kill-switch",
            json={"reason": "Testing emergency stop"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "disabled globally" in data["message"].lower()
        assert data["reason"] == "Testing emergency stop"
        assert "timestamp" in data
        
        # Verify AI is disabled
        status_response = client.get("/api/ai/status")
        status_data = status_response.json()
        assert status_data["enabled"] is False


class TestDecisionsEndpoint:
    """Test AI decisions history endpoint."""
    
    def test_get_decisions_empty(self, client):
        """Test getting decisions when none exist."""
        response = client.get("/api/ai/decisions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "count" in data
        assert "decisions" in data
        assert isinstance(data["decisions"], list)
    
    def test_get_decisions_with_limit(self, client):
        """Test getting decisions with limit parameter."""
        response = client.get("/api/ai/decisions?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["decisions"]) <= 10


class TestStrategiesEndpoints:
    """Test strategy management endpoints."""
    
    def test_list_strategies(self, client):
        """Test listing all strategies."""
        response = client.get("/api/ai/strategies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "count" in data
        assert "strategies" in data
        assert isinstance(data["strategies"], list)
    
    def test_get_strategy_existing(self, client):
        """Test getting an existing strategy."""
        response = client.get("/api/ai/strategies/EURUSD?timeframe=H1")
        
        # Should return 200 if strategy exists, 404 if not
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "strategy" in data
    
    def test_get_strategy_not_found(self, client):
        """Test getting a non-existent strategy."""
        response = client.get("/api/ai/strategies/NONEXISTENT?timeframe=H1")
        
        assert response.status_code == 404


class TestEndToEndEvaluation:
    """End-to-end integration tests."""

    def test_full_evaluation_cycle(self, client, mock_trade_idea):
        """Test complete evaluation cycle from enable to evaluate."""
        # Mock the engine
        from pathlib import Path
        mock_engine = Mock()
        mock_engine.evaluate = Mock(return_value=mock_trade_idea)
        mock_engine.settings = {"enabled": True, "mode": "semi-auto"}
        mock_engine.data_dir = Path("data/ai")  # Use real Path object for testing

        # Override the dependency
        from backend import ai_routes
        app.dependency_overrides[ai_routes.get_ai_engine] = lambda: mock_engine

        try:
            # 1. Check initial status
            status = client.get("/api/ai/status")
            assert status.status_code == 200

            # 2. Enable AI for EURUSD
            enable = client.post(
                "/api/ai/enable/EURUSD",
                json={"timeframe": "H1", "auto_execute": False}
            )
            assert enable.status_code == 200

            # 3. Trigger evaluation
            evaluate = client.post(
                "/api/ai/evaluate/EURUSD",
                json={"timeframe": "H1", "force": False}
            )
            assert evaluate.status_code == 200
            eval_data = evaluate.json()
            assert eval_data["confidence"] == 85
            assert eval_data["trade_idea"] is not None

            # 4. Check decisions history
            decisions = client.get("/api/ai/decisions?symbol=EURUSD&limit=10")
            assert decisions.status_code == 200

            # 5. Disable AI
            disable = client.post("/api/ai/disable/EURUSD")
            assert disable.status_code == 200
        finally:
            # Clean up override
            app.dependency_overrides.clear()

