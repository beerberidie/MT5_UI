"""
AI-related background tasks for Celery.

This module contains tasks for:
- Periodic AI strategy evaluation
- Trade idea generation
- Symbol analysis
- Performance tracking
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import json
from pathlib import Path

from backend.celery_app import celery_app
from backend.storage.file_storage import FileStorage
from backend.ai.engine import AIEngine
from backend.mt5_client import MT5Client

logger = logging.getLogger(__name__)


@celery_app.task(name="backend.tasks.ai_tasks.evaluate_all_strategies", bind=True)
def evaluate_all_strategies(self):
    """
    Evaluate all enabled AI strategies for all enabled symbols.

    This task:
    1. Gets list of enabled symbols from watchlist
    2. Loads AI strategies for each symbol
    3. Evaluates each strategy using current market data
    4. Generates trade ideas
    5. Stores results in CSV files

    Returns:
        Dict with evaluation results and statistics
    """
    try:
        logger.info("Starting AI strategy evaluation task")

        # Initialize storage and AI engine
        storage = FileStorage()
        mt5_client = MT5Client()
        ai_engine = AIEngine(mt5_client)

        # Get enabled symbols from watchlist
        # For now, use a default list - can be enhanced to read from config
        enabled_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]

        results = {
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols_evaluated": 0,
            "trade_ideas_generated": 0,
            "errors": [],
            "evaluations": [],
        }

        # Evaluate each symbol
        for symbol in enabled_symbols:
            try:
                logger.info(f"Evaluating {symbol}")

                # Initialize MT5 connection
                try:
                    mt5_client.init()
                except Exception as e:
                    logger.error(f"Failed to initialize MT5: {e}")
                    results["errors"].append(f"{symbol}: MT5 initialization failed")
                    continue

                # Evaluate symbol using AI engine
                evaluation = ai_engine.evaluate(symbol)

                if evaluation:
                    results["symbols_evaluated"] += 1

                    # Store trade idea if generated
                    _store_trade_idea(storage, symbol, evaluation)
                    results["trade_ideas_generated"] += 1

                    results["evaluations"].append(
                        {
                            "symbol": symbol,
                            "confidence": getattr(evaluation, "confidence", 0),
                            "action": getattr(evaluation, "action", "observe"),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                else:
                    logger.info(f"No trade idea generated for {symbol}")

            except Exception as e:
                logger.error(f"Error evaluating {symbol}: {e}", exc_info=True)
                results["errors"].append(f"{symbol}: {str(e)}")

        # Shutdown MT5
        mt5_client.shutdown()

        # Store evaluation results
        _store_evaluation_results(storage, results)

        logger.info(
            f"AI evaluation complete: {results['symbols_evaluated']} symbols, "
            f"{results['trade_ideas_generated']} trade ideas"
        )

        return results

    except Exception as e:
        logger.error(f"Error in evaluate_all_strategies task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.ai_tasks.evaluate_single_symbol", bind=True)
def evaluate_single_symbol(self, symbol: str):
    """
    Evaluate a single symbol on-demand.

    Args:
        symbol: Symbol to evaluate (e.g., "EURUSD")

    Returns:
        Dict with evaluation results
    """
    try:
        logger.info(f"Evaluating single symbol: {symbol}")

        # Initialize components
        storage = FileStorage()
        mt5_client = MT5Client()
        ai_engine = AIEngine(mt5_client)

        # Initialize MT5
        try:
            mt5_client.init()
        except Exception as e:
            return {
                "success": False,
                "error": f"MT5 initialization failed: {str(e)}",
                "symbol": symbol,
            }

        # Evaluate symbol
        evaluation = ai_engine.evaluate(symbol)

        # Shutdown MT5
        mt5_client.shutdown()

        # Store trade idea if generated
        if evaluation:
            _store_trade_idea(storage, symbol, evaluation)

        return {
            "success": True,
            "symbol": symbol,
            "evaluation": evaluation.__dict__ if evaluation else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error evaluating {symbol}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "symbol": symbol}


@celery_app.task(name="backend.tasks.ai_tasks.backtest_strategy", bind=True)
def backtest_strategy(self, symbol: str, strategy_name: str, days: int = 30):
    """
    Backtest a strategy on historical data.

    Args:
        symbol: Symbol to backtest
        strategy_name: Name of strategy to test
        days: Number of days of historical data

    Returns:
        Dict with backtest results
    """
    try:
        logger.info(f"Backtesting {strategy_name} on {symbol} for {days} days")

        # Initialize components
        mt5_client = MT5Client()

        # Initialize MT5
        try:
            mt5_client.init()
        except Exception as e:
            return {"success": False, "error": f"MT5 initialization failed: {str(e)}"}

        # Get historical data
        # This is a placeholder - actual backtest logic would go here

        mt5_client.shutdown()

        return {
            "success": True,
            "symbol": symbol,
            "strategy": strategy_name,
            "days": days,
            "message": "Backtest functionality coming soon",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in backtest: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# Helper functions


def _store_trade_idea(storage: FileStorage, symbol: str, trade_idea: Any):
    """
    Store trade idea in JSON file.

    Args:
        storage: FileStorage instance
        symbol: Symbol for the trade idea
        trade_idea: TradeIdea object or dict
    """
    try:
        # Create trade ideas directory if not exists
        ideas_dir = Path("data/trade_ideas")
        ideas_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = ideas_dir / f"{symbol}_{timestamp}.json"

        # Convert TradeIdea object to dict if needed
        if hasattr(trade_idea, "__dict__"):
            trade_idea_dict = trade_idea.__dict__
        elif isinstance(trade_idea, dict):
            trade_idea_dict = trade_idea
        else:
            trade_idea_dict = {"data": str(trade_idea)}

        # Add metadata
        trade_idea_with_meta = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "celery_task",
            **trade_idea_dict,
        }

        # Write to file
        with open(filename, "w") as f:
            json.dump(trade_idea_with_meta, f, indent=2, default=str)

        logger.info(f"Stored trade idea: {filename}")

    except Exception as e:
        logger.error(f"Error storing trade idea: {e}", exc_info=True)


def _store_evaluation_results(storage: FileStorage, results: Dict[str, Any]):
    """
    Store evaluation results in CSV file.

    Args:
        storage: FileStorage instance
        results: Evaluation results
    """
    try:
        # Create evaluations directory if not exists
        eval_dir = Path("data/evaluations")
        eval_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with date
        date_str = datetime.utcnow().strftime("%Y%m%d")
        filename = eval_dir / f"evaluation_{date_str}.json"

        # Append to daily file (or create new)
        daily_results = []
        if filename.exists():
            with open(filename, "r") as f:
                daily_results = json.load(f)

        daily_results.append(results)

        # Write back
        with open(filename, "w") as f:
            json.dump(daily_results, f, indent=2)

        logger.info(f"Stored evaluation results: {filename}")

    except Exception as e:
        logger.error(f"Error storing evaluation results: {e}", exc_info=True)
