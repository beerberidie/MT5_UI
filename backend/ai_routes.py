"""
AI Trading Routes - FastAPI endpoints for AI trading operations.

Provides REST API endpoints for:
- Manual evaluation triggers
- AI status monitoring
- Enable/disable AI for symbols
- Emergency kill switch
- Decision history
- Strategy management
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import json
from pathlib import Path

from backend.models import (
    EvaluateRequest,
    EvaluateResponse,
    AIStatusResponse,
    EnableAIRequest,
    KillSwitchRequest,
    TradeIdea
)
from backend.ai.engine import AIEngine
from backend.ai.ai_logger import get_decisions, get_decision_stats
from backend.ai.rules_manager import load_rules, save_rules, create_default_rules
from backend.mt5_client import MT5Client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ai", tags=["AI Trading"])

# Global state (in production, use proper state management)
_ai_engine: Optional[AIEngine] = None
_enabled_symbols: Dict[str, Dict] = {}  # {symbol: {timeframe, auto_execute}}
_active_trade_ideas: List[TradeIdea] = []


def get_ai_engine() -> AIEngine:
    """Dependency to get AI engine instance."""
    global _ai_engine
    if _ai_engine is None:
        # Initialize MT5Client and AIEngine
        mt5_client = MT5Client()
        _ai_engine = AIEngine(mt5_client)
    return _ai_engine


@router.post("/evaluate/{symbol}", response_model=EvaluateResponse)
async def evaluate_symbol(
    symbol: str,
    request: EvaluateRequest,
    engine: AIEngine = Depends(get_ai_engine)
):
    """
    Manually trigger AI evaluation for a symbol.
    
    Args:
        symbol: Trading symbol (e.g., "EURUSD")
        request: Evaluation request with timeframe and force flag
        
    Returns:
        EvaluateResponse with trade idea and confidence
    """
    try:
        logger.info(f"Manual evaluation requested for {symbol} {request.timeframe}")
        
        # Evaluate symbol
        trade_idea = engine.evaluate(
            symbol=symbol,
            timeframe=request.timeframe,
            force=request.force
        )
        
        if trade_idea:
            # Add to active trade ideas
            _active_trade_ideas.append(trade_idea)
            
            return EvaluateResponse(
                trade_idea=trade_idea,
                confidence=trade_idea.confidence,
                action=trade_idea.execution_plan.action,
                message=f"Trade idea generated with {trade_idea.confidence}% confidence"
            )
        else:
            return EvaluateResponse(
                trade_idea=None,
                confidence=0,
                action="observe",
                message="No trade idea generated - conditions not met"
            )
            
    except Exception as e:
        logger.error(f"Error evaluating {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status(engine: AIEngine = Depends(get_ai_engine)):
    """
    Get current AI engine status.
    
    Returns:
        AIStatusResponse with enabled status, mode, and active symbols
    """
    try:
        return AIStatusResponse(
            enabled=engine.settings.get("enabled", True),
            mode=engine.settings.get("mode", "semi-auto"),
            enabled_symbols=list(_enabled_symbols.keys()),
            active_trade_ideas=len(_active_trade_ideas),
            autonomy_loop_running=False  # TODO: Implement autonomy loop
        )
    except Exception as e:
        logger.error(f"Error getting AI status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable/{symbol}")
async def enable_ai_for_symbol(
    symbol: str,
    request: EnableAIRequest,
    engine: AIEngine = Depends(get_ai_engine)
):
    """
    Enable AI trading for a specific symbol.
    
    Args:
        symbol: Trading symbol to enable
        request: Configuration for AI (timeframe, auto_execute)
        
    Returns:
        Success message
    """
    try:
        _enabled_symbols[symbol] = {
            "timeframe": request.timeframe,
            "auto_execute": request.auto_execute,
            "enabled_at": datetime.now().isoformat()
        }
        
        logger.info(f"AI enabled for {symbol} on {request.timeframe} (auto_execute={request.auto_execute})")
        
        return {
            "success": True,
            "message": f"AI enabled for {symbol}",
            "config": _enabled_symbols[symbol]
        }
    except Exception as e:
        logger.error(f"Error enabling AI for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable/{symbol}")
async def disable_ai_for_symbol(symbol: str):
    """
    Disable AI trading for a specific symbol.
    
    Args:
        symbol: Trading symbol to disable
        
    Returns:
        Success message
    """
    try:
        if symbol in _enabled_symbols:
            del _enabled_symbols[symbol]
            logger.info(f"AI disabled for {symbol}")
            return {"success": True, "message": f"AI disabled for {symbol}"}
        else:
            raise HTTPException(status_code=404, detail=f"AI not enabled for {symbol}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling AI for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kill-switch")
async def emergency_kill_switch(
    request: KillSwitchRequest,
    engine: AIEngine = Depends(get_ai_engine)
):
    """
    Emergency kill switch - immediately disable all AI trading.
    
    Args:
        request: Kill switch request with reason
        
    Returns:
        Success message
    """
    try:
        # Disable AI globally
        engine.settings["enabled"] = False
        
        # Clear all enabled symbols
        _enabled_symbols.clear()
        
        # Clear active trade ideas
        _active_trade_ideas.clear()
        
        logger.warning(f"EMERGENCY KILL SWITCH ACTIVATED: {request.reason}")
        
        return {
            "success": True,
            "message": "AI trading disabled globally",
            "reason": request.reason,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error activating kill switch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions")
async def get_recent_decisions(
    symbol: Optional[str] = None,
    limit: int = 50,
    engine: AIEngine = Depends(get_ai_engine)
):
    """
    Get recent AI decisions from logs.
    
    Args:
        symbol: Filter by symbol (optional)
        limit: Maximum number of decisions to return
        
    Returns:
        List of recent decisions
    """
    try:
        if symbol:
            log_path = engine.data_dir / "indicators" / f"{symbol}_decisions.csv"
            decisions = get_decisions(str(log_path), symbol, limit)
        else:
            # Get decisions from all symbols
            decisions = []
            for log_file in (engine.data_dir / "indicators").glob("*_decisions.csv"):
                sym = log_file.stem.replace("_decisions", "")
                decisions.extend(get_decisions(str(log_file), sym, limit))
            
            # Sort by timestamp and limit
            decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            decisions = decisions[:limit]
        
        return {
            "success": True,
            "count": len(decisions),
            "decisions": decisions
        }
    except Exception as e:
        logger.error(f"Error getting decisions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
async def list_strategies(engine: AIEngine = Depends(get_ai_engine)):
    """
    List all available AI strategies.
    
    Returns:
        List of strategy files
    """
    try:
        strategies_dir = engine.config_dir / "strategies"
        strategies = []
        
        for strategy_file in strategies_dir.glob("*.json"):
            with open(strategy_file, 'r') as f:
                strategy = json.load(f)
                strategies.append({
                    "file": strategy_file.name,
                    "symbol": strategy.get("symbol"),
                    "timeframe": strategy.get("timeframe"),
                    "direction": strategy.get("strategy", {}).get("direction")
                })
        
        return {
            "success": True,
            "count": len(strategies),
            "strategies": strategies
        }
    except Exception as e:
        logger.error(f"Error listing strategies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{symbol}")
async def get_strategy(
    symbol: str,
    timeframe: str = "H1",
    engine: AIEngine = Depends(get_ai_engine)
):
    """
    Get strategy configuration for a symbol.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe for strategy
        
    Returns:
        Strategy configuration
    """
    try:
        rules = load_rules(
            str(engine.config_dir / "strategies"),
            symbol,
            timeframe
        )
        
        if rules:
            return {
                "success": True,
                "strategy": rules.__dict__
            }
        else:
            raise HTTPException(status_code=404, detail=f"No strategy found for {symbol} {timeframe}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategies/{symbol}")
async def save_strategy(
    symbol: str,
    strategy: Dict,
    engine: AIEngine = Depends(get_ai_engine)
):
    """
    Save or update strategy configuration for a symbol.
    
    Args:
        symbol: Trading symbol
        strategy: Strategy configuration
        
    Returns:
        Success message
    """
    try:
        # TODO: Validate strategy structure
        timeframe = strategy.get("timeframe", "H1")
        
        # Save strategy
        success = save_rules(
            str(engine.config_dir / "strategies"),
            symbol,
            strategy
        )
        
        if success:
            return {
                "success": True,
                "message": f"Strategy saved for {symbol} {timeframe}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save strategy")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving strategy for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

