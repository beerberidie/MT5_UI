"""
FastAPI routes for Celery task management.

This module provides endpoints for:
- Triggering tasks manually
- Checking task status
- Viewing task results
- Managing scheduled tasks
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from backend.celery_app import celery_app
from backend.tasks import (
    evaluate_all_strategies,
    evaluate_single_symbol,
    backtest_strategy,
    collect_market_data,
    update_economic_calendar,
    collect_rss_news,
    update_symbol_info,
    cleanup_old_logs,
    cleanup_cache,
    archive_old_trades,
    system_health_check,
    optimize_csv_files,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/celery", tags=["celery"])


# Request models
class EvaluateSymbolRequest(BaseModel):
    symbol: str


class BacktestRequest(BaseModel):
    symbol: str
    strategy_name: str
    days: int = 30


class CleanupRequest(BaseModel):
    days_to_keep: int = 30


# Response models
class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ==================== AI Tasks ====================


@router.post("/tasks/ai/evaluate-all", response_model=TaskResponse)
async def trigger_evaluate_all_strategies():
    """
    Trigger AI strategy evaluation for all symbols.

    Returns:
        Task ID and status
    """
    try:
        task = evaluate_all_strategies.delay()

        return TaskResponse(
            task_id=task.id, status="pending", message="AI evaluation task started"
        )
    except Exception as e:
        logger.error(f"Error triggering AI evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/ai/evaluate-symbol", response_model=TaskResponse)
async def trigger_evaluate_symbol(request: EvaluateSymbolRequest):
    """
    Trigger AI strategy evaluation for a single symbol.

    Args:
        request: Symbol to evaluate

    Returns:
        Task ID and status
    """
    try:
        task = evaluate_single_symbol.delay(request.symbol)

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Symbol evaluation task started for {request.symbol}",
        )
    except Exception as e:
        logger.error(f"Error triggering symbol evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/ai/backtest", response_model=TaskResponse)
async def trigger_backtest(request: BacktestRequest):
    """
    Trigger strategy backtest.

    Args:
        request: Backtest parameters

    Returns:
        Task ID and status
    """
    try:
        task = backtest_strategy.delay(
            request.symbol, request.strategy_name, request.days
        )

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Backtest task started for {request.symbol}",
        )
    except Exception as e:
        logger.error(f"Error triggering backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Data Tasks ====================


@router.post("/tasks/data/collect-market-data", response_model=TaskResponse)
async def trigger_collect_market_data():
    """
    Trigger market data collection.

    Returns:
        Task ID and status
    """
    try:
        task = collect_market_data.delay()

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message="Market data collection task started",
        )
    except Exception as e:
        logger.error(f"Error triggering market data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/data/update-calendar", response_model=TaskResponse)
async def trigger_update_calendar():
    """
    Trigger economic calendar update.

    Returns:
        Task ID and status
    """
    try:
        task = update_economic_calendar.delay()

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message="Economic calendar update task started",
        )
    except Exception as e:
        logger.error(f"Error triggering calendar update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/data/collect-news", response_model=TaskResponse)
async def trigger_collect_news():
    """
    Trigger RSS news collection.

    Returns:
        Task ID and status
    """
    try:
        task = collect_rss_news.delay()

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message="RSS news collection task started",
        )
    except Exception as e:
        logger.error(f"Error triggering news collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/data/update-symbols", response_model=TaskResponse)
async def trigger_update_symbols():
    """
    Trigger symbol info update.

    Returns:
        Task ID and status
    """
    try:
        task = update_symbol_info.delay()

        return TaskResponse(
            task_id=task.id, status="pending", message="Symbol info update task started"
        )
    except Exception as e:
        logger.error(f"Error triggering symbol update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Maintenance Tasks ====================


@router.post("/tasks/maintenance/cleanup-logs", response_model=TaskResponse)
async def trigger_cleanup_logs(request: Optional[CleanupRequest] = None):
    """
    Trigger log cleanup.

    Args:
        request: Optional cleanup parameters

    Returns:
        Task ID and status
    """
    try:
        days = request.days_to_keep if request else 30
        task = cleanup_old_logs.delay(days)

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Log cleanup task started (keeping {days} days)",
        )
    except Exception as e:
        logger.error(f"Error triggering log cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/maintenance/cleanup-cache", response_model=TaskResponse)
async def trigger_cleanup_cache(request: Optional[CleanupRequest] = None):
    """
    Trigger cache cleanup.

    Args:
        request: Optional cleanup parameters

    Returns:
        Task ID and status
    """
    try:
        days = request.days_to_keep if request else 7
        task = cleanup_cache.delay(days)

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Cache cleanup task started (keeping {days} days)",
        )
    except Exception as e:
        logger.error(f"Error triggering cache cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/maintenance/archive-trades", response_model=TaskResponse)
async def trigger_archive_trades(request: Optional[CleanupRequest] = None):
    """
    Trigger trade log archival.

    Args:
        request: Optional archival parameters

    Returns:
        Task ID and status
    """
    try:
        days = request.days_to_keep if request else 90
        task = archive_old_trades.delay(days)

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Trade archival task started (keeping {days} days)",
        )
    except Exception as e:
        logger.error(f"Error triggering trade archival: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/maintenance/health-check", response_model=TaskResponse)
async def trigger_health_check():
    """
    Trigger system health check.

    Returns:
        Task ID and status
    """
    try:
        task = system_health_check.delay()

        return TaskResponse(
            task_id=task.id,
            status="pending",
            message="System health check task started",
        )
    except Exception as e:
        logger.error(f"Error triggering health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Task Status ====================


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a Celery task.

    Args:
        task_id: Task ID to check

    Returns:
        Task status and result
    """
    try:
        task_result = celery_app.AsyncResult(task_id)

        response = TaskStatusResponse(
            task_id=task_id, status=task_result.status.lower()
        )

        if task_result.ready():
            if task_result.successful():
                response.result = task_result.result
            else:
                response.error = str(task_result.info)

        return response

    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/active", response_model=Dict[str, Any])
async def get_active_tasks():
    """
    Get list of active tasks.

    Returns:
        List of active tasks
    """
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active = inspect.active()
        scheduled = inspect.scheduled()

        return {
            "active": active or {},
            "scheduled": scheduled or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/stats", response_model=Dict[str, Any])
async def get_task_stats():
    """
    Get Celery task statistics.

    Returns:
        Task statistics
    """
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        return {"stats": stats or {}, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Error getting task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
