"""
Strategy Management API Routes - CRUD operations for trading strategies.

This module provides REST API endpoints for managing trading strategies
stored as JSON files in the config/ai/strategies directory.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field

from backend.strategy_validator import (
    validate_and_prepare,
    validate_strategy,
    StrategyValidationError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

# Directory for strategy files
STRATEGIES_DIR = Path("config/ai/strategies")
STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)


# Pydantic Models

class StrategyBase(BaseModel):
    """Base strategy model."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    enabled: bool = Field(default=True)
    symbol: str = Field(..., pattern="^[A-Z0-9]+$")
    timeframe: str = Field(..., pattern="^(M1|M5|M15|M30|H1|H4|D1)$")
    sessions: List[str] = Field(..., min_items=1)
    indicators: Dict[str, Any]
    conditions: Dict[str, List[str]]
    strategy: Dict[str, Any]


class StrategyCreate(StrategyBase):
    """Model for creating a new strategy."""
    pass


class StrategyUpdate(BaseModel):
    """Model for updating an existing strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = None
    sessions: Optional[List[str]] = Field(None, min_items=1)
    indicators: Optional[Dict[str, Any]] = None
    conditions: Optional[Dict[str, List[str]]] = None
    strategy: Optional[Dict[str, Any]] = None


class StrategyResponse(StrategyBase):
    """Model for strategy response."""
    id: str
    created_at: str
    updated_at: str
    created_by: str


class StrategyListResponse(BaseModel):
    """Model for strategy list response."""
    items: List[StrategyResponse]
    total: int
    enabled_count: int
    disabled_count: int


class StrategyToggleRequest(BaseModel):
    """Model for enabling/disabling a strategy."""
    enabled: bool


class ValidationResponse(BaseModel):
    """Model for validation response."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)


# Helper Functions

def _get_strategy_path(strategy_id: str) -> Path:
    """Get file path for strategy by ID."""
    return STRATEGIES_DIR / f"{strategy_id}.json"


def _load_strategy(strategy_id: str) -> Optional[Dict[str, Any]]:
    """Load strategy from JSON file."""
    strategy_path = _get_strategy_path(strategy_id)
    
    if not strategy_path.exists():
        return None
    
    try:
        with open(strategy_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading strategy {strategy_id}: {e}")
        return None


def _save_strategy(strategy_id: str, data: Dict[str, Any]) -> bool:
    """Save strategy to JSON file."""
    strategy_path = _get_strategy_path(strategy_id)
    
    try:
        with open(strategy_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving strategy {strategy_id}: {e}")
        return False


def _delete_strategy_file(strategy_id: str) -> bool:
    """Delete strategy JSON file."""
    strategy_path = _get_strategy_path(strategy_id)
    
    try:
        if strategy_path.exists():
            strategy_path.unlink()
        return True
    except Exception as e:
        logger.error(f"Error deleting strategy {strategy_id}: {e}")
        return False


def _load_all_strategies() -> List[Dict[str, Any]]:
    """Load all strategies from directory."""
    strategies = []
    
    for strategy_file in STRATEGIES_DIR.glob("*.json"):
        try:
            with open(strategy_file, 'r', encoding='utf-8') as f:
                strategy = json.load(f)
                strategies.append(strategy)
        except Exception as e:
            logger.error(f"Error loading strategy from {strategy_file}: {e}")
    
    return strategies


# API Endpoints

@router.get("", response_model=StrategyListResponse)
async def list_strategies(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    """
    Get all strategies with optional filtering.
    
    Query Parameters:
        - enabled: Filter by enabled status (true/false)
        - symbol: Filter by symbol (e.g., EURUSD)
    
    Returns:
        List of strategies with counts
    """
    try:
        strategies = _load_all_strategies()
        
        # Apply filters
        if enabled is not None:
            strategies = [s for s in strategies if s.get('enabled') == enabled]
        
        if symbol:
            strategies = [s for s in strategies if s.get('symbol') == symbol.upper()]
        
        # Calculate counts
        all_strategies = _load_all_strategies()
        enabled_count = sum(1 for s in all_strategies if s.get('enabled', True))
        disabled_count = len(all_strategies) - enabled_count
        
        return StrategyListResponse(
            items=[StrategyResponse(**s) for s in strategies],
            total=len(strategies),
            enabled_count=enabled_count,
            disabled_count=disabled_count
        )
    
    except Exception as e:
        logger.error(f"Error listing strategies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: str):
    """
    Get a specific strategy by ID.
    
    Path Parameters:
        - strategy_id: Strategy identifier (e.g., EURUSD_H1)
    
    Returns:
        Strategy configuration
    """
    strategy = _load_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy not found: {strategy_id}"
        )
    
    return StrategyResponse(**strategy)


@router.post("", response_model=StrategyResponse, status_code=201)
async def create_strategy(strategy: StrategyCreate = Body(...)):
    """
    Create a new strategy.
    
    Request Body:
        Strategy configuration (see StrategyCreate model)
    
    Returns:
        Created strategy with metadata
    """
    try:
        # Convert to dict
        strategy_data = strategy.model_dump()
        
        # Validate and prepare
        is_valid, prepared_data, errors = validate_and_prepare(strategy_data, user="user")
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"message": "Validation failed", "errors": errors}
            )
        
        strategy_id = prepared_data['id']
        
        # Check if strategy already exists
        if _get_strategy_path(strategy_id).exists():
            raise HTTPException(
                status_code=409,
                detail=f"Strategy already exists: {strategy_id}"
            )
        
        # Save strategy
        if not _save_strategy(strategy_id, prepared_data):
            raise HTTPException(
                status_code=500,
                detail="Failed to save strategy"
            )
        
        logger.info(f"Created strategy: {strategy_id}")
        return StrategyResponse(**prepared_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    updates: StrategyUpdate = Body(...)
):
    """
    Update an existing strategy.
    
    Path Parameters:
        - strategy_id: Strategy identifier
    
    Request Body:
        Fields to update (see StrategyUpdate model)
    
    Returns:
        Updated strategy
    """
    try:
        # Load existing strategy
        existing = _load_strategy(strategy_id)
        
        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy not found: {strategy_id}"
            )
        
        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        existing.update(update_data)
        
        # Validate and prepare
        is_valid, prepared_data, errors = validate_and_prepare(existing, user="user")
        
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"message": "Validation failed", "errors": errors}
            )
        
        # Save updated strategy
        if not _save_strategy(strategy_id, prepared_data):
            raise HTTPException(
                status_code=500,
                detail="Failed to save strategy"
            )
        
        logger.info(f"Updated strategy: {strategy_id}")
        return StrategyResponse(**prepared_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(strategy_id: str):
    """
    Delete a strategy.

    Path Parameters:
        - strategy_id: Strategy identifier

    Returns:
        204 No Content on success
    """
    try:
        # Check if strategy exists
        if not _get_strategy_path(strategy_id).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Strategy not found: {strategy_id}"
            )

        # Delete strategy file
        if not _delete_strategy_file(strategy_id):
            raise HTTPException(
                status_code=500,
                detail="Failed to delete strategy"
            )

        logger.info(f"Deleted strategy: {strategy_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{strategy_id}/toggle", response_model=StrategyResponse)
async def toggle_strategy(
    strategy_id: str,
    request: StrategyToggleRequest = Body(...)
):
    """
    Enable or disable a strategy.

    Path Parameters:
        - strategy_id: Strategy identifier

    Request Body:
        - enabled: true to enable, false to disable

    Returns:
        Updated strategy
    """
    try:
        # Load existing strategy
        existing = _load_strategy(strategy_id)

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy not found: {strategy_id}"
            )

        # Update enabled status
        existing['enabled'] = request.enabled
        existing['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        # Save updated strategy
        if not _save_strategy(strategy_id, existing):
            raise HTTPException(
                status_code=500,
                detail="Failed to save strategy"
            )

        status = "enabled" if request.enabled else "disabled"
        logger.info(f"Strategy {strategy_id} {status}")
        return StrategyResponse(**existing)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidationResponse)
async def validate_strategy_endpoint(strategy_data: Dict[str, Any] = Body(...)):
    """
    Validate a strategy without saving it.

    Request Body:
        Strategy configuration to validate

    Returns:
        Validation result with errors if any
    """
    try:
        is_valid, errors = validate_strategy(strategy_data)

        return ValidationResponse(
            is_valid=is_valid,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Error validating strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/duplicate", response_model=StrategyResponse, status_code=201)
async def duplicate_strategy(
    strategy_id: str,
    new_name: str = Body(..., embed=True)
):
    """
    Duplicate an existing strategy with a new name.

    Path Parameters:
        - strategy_id: Strategy identifier to duplicate

    Request Body:
        - new_name: Name for the duplicated strategy

    Returns:
        Duplicated strategy
    """
    try:
        # Load existing strategy
        existing = _load_strategy(strategy_id)

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy not found: {strategy_id}"
            )

        # Create duplicate with new name
        duplicate = existing.copy()
        duplicate['name'] = new_name
        duplicate['description'] = f"Duplicate of {existing.get('name', strategy_id)}"

        # Remove metadata to generate new ones
        duplicate.pop('id', None)
        duplicate.pop('created_at', None)
        duplicate.pop('updated_at', None)
        duplicate.pop('created_by', None)

        # Validate and prepare
        is_valid, prepared_data, errors = validate_and_prepare(duplicate, user="user")

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={"message": "Validation failed", "errors": errors}
            )

        new_strategy_id = prepared_data['id']

        # Check if new strategy already exists
        if _get_strategy_path(new_strategy_id).exists():
            raise HTTPException(
                status_code=409,
                detail=f"Strategy already exists: {new_strategy_id}"
            )

        # Save duplicated strategy
        if not _save_strategy(new_strategy_id, prepared_data):
            raise HTTPException(
                status_code=500,
                detail="Failed to save duplicated strategy"
            )

        logger.info(f"Duplicated strategy {strategy_id} to {new_strategy_id}")
        return StrategyResponse(**prepared_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error duplicating strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

