"""
Decision History API Routes for Phase 4: Audit Trail Visualization

Provides endpoints to retrieve AI evaluation history, trade ideas, and system decisions
from CSV/JSON files for frontend visualization.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/decision-history", tags=["decision-history"])


# ==================== RESPONSE MODELS ====================


class DecisionHistoryItem(BaseModel):
    """Single decision history item."""

    id: str
    timestamp: str
    symbol: str
    action: str
    confidence: int
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    rr_ratio: Optional[float] = None
    status: str
    source: str  # "ai_evaluation", "trade_idea", "health_check"
    notes: Optional[str] = None
    emnr_flags: Optional[Dict[str, bool]] = None
    indicators: Optional[Dict[str, Any]] = None


class DecisionHistoryResponse(BaseModel):
    """Response containing decision history items."""

    items: List[DecisionHistoryItem]
    total: int
    page: int
    page_size: int
    filters_applied: Dict[str, Any]


class DecisionStats(BaseModel):
    """Statistics about decision history."""

    total_decisions: int
    by_action: Dict[str, int]
    by_symbol: Dict[str, int]
    by_status: Dict[str, int]
    avg_confidence: float
    date_range: Dict[str, str]


# ==================== HELPER FUNCTIONS ====================


def _load_trade_ideas(
    date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Load trade ideas from data/trade_ideas/ directory.

    Args:
        date_from: Start date filter
        date_to: End date filter

    Returns:
        List of trade idea dictionaries
    """
    trade_ideas_dir = Path("data/trade_ideas")
    if not trade_ideas_dir.exists():
        return []

    trade_ideas = []

    for json_file in trade_ideas_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                idea = json.load(f)

            # Parse timestamp
            timestamp_str = idea.get("timestamp", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )

                    # Apply date filters
                    if date_from and timestamp < date_from:
                        continue
                    if date_to and timestamp > date_to:
                        continue
                except Exception:
                    pass

            trade_ideas.append(idea)

        except Exception as e:
            logger.error(f"Error loading trade idea from {json_file}: {e}")

    return trade_ideas


def _load_evaluations(
    date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Load AI evaluations from data/evaluations/ directory.

    Args:
        date_from: Start date filter
        date_to: End date filter

    Returns:
        List of evaluation dictionaries
    """
    evaluations_dir = Path("data/evaluations")
    if not evaluations_dir.exists():
        return []

    evaluations = []

    for json_file in evaluations_dir.glob("evaluation_*.json"):
        try:
            with open(json_file, "r") as f:
                eval_data = json.load(f)

            # Parse timestamp
            timestamp_str = eval_data.get("timestamp", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )

                    # Apply date filters
                    if date_from and timestamp < date_from:
                        continue
                    if date_to and timestamp > date_to:
                        continue
                except Exception:
                    pass

            # Extract evaluations array if present
            if "evaluations" in eval_data and isinstance(
                eval_data["evaluations"], list
            ):
                evaluations.extend(eval_data["evaluations"])
            else:
                evaluations.append(eval_data)

        except Exception as e:
            logger.error(f"Error loading evaluation from {json_file}: {e}")

    return evaluations


def _load_health_checks(
    date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Load health check results from data/health_checks/ directory.

    Args:
        date_from: Start date filter
        date_to: End date filter

    Returns:
        List of health check dictionaries
    """
    health_dir = Path("data/health_checks")
    if not health_dir.exists():
        return []

    health_checks = []

    for json_file in health_dir.glob("health_*.json"):
        try:
            with open(json_file, "r") as f:
                health_data = json.load(f)

            # Parse timestamp
            timestamp_str = health_data.get("timestamp", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )

                    # Apply date filters
                    if date_from and timestamp < date_from:
                        continue
                    if date_to and timestamp > date_to:
                        continue
                except Exception:
                    pass

            health_checks.append(health_data)

        except Exception as e:
            logger.error(f"Error loading health check from {json_file}: {e}")

    return health_checks


def _convert_to_decision_item(data: Dict[str, Any], source: str) -> DecisionHistoryItem:
    """
    Convert raw data to DecisionHistoryItem.

    Args:
        data: Raw data dictionary
        source: Source type ("trade_idea", "evaluation", "health_check")

    Returns:
        DecisionHistoryItem
    """
    return DecisionHistoryItem(
        id=data.get("id", data.get("task_id", f"{source}_{data.get('timestamp', '')}")),
        timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        symbol=data.get("symbol", "SYSTEM"),
        action=data.get("action", "observe"),
        confidence=int(data.get("confidence", 0)),
        direction=data.get("direction"),
        entry_price=data.get("entry_price"),
        stop_loss=data.get("stop_loss"),
        take_profit=data.get("take_profit"),
        rr_ratio=data.get("rr_ratio"),
        status=data.get("status", "completed"),
        source=source,
        notes=data.get("notes"),
        emnr_flags=data.get("emnr_flags"),
        indicators=data.get("indicators"),
    )


# ==================== API ENDPOINTS ====================


@router.get("/", response_model=DecisionHistoryResponse)
async def get_decision_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(
        None, description="Filter by source (trade_idea, evaluation, health_check)"
    ),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """
    Get decision history with filtering and pagination.

    Returns chronological list of AI evaluations, trade ideas, and system decisions.
    """
    try:
        # Parse date filters
        date_from_dt = None
        date_to_dt = None

        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid date_from format: {e}"
                )

        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid date_to format: {e}"
                )

        # Load data from all sources
        all_items: List[DecisionHistoryItem] = []

        if not source or source == "trade_idea":
            trade_ideas = _load_trade_ideas(date_from_dt, date_to_dt)
            all_items.extend(
                [_convert_to_decision_item(idea, "trade_idea") for idea in trade_ideas]
            )

        if not source or source == "evaluation":
            evaluations = _load_evaluations(date_from_dt, date_to_dt)
            all_items.extend(
                [
                    _convert_to_decision_item(eval_data, "evaluation")
                    for eval_data in evaluations
                ]
            )

        if not source or source == "health_check":
            health_checks = _load_health_checks(date_from_dt, date_to_dt)
            all_items.extend(
                [
                    _convert_to_decision_item(health, "health_check")
                    for health in health_checks
                ]
            )

        # Apply filters
        filtered_items = all_items

        if symbol:
            filtered_items = [item for item in filtered_items if item.symbol == symbol]

        if action:
            filtered_items = [item for item in filtered_items if item.action == action]

        if status:
            filtered_items = [item for item in filtered_items if item.status == status]

        # Sort by timestamp (newest first)
        filtered_items.sort(key=lambda x: x.timestamp, reverse=True)

        # Pagination
        total = len(filtered_items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered_items[start_idx:end_idx]

        return DecisionHistoryResponse(
            items=page_items,
            total=total,
            page=page,
            page_size=page_size,
            filters_applied={
                "symbol": symbol,
                "action": action,
                "status": status,
                "source": source,
                "date_from": date_from,
                "date_to": date_to,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving decision history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve decision history: {str(e)}"
        )


@router.get("/stats", response_model=DecisionStats)
async def get_decision_stats(
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
):
    """
    Get statistics about decision history.
    """
    try:
        # Parse date filters
        date_from_dt = None
        date_to_dt = None

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        if date_to:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))

        # Load all data
        trade_ideas = _load_trade_ideas(date_from_dt, date_to_dt)
        evaluations = _load_evaluations(date_from_dt, date_to_dt)
        health_checks = _load_health_checks(date_from_dt, date_to_dt)

        all_items = (
            [_convert_to_decision_item(idea, "trade_idea") for idea in trade_ideas]
            + [
                _convert_to_decision_item(eval_data, "evaluation")
                for eval_data in evaluations
            ]
            + [
                _convert_to_decision_item(health, "health_check")
                for health in health_checks
            ]
        )

        # Calculate statistics
        by_action: Dict[str, int] = {}
        by_symbol: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        total_confidence = 0

        for item in all_items:
            by_action[item.action] = by_action.get(item.action, 0) + 1
            by_symbol[item.symbol] = by_symbol.get(item.symbol, 0) + 1
            by_status[item.status] = by_status.get(item.status, 0) + 1
            total_confidence += item.confidence

        avg_confidence = total_confidence / len(all_items) if all_items else 0

        # Get date range
        timestamps = [item.timestamp for item in all_items]
        date_range = {
            "earliest": min(timestamps) if timestamps else "",
            "latest": max(timestamps) if timestamps else "",
        }

        return DecisionStats(
            total_decisions=len(all_items),
            by_action=by_action,
            by_symbol=by_symbol,
            by_status=by_status,
            avg_confidence=round(avg_confidence, 2),
            date_range=date_range,
        )

    except Exception as e:
        logger.error(f"Error calculating decision stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate stats: {str(e)}"
        )
