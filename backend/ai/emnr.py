"""
EMNR Rule Evaluator

Evaluates Entry/Exit/Strong/Weak conditions based on indicator facts.
Ported from ai_trading_system_modular_light_revision/apps/strategy/emnr.py
"""

from typing import Dict, Any, List


def evaluate_conditions(
    facts: Dict[str, bool], conditions: Dict[str, List[str]]
) -> Dict[str, bool]:
    """
    Evaluate EMNR conditions based on indicator facts.

    Args:
        facts: Dictionary of condition_name -> bool
               Example: {"ema_fast_gt_slow": True, "rsi_lt_30": False, ...}
        conditions: Dictionary with keys: entry, exit, strong, weak
                   Each value is a list of condition names that must all be true
                   Example: {"entry": ["ema_fast_gt_slow", "rsi_between_40_60"], ...}

    Returns:
        Dictionary with entry, exit, strong, weak boolean flags
        Example: {"entry": True, "exit": False, "strong": True, "weak": False}

    Example:
        >>> facts = {"ema_fast_gt_slow": True, "rsi_between_40_60": True}
        >>> conditions = {"entry": ["ema_fast_gt_slow", "rsi_between_40_60"], "exit": [], "strong": [], "weak": []}
        >>> evaluate_conditions(facts, conditions)
        {"entry": True, "exit": False, "strong": False, "weak": False}
    """
    result = {}

    for condition_type in ("entry", "exit", "strong", "weak"):
        required_conditions = conditions.get(condition_type, [])

        if not required_conditions:
            # No conditions specified = False
            result[condition_type] = False
        else:
            # All required conditions must be True
            result[condition_type] = all(
                facts.get(condition_name, False)
                for condition_name in required_conditions
            )

    return result


def validate_conditions(conditions: Dict[str, List[str]]) -> bool:
    """
    Validate that conditions dictionary has the correct structure.

    Args:
        conditions: Dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    required_keys = {"entry", "exit", "strong", "weak"}

    if not isinstance(conditions, dict):
        return False

    # Check all required keys are present
    if not required_keys.issubset(conditions.keys()):
        return False

    # Check all values are lists of strings
    for key in required_keys:
        value = conditions[key]
        if not isinstance(value, list):
            return False
        if not all(isinstance(item, str) for item in value):
            return False

    return True
