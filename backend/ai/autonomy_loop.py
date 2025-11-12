"""
AI Autonomy Loop - Background task scheduler for automated AI evaluation.

This module provides:
- Background scheduler using APScheduler
- Periodic evaluation of enabled symbols
- Trade idea generation and storage
- Automatic execution in full-auto mode
- Manual approval workflow in semi-auto mode
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

logger = logging.getLogger(__name__)


class AutonomyLoop:
    """
    Background scheduler for automated AI trading evaluation.

    Features:
    - Periodic evaluation of enabled symbols
    - Configurable evaluation interval (default: 15 minutes)
    - Start/stop control
    - Status monitoring
    - Integration with AI engine and executor
    """

    def __init__(
        self,
        evaluation_callback: Callable[[str], Dict],
        enabled_symbols_callback: Callable[[], Dict[str, bool]],
        timezone: str = "Africa/Johannesburg",
    ):
        """
        Initialize Autonomy Loop.

        Args:
            evaluation_callback: Function to call for symbol evaluation (symbol -> trade_idea)
            enabled_symbols_callback: Function to get enabled symbols dict
            timezone: Timezone for scheduler (default: Africa/Johannesburg)
        """
        self.evaluation_callback = evaluation_callback
        self.enabled_symbols_callback = enabled_symbols_callback
        self.timezone = pytz.timezone(timezone)

        # Initialize scheduler
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.is_running = False
        self.evaluation_interval_minutes = 15
        self.last_evaluation_time = None
        self.evaluation_count = 0
        self.error_count = 0

        logger.info("Autonomy Loop initialized")

    def start(self, interval_minutes: int = 15) -> Dict[str, any]:
        """
        Start the autonomy loop with specified interval.

        Args:
            interval_minutes: Evaluation interval in minutes (default: 15)

        Returns:
            Status dictionary with success/error information
        """
        if self.is_running:
            return {
                "success": False,
                "message": "Autonomy loop is already running",
                "status": self.get_status(),
            }

        try:
            self.evaluation_interval_minutes = interval_minutes

            # Add periodic job
            self.scheduler.add_job(
                func=self._evaluate_all_symbols,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id="ai_evaluation",
                name="AI Symbol Evaluation",
                replace_existing=True,
            )

            # Start scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info(
                f"Autonomy loop started with {interval_minutes} minute interval"
            )

            return {
                "success": True,
                "message": f"Autonomy loop started with {interval_minutes} minute interval",
                "status": self.get_status(),
            }

        except Exception as e:
            logger.error(f"Error starting autonomy loop: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error starting autonomy loop: {str(e)}",
                "status": self.get_status(),
            }

    def stop(self) -> Dict[str, any]:
        """
        Stop the autonomy loop.

        Returns:
            Status dictionary with success/error information
        """
        if not self.is_running:
            return {
                "success": False,
                "message": "Autonomy loop is not running",
                "status": self.get_status(),
            }

        try:
            # Remove job and shutdown scheduler
            self.scheduler.remove_job("ai_evaluation")
            self.scheduler.shutdown(wait=False)
            self.is_running = False

            logger.info("Autonomy loop stopped")

            return {
                "success": True,
                "message": "Autonomy loop stopped",
                "status": self.get_status(),
            }

        except Exception as e:
            logger.error(f"Error stopping autonomy loop: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error stopping autonomy loop: {str(e)}",
                "status": self.get_status(),
            }

    def get_status(self) -> Dict[str, any]:
        """
        Get current status of autonomy loop.

        Returns:
            Status dictionary with running state, interval, stats
        """
        enabled_symbols = self.enabled_symbols_callback()

        return {
            "running": self.is_running,
            "interval_minutes": self.evaluation_interval_minutes,
            "enabled_symbols_count": len(enabled_symbols),
            "enabled_symbols": list(enabled_symbols.keys()),
            "last_evaluation_time": (
                self.last_evaluation_time.isoformat()
                if self.last_evaluation_time
                else None
            ),
            "evaluation_count": self.evaluation_count,
            "error_count": self.error_count,
            "next_run_time": self._get_next_run_time(),
        }

    def _get_next_run_time(self) -> Optional[str]:
        """Get next scheduled run time."""
        if not self.is_running:
            return None

        try:
            job = self.scheduler.get_job("ai_evaluation")
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
        except Exception:
            pass

        return None

    def _evaluate_all_symbols(self):
        """
        Evaluate all enabled symbols (called by scheduler).

        This is the main periodic task that:
        1. Gets list of enabled symbols
        2. Evaluates each symbol using the evaluation callback
        3. Stores trade ideas for approval/execution
        4. Logs results
        """
        try:
            self.last_evaluation_time = datetime.now(self.timezone)
            enabled_symbols = self.enabled_symbols_callback()

            if not enabled_symbols:
                logger.info("No enabled symbols for evaluation")
                return

            logger.info(
                f"Starting autonomy loop evaluation for {len(enabled_symbols)} symbols"
            )

            success_count = 0
            error_count = 0

            for symbol in enabled_symbols.keys():
                try:
                    # Call evaluation callback (from ai_routes)
                    result = self.evaluation_callback(symbol)

                    if result.get("success"):
                        success_count += 1
                        trade_idea = result.get("trade_idea")
                        if trade_idea:
                            logger.info(
                                f"Generated trade idea for {symbol}: "
                                f"confidence={trade_idea.get('confidence', 0)}%, "
                                f"action={trade_idea.get('action', 'unknown')}"
                            )
                    else:
                        error_count += 1
                        logger.warning(
                            f"Evaluation failed for {symbol}: {result.get('message', 'Unknown error')}"
                        )

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error evaluating {symbol}: {e}", exc_info=True)

            self.evaluation_count += 1
            self.error_count += error_count

            logger.info(
                f"Autonomy loop evaluation complete: "
                f"{success_count} successful, {error_count} errors"
            )

        except Exception as e:
            logger.error(f"Error in autonomy loop evaluation: {e}", exc_info=True)
            self.error_count += 1

    def evaluate_now(self) -> Dict[str, any]:
        """
        Trigger immediate evaluation (manual trigger).

        Returns:
            Status dictionary with evaluation results
        """
        try:
            logger.info("Manual evaluation triggered")
            self._evaluate_all_symbols()

            return {
                "success": True,
                "message": "Manual evaluation completed",
                "status": self.get_status(),
            }

        except Exception as e:
            logger.error(f"Error in manual evaluation: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error in manual evaluation: {str(e)}",
                "status": self.get_status(),
            }


# Global instance (initialized in ai_routes.py)
_autonomy_loop: Optional[AutonomyLoop] = None


def get_autonomy_loop() -> Optional[AutonomyLoop]:
    """Get global autonomy loop instance."""
    return _autonomy_loop


def set_autonomy_loop(loop: AutonomyLoop):
    """Set global autonomy loop instance."""
    global _autonomy_loop
    _autonomy_loop = loop
