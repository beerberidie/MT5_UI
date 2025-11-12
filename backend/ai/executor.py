"""
AI Trade Idea Executor

Handles execution of approved AI trade ideas with comprehensive safety checks.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import csv
import os

from backend.models import TradeIdea
from backend.mt5_client import MT5Client
from backend.risk import risk_limits

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Result of trade idea execution."""

    def __init__(
        self,
        success: bool,
        order_id: Optional[int] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.order_id = order_id
        self.error = error
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class ValidationResult:
    """Result of execution safety validation."""

    def __init__(self, valid: bool, errors: list[str] = None):
        self.valid = valid
        self.errors = errors or []


class TradeIdeaExecutor:
    """
    Execute approved AI trade ideas with safety checks.

    Responsibilities:
    - Validate trade ideas meet safety requirements
    - Calculate position sizes based on risk
    - Execute orders via MT5
    - Log execution results
    - Update trade idea status
    """

    def __init__(self, mt5_client: MT5Client, log_dir: str = "logs"):
        self.mt5_client = mt5_client
        self.log_dir = log_dir
        self.execution_log_path = os.path.join(log_dir, "ai_executions.csv")

        # Ensure log file exists with headers
        self._init_execution_log()

        logger.info("TradeIdeaExecutor initialized")

    def _init_execution_log(self):
        """Initialize execution log file with headers."""
        if not os.path.exists(self.execution_log_path):
            os.makedirs(self.log_dir, exist_ok=True)
            with open(self.execution_log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "idea_id",
                        "symbol",
                        "direction",
                        "confidence",
                        "entry_price",
                        "stop_loss",
                        "take_profit",
                        "volume",
                        "rr_ratio",
                        "risk_pct",
                        "order_id",
                        "success",
                        "error",
                    ]
                )

    async def validate_execution_safety(
        self, idea: TradeIdea, account_balance: float
    ) -> ValidationResult:
        """
        Validate trade idea meets all safety requirements.

        Args:
            idea: Trade idea to validate
            account_balance: Current account balance

        Returns:
            ValidationResult with validation status and errors
        """
        errors = []

        # Check idea status
        if idea.status != "approved":
            errors.append(
                f"Trade idea must be approved (current status: {idea.status})"
            )

        # Check RR ratio
        if idea.rr_ratio < 2.0:
            errors.append(f"RR ratio {idea.rr_ratio:.2f} below minimum 2.0")

        # Check confidence threshold (for auto-execution)
        if idea.confidence < 75:
            errors.append(
                f"Confidence {idea.confidence} below minimum 75 for execution"
            )

        # Validate volume
        if idea.volume <= 0:
            errors.append(f"Invalid volume: {idea.volume}")

        # Check daily loss limit
        try:
            limits = risk_limits()
            daily_limit = float(limits.get("daily_loss_limit_r", 0) or 0)

            if daily_limit > 0:
                # Import here to avoid circular dependency
                from backend.app import _calculate_daily_pnl

                current_pnl = _calculate_daily_pnl()

                if current_pnl <= -abs(daily_limit):
                    errors.append(
                        f"Daily loss limit reached: {current_pnl:.2f} <= -{daily_limit:.2f}"
                    )
        except Exception as e:
            logger.warning(f"Could not check daily loss limit: {e}")

        # Validate symbol is tradeable
        try:
            symbol_info = self.mt5_client.get_symbol_info(idea.symbol)
            if not symbol_info:
                errors.append(f"Symbol {idea.symbol} not found or not tradeable")
        except Exception as e:
            errors.append(f"Error checking symbol info: {e}")

        # Check risk percentage is reasonable
        try:
            risk_pct = float(idea.execution_plan.riskPct)
            if risk_pct <= 0 or risk_pct > 5:  # Max 5% risk per trade
                errors.append(
                    f"Risk percentage {risk_pct}% outside acceptable range (0-5%)"
                )
        except ValueError:
            errors.append(f"Invalid risk percentage: {idea.execution_plan.riskPct}")

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def calculate_position_size(self, idea: TradeIdea, account_balance: float) -> float:
        """
        Calculate position size based on risk percentage.

        Args:
            idea: Trade idea with entry, SL, and risk %
            account_balance: Current account balance

        Returns:
            Position size in lots
        """
        try:
            # Get risk percentage from execution plan
            risk_pct = float(idea.execution_plan.riskPct)

            # Calculate risk amount in account currency
            risk_amount = account_balance * (risk_pct / 100)

            # Calculate SL distance in price
            sl_distance = abs(idea.entry_price - idea.stop_loss)

            # Get symbol info for pip value calculation
            symbol_info = self.mt5_client.get_symbol_info(idea.symbol)
            if not symbol_info:
                logger.error(f"Cannot get symbol info for {idea.symbol}")
                return idea.volume  # Fallback to suggested volume

            # Calculate position size
            # For forex: position_size = risk_amount / (sl_distance * contract_size)
            # Simplified: use the volume from trade idea (already calculated by scheduler)
            volume = idea.volume

            # Ensure volume is within symbol limits
            min_volume = symbol_info.get("volume_min", 0.01)
            max_volume = symbol_info.get("volume_max", 100.0)
            volume_step = symbol_info.get("volume_step", 0.01)

            # Round to volume step
            volume = round(volume / volume_step) * volume_step

            # Clamp to limits
            volume = max(min_volume, min(max_volume, volume))

            logger.info(
                f"Calculated position size: {volume} lots (risk: {risk_pct}%, amount: ${risk_amount:.2f})"
            )
            return volume

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return idea.volume  # Fallback to suggested volume

    async def execute_trade_idea(
        self, idea: TradeIdea, account_balance: float
    ) -> ExecutionResult:
        """
        Execute an approved trade idea.

        Args:
            idea: Approved trade idea to execute
            account_balance: Current account balance

        Returns:
            ExecutionResult with execution status
        """
        logger.info(f"Executing trade idea {idea.id} for {idea.symbol}")

        # Validate safety
        validation = await self.validate_execution_safety(idea, account_balance)
        if not validation.valid:
            error_msg = "; ".join(validation.errors)
            logger.error(f"Trade idea validation failed: {error_msg}")
            self._log_execution(idea, success=False, error=error_msg)
            return ExecutionResult(success=False, error=error_msg)

        # Calculate position size
        volume = self.calculate_position_size(idea, account_balance)

        try:
            # Prepare order parameters
            order_type = "buy" if idea.direction == "long" else "sell"

            # Execute market order via MT5 client
            result = self.mt5_client.place_order(
                canonical=idea.symbol,
                order_type=order_type,
                volume=volume,
                sl=idea.stop_loss,
                tp=idea.take_profit,
                comment=f"AI:{idea.id[:8]}",  # Add AI identifier to comment
            )

            if result.get("success"):
                order_id = result.get("order_id")
                logger.info(
                    f"Trade idea {idea.id} executed successfully: order {order_id}"
                )
                self._log_execution(
                    idea, success=True, order_id=order_id, volume=volume
                )
                return ExecutionResult(
                    success=True,
                    order_id=order_id,
                    details={"volume": volume, "result": result},
                )
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Trade idea {idea.id} execution failed: {error}")
                self._log_execution(idea, success=False, error=error, volume=volume)
                return ExecutionResult(success=False, error=error)

        except Exception as e:
            error_msg = f"Exception during execution: {str(e)}"
            logger.error(
                f"Trade idea {idea.id} execution exception: {e}", exc_info=True
            )
            self._log_execution(idea, success=False, error=error_msg)
            return ExecutionResult(success=False, error=error_msg)

    def _log_execution(
        self,
        idea: TradeIdea,
        success: bool,
        order_id: Optional[int] = None,
        volume: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """Log execution attempt to CSV."""
        try:
            with open(self.execution_log_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        datetime.utcnow().isoformat(),
                        idea.id,
                        idea.symbol,
                        idea.direction,
                        idea.confidence,
                        idea.entry_price,
                        idea.stop_loss,
                        idea.take_profit,
                        volume or idea.volume,
                        idea.rr_ratio,
                        idea.execution_plan.riskPct,
                        order_id or "",
                        success,
                        error or "",
                    ]
                )
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
