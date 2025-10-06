"""
Tests for AI Trade Idea Executor
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.ai.executor import TradeIdeaExecutor, ExecutionResult, ValidationResult
from backend.models import TradeIdea, ExecutionPlan, EMNRFlags, IndicatorValues


@pytest.fixture
def mock_mt5_client():
    """Mock MT5 client."""
    client = Mock()
    client.get_symbol_info = Mock(return_value={
        'volume_min': 0.01,
        'volume_max': 100.0,
        'volume_step': 0.01,
        'trade_contract_size': 100000
    })
    client.place_order = Mock(return_value={
        'success': True,
        'order_id': 12345
    })
    client.get_account_info = Mock(return_value={
        'balance': 10000.0,
        'equity': 10000.0
    })
    return client


@pytest.fixture
def executor(mock_mt5_client, tmp_path):
    """Create executor instance."""
    return TradeIdeaExecutor(
        mt5_client=mock_mt5_client,
        log_dir=str(tmp_path)
    )


@pytest.fixture
def valid_trade_idea():
    """Create a valid trade idea for testing."""
    return TradeIdea(
        id="test-idea-001",
        timestamp=datetime.utcnow().isoformat(),
        symbol="EURUSD",
        timeframe="H1",
        confidence=80,
        action="open_or_scale",
        direction="long",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        volume=0.1,
        rr_ratio=2.0,
        emnr_flags=EMNRFlags(entry=True, exit=False, strong=True, weak=False),
        indicators=IndicatorValues(
            ema_fast=1.0990,
            ema_slow=1.0980,
            rsi=55.0,
            macd=0.0005,
            atr=0.0015,
            atr_median=0.0014
        ),
        execution_plan=ExecutionPlan(action="open_or_scale", riskPct="1.0"),
        status="approved"
    )


class TestValidation:
    """Test execution safety validation."""
    
    @pytest.mark.asyncio
    async def test_validate_approved_idea(self, executor, valid_trade_idea):
        """Test validation of approved trade idea."""
        result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
        assert result.valid is True
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_pending_idea_fails(self, executor, valid_trade_idea):
        """Test validation fails for pending idea."""
        valid_trade_idea.status = "pending_approval"
        result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
        assert result.valid is False
        assert any("approved" in err.lower() for err in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_low_rr_fails(self, executor, valid_trade_idea):
        """Test validation fails for low RR ratio."""
        valid_trade_idea.rr_ratio = 1.5
        result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
        assert result.valid is False
        assert any("rr ratio" in err.lower() for err in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_low_confidence_fails(self, executor, valid_trade_idea):
        """Test validation fails for low confidence."""
        valid_trade_idea.confidence = 60
        result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
        assert result.valid is False
        assert any("confidence" in err.lower() for err in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_volume_fails(self, executor, valid_trade_idea):
        """Test validation fails for invalid volume."""
        valid_trade_idea.volume = 0.0
        result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
        assert result.valid is False
        assert any("volume" in err.lower() for err in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_daily_loss_limit_fails(self, executor, valid_trade_idea):
        """Test validation fails when daily loss limit reached."""
        # Mock the daily loss calculation to return a loss exceeding the limit
        with patch('backend.ai.executor.risk_limits', return_value={'daily_loss_limit_r': '500'}):
            with patch('backend.app._calculate_daily_pnl', return_value=-600.0):
                result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
                assert result.valid is False
                assert any("daily loss" in err.lower() for err in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_high_risk_fails(self, executor, valid_trade_idea):
        """Test validation fails for excessive risk percentage."""
        valid_trade_idea.execution_plan.riskPct = "10.0"  # 10% is too high
        result = await executor.validate_execution_safety(valid_trade_idea, 10000.0)
        assert result.valid is False
        assert any("risk percentage" in err.lower() for err in result.errors)


class TestPositionSizing:
    """Test position size calculation."""
    
    def test_calculate_position_size(self, executor, valid_trade_idea):
        """Test position size calculation."""
        volume = executor.calculate_position_size(valid_trade_idea, 10000.0)
        assert volume > 0
        assert volume >= 0.01  # Min volume
        assert volume <= 100.0  # Max volume
    
    def test_position_size_respects_limits(self, executor, valid_trade_idea, mock_mt5_client):
        """Test position size respects symbol limits."""
        mock_mt5_client.get_symbol_info = Mock(return_value={
            'volume_min': 0.1,
            'volume_max': 1.0,
            'volume_step': 0.1
        })
        
        volume = executor.calculate_position_size(valid_trade_idea, 10000.0)
        assert volume >= 0.1
        assert volume <= 1.0
        assert volume % 0.1 == 0  # Respects step
    
    def test_position_size_fallback_on_error(self, executor, valid_trade_idea, mock_mt5_client):
        """Test position size falls back to idea volume on error."""
        mock_mt5_client.get_symbol_info = Mock(return_value=None)
        
        volume = executor.calculate_position_size(valid_trade_idea, 10000.0)
        assert volume == valid_trade_idea.volume


class TestExecution:
    """Test trade idea execution."""
    
    @pytest.mark.asyncio
    async def test_execute_valid_idea(self, executor, valid_trade_idea, mock_mt5_client):
        """Test successful execution of valid trade idea."""
        result = await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        assert result.success is True
        assert result.order_id == 12345
        assert mock_mt5_client.place_order.called
    
    @pytest.mark.asyncio
    async def test_execute_calls_place_order_with_correct_params(
        self, executor, valid_trade_idea, mock_mt5_client
    ):
        """Test execution calls place_order with correct parameters."""
        await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        call_args = mock_mt5_client.place_order.call_args
        assert call_args[1]['canonical'] == "EURUSD"
        assert call_args[1]['order_type'] == "buy"
        assert call_args[1]['sl'] == 1.0950
        assert call_args[1]['tp'] == 1.1100
        assert "AI:" in call_args[1]['comment']
    
    @pytest.mark.asyncio
    async def test_execute_short_idea(self, executor, valid_trade_idea, mock_mt5_client):
        """Test execution of short trade idea."""
        valid_trade_idea.direction = "short"
        await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        call_args = mock_mt5_client.place_order.call_args
        assert call_args[1]['order_type'] == "sell"
    
    @pytest.mark.asyncio
    async def test_execute_invalid_idea_fails(self, executor, valid_trade_idea):
        """Test execution fails for invalid trade idea."""
        valid_trade_idea.status = "pending_approval"
        result = await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        assert result.success is False
        assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_execute_mt5_error_returns_failure(
        self, executor, valid_trade_idea, mock_mt5_client
    ):
        """Test execution returns failure when MT5 returns error."""
        mock_mt5_client.place_order = Mock(return_value={
            'success': False,
            'error': 'Insufficient margin'
        })
        
        result = await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        assert result.success is False
        assert "margin" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_exception_returns_failure(
        self, executor, valid_trade_idea, mock_mt5_client
    ):
        """Test execution returns failure when exception occurs."""
        mock_mt5_client.place_order = Mock(side_effect=Exception("Connection error"))
        
        result = await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        assert result.success is False
        assert "exception" in result.error.lower()


class TestLogging:
    """Test execution logging."""
    
    @pytest.mark.asyncio
    async def test_execution_logged(self, executor, valid_trade_idea, tmp_path):
        """Test execution is logged to CSV."""
        await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        log_file = tmp_path / "ai_executions.csv"
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "test-idea-001" in content
        assert "EURUSD" in content
        assert "True" in content  # Success
    
    @pytest.mark.asyncio
    async def test_failed_execution_logged(self, executor, valid_trade_idea, tmp_path, mock_mt5_client):
        """Test failed execution is logged."""
        mock_mt5_client.place_order = Mock(return_value={
            'success': False,
            'error': 'Test error'
        })
        
        await executor.execute_trade_idea(valid_trade_idea, 10000.0)
        
        log_file = tmp_path / "ai_executions.csv"
        content = log_file.read_text()
        assert "False" in content  # Failed
        assert "Test error" in content

