"""
Strategy Validator - Validates trading strategy JSON against schema.

This module provides validation for trading strategies to ensure they meet
the required schema and business rules before being saved.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

# Load strategy schema
SCHEMA_PATH = Path(__file__).parent / "strategy_schema.json"
with open(SCHEMA_PATH, 'r') as f:
    STRATEGY_SCHEMA = json.load(f)


class StrategyValidationError(Exception):
    """Custom exception for strategy validation errors."""
    
    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


def validate_strategy(strategy_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate strategy data against JSON schema and business rules.
    
    Args:
        strategy_data: Strategy configuration dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
        
    Example:
        >>> strategy = {"name": "Test", "symbol": "EURUSD", ...}
        >>> is_valid, errors = validate_strategy(strategy)
        >>> if not is_valid:
        ...     print(f"Validation failed: {errors}")
    """
    errors = []
    
    # 1. Validate against JSON schema
    try:
        validate(instance=strategy_data, schema=STRATEGY_SCHEMA)
    except ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        return False, errors
    
    # 2. Business rule validations
    
    # Check EMA fast < slow
    if 'indicators' in strategy_data and 'ema' in strategy_data['indicators']:
        ema = strategy_data['indicators']['ema']
        if ema.get('fast', 0) >= ema.get('slow', 0):
            errors.append("EMA fast period must be less than slow period")
    
    # Check MACD fast < slow
    if 'indicators' in strategy_data and 'macd' in strategy_data['indicators']:
        macd = strategy_data['indicators']['macd']
        if macd.get('fast', 0) >= macd.get('slow', 0):
            errors.append("MACD fast period must be less than slow period")
    
    # Check RSI overbought > oversold
    if 'indicators' in strategy_data and 'rsi' in strategy_data['indicators']:
        rsi = strategy_data['indicators']['rsi']
        if rsi.get('overbought', 100) <= rsi.get('oversold', 0):
            errors.append("RSI overbought must be greater than oversold")
    
    # Check at least one entry condition
    if 'conditions' in strategy_data:
        conditions = strategy_data['conditions']
        if not conditions.get('entry') or len(conditions['entry']) == 0:
            errors.append("At least one entry condition is required")
    
    # Check symbol format (uppercase alphanumeric)
    if 'symbol' in strategy_data:
        symbol = strategy_data['symbol']
        if not symbol.isupper() or not symbol.isalnum():
            errors.append("Symbol must be uppercase alphanumeric (e.g., EURUSD, XAUUSD)")
    
    # Check min_rr is reasonable
    if 'strategy' in strategy_data:
        min_rr = strategy_data['strategy'].get('min_rr', 2.0)
        if min_rr < 1.0:
            errors.append("Minimum R:R ratio must be at least 1.0")
        if min_rr > 10.0:
            errors.append("Minimum R:R ratio should not exceed 10.0")
    
    # Check max_risk_pct is reasonable
    if 'strategy' in strategy_data:
        max_risk = strategy_data['strategy'].get('max_risk_pct', 0.01)
        if max_risk < 0.001:
            errors.append("Maximum risk percentage must be at least 0.1%")
        if max_risk > 0.1:
            errors.append("Maximum risk percentage should not exceed 10%")
    
    return len(errors) == 0, errors


def validate_condition_syntax(condition: str) -> Tuple[bool, Optional[str]]:
    """
    Validate condition string syntax.
    
    Args:
        condition: Condition string (e.g., "ema_fast_gt_slow")
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> is_valid, error = validate_condition_syntax("ema_fast_gt_slow")
        >>> is_valid
        True
    """
    # List of known valid condition patterns
    valid_patterns = [
        # EMA conditions
        "ema_fast_gt_slow", "ema_fast_lt_slow",
        "price_above_ema_fast", "price_below_ema_fast",
        "price_above_ema_slow", "price_below_ema_slow",
        "price_close_gt_ema_slow", "price_close_lt_ema_slow",
        
        # RSI conditions
        "rsi_gt_70", "rsi_lt_30",
        "rsi_between_40_60", "rsi_between_30_70",
        "rsi_overbought", "rsi_oversold",
        
        # MACD conditions
        "macd_hist_gt_0", "macd_hist_lt_0",
        "macd_line_gt_signal", "macd_line_lt_signal",
        "macd_bullish_cross", "macd_bearish_cross",
        
        # ATR conditions
        "atr_above_median", "atr_below_median",
        "atr_expanding", "atr_contracting",
        
        # Price action conditions
        "long_upper_wick", "long_lower_wick",
        "bullish_engulfing", "bearish_engulfing",
        "doji", "hammer", "shooting_star",
        
        # Divergence conditions
        "divergence_bullish", "divergence_bearish",
        
        # Trend conditions
        "uptrend", "downtrend", "sideways",
        
        # Volume conditions (if available)
        "volume_above_average", "volume_below_average"
    ]
    
    if condition in valid_patterns:
        return True, None
    
    # Check if it's a custom condition (allow alphanumeric + underscores)
    if condition.replace('_', '').isalnum():
        logger.warning(f"Unknown condition '{condition}' - may not be recognized by EMNR evaluator")
        return True, None  # Allow but warn
    
    return False, f"Invalid condition syntax: '{condition}'"


def validate_all_conditions(strategy_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate all condition strings in strategy.
    
    Args:
        strategy_data: Strategy configuration dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if 'conditions' not in strategy_data:
        return True, []
    
    conditions = strategy_data['conditions']
    
    # Validate entry conditions
    for condition in conditions.get('entry', []):
        is_valid, error = validate_condition_syntax(condition)
        if not is_valid:
            errors.append(f"Entry condition error: {error}")
    
    # Validate exit conditions
    for condition in conditions.get('exit', []):
        is_valid, error = validate_condition_syntax(condition)
        if not is_valid:
            errors.append(f"Exit condition error: {error}")
    
    # Validate strong conditions
    for condition in conditions.get('strong', []):
        is_valid, error = validate_condition_syntax(condition)
        if not is_valid:
            errors.append(f"Strong condition error: {error}")
    
    # Validate weak conditions
    for condition in conditions.get('weak', []):
        is_valid, error = validate_condition_syntax(condition)
        if not is_valid:
            errors.append(f"Weak condition error: {error}")
    
    # Validate invalidations
    if 'strategy' in strategy_data:
        for condition in strategy_data['strategy'].get('invalidations', []):
            is_valid, error = validate_condition_syntax(condition)
            if not is_valid:
                errors.append(f"Invalidation condition error: {error}")
    
    return len(errors) == 0, errors


def add_metadata(strategy_data: Dict[str, Any], user: str = "user") -> Dict[str, Any]:
    """
    Add metadata fields to strategy (id, timestamps, user).
    
    Args:
        strategy_data: Strategy configuration dictionary
        user: Username creating/updating the strategy
        
    Returns:
        Strategy data with metadata added
    """
    now = datetime.utcnow().isoformat() + 'Z'
    
    # Generate ID if not present
    if 'id' not in strategy_data:
        symbol = strategy_data.get('symbol', 'UNKNOWN')
        timeframe = strategy_data.get('timeframe', 'H1')
        strategy_data['id'] = f"{symbol}_{timeframe}"
    
    # Add timestamps
    if 'created_at' not in strategy_data:
        strategy_data['created_at'] = now
    strategy_data['updated_at'] = now
    
    # Add user
    if 'created_by' not in strategy_data:
        strategy_data['created_by'] = user
    
    # Add enabled flag if not present
    if 'enabled' not in strategy_data:
        strategy_data['enabled'] = True
    
    return strategy_data


def sanitize_strategy(strategy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize strategy data by removing invalid fields and normalizing values.
    
    Args:
        strategy_data: Strategy configuration dictionary
        
    Returns:
        Sanitized strategy data
    """
    # Create a copy to avoid modifying original
    sanitized = strategy_data.copy()
    
    # Normalize symbol to uppercase
    if 'symbol' in sanitized:
        sanitized['symbol'] = sanitized['symbol'].upper()
    
    # Ensure sessions are unique
    if 'sessions' in sanitized:
        sanitized['sessions'] = list(set(sanitized['sessions']))
    
    # Remove empty condition arrays
    if 'conditions' in sanitized:
        conditions = sanitized['conditions']
        for key in ['entry', 'exit', 'strong', 'weak']:
            if key in conditions and not conditions[key]:
                if key != 'entry':  # entry is required
                    del conditions[key]
    
    # Remove empty invalidations
    if 'strategy' in sanitized and 'invalidations' in sanitized['strategy']:
        if not sanitized['strategy']['invalidations']:
            del sanitized['strategy']['invalidations']
    
    return sanitized


def validate_and_prepare(
    strategy_data: Dict[str, Any],
    user: str = "user"
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Complete validation and preparation pipeline for strategy.
    
    This function:
    1. Sanitizes the data
    2. Validates against schema
    3. Validates business rules
    4. Validates condition syntax
    5. Adds metadata
    
    Args:
        strategy_data: Strategy configuration dictionary
        user: Username creating/updating the strategy
        
    Returns:
        Tuple of (is_valid, prepared_data, error_messages)
        
    Example:
        >>> strategy = {"name": "Test", "symbol": "eurusd", ...}
        >>> is_valid, prepared, errors = validate_and_prepare(strategy)
        >>> if is_valid:
        ...     # Save prepared strategy
        ...     save_strategy(prepared)
    """
    errors = []
    
    # 1. Sanitize
    sanitized = sanitize_strategy(strategy_data)
    
    # 2. Validate schema and business rules
    is_valid, schema_errors = validate_strategy(sanitized)
    if not is_valid:
        errors.extend(schema_errors)
        return False, sanitized, errors
    
    # 3. Validate condition syntax
    is_valid, condition_errors = validate_all_conditions(sanitized)
    if not is_valid:
        errors.extend(condition_errors)
        return False, sanitized, errors
    
    # 4. Add metadata
    prepared = add_metadata(sanitized, user)
    
    return True, prepared, []

