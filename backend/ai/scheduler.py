"""
Action Scheduler

Maps confidence scores to trading actions with risk percentages.
Ported from ai_trading_system_modular_light_revision/apps/strategy/scheduler.py
"""

from typing import Dict


def schedule_action(
    confidence: int,
    min_rr_ok: bool,
    risk_cap_pct: float = 0.03
) -> Dict[str, str]:
    """
    Determine trading action based on confidence score and RR validation.
    
    Action Logic:
    - confidence < 60: observe (no action)
    - confidence 60-74: pending_only (limit orders only, reduced risk)
    - confidence >= 75 and RR < min: wait_rr (wait for better setup)
    - confidence >= 75 and RR >= min: open_or_scale (execute trade)
    
    Args:
        confidence: Confidence score (0-100)
        min_rr_ok: True if risk/reward ratio meets minimum requirement
        risk_cap_pct: Maximum risk percentage (default 0.03 = 3%)
    
    Returns:
        Dictionary with action and riskPct
        Example: {"action": "open_or_scale", "riskPct": "0.03"}
    
    Examples:
        >>> schedule_action(45, True, 0.03)
        {"action": "observe", "riskPct": "0"}
        
        >>> schedule_action(65, True, 0.03)
        {"action": "pending_only", "riskPct": "0.015"}
        
        >>> schedule_action(80, False, 0.03)
        {"action": "wait_rr", "riskPct": "0"}
        
        >>> schedule_action(80, True, 0.03)
        {"action": "open_or_scale", "riskPct": "0.03"}
    """
    # Low confidence: observe only
    if confidence < 60:
        return {
            "action": "observe",
            "riskPct": "0"
        }
    
    # Medium confidence: pending orders only with reduced risk
    if confidence < 75:
        reduced_risk = min(risk_cap_pct / 2, 0.02)
        return {
            "action": "pending_only",
            "riskPct": f"{reduced_risk:.3f}"
        }
    
    # High confidence but RR not met: wait for better setup
    if not min_rr_ok:
        return {
            "action": "wait_rr",
            "riskPct": "0"
        }
    
    # High confidence and RR met: execute trade
    return {
        "action": "open_or_scale",
        "riskPct": f"{risk_cap_pct:.3f}"
    }


def get_action_description(action: str) -> str:
    """
    Get human-readable description of action.
    
    Args:
        action: Action string (observe, pending_only, wait_rr, open_or_scale)
    
    Returns:
        Description string
    """
    descriptions = {
        "observe": "Confidence too low. Observing market only.",
        "pending_only": "Medium confidence. Pending orders allowed with reduced risk.",
        "wait_rr": "High confidence but risk/reward ratio insufficient. Waiting for better setup.",
        "open_or_scale": "High confidence and good risk/reward. Ready to execute trade.",
    }
    return descriptions.get(action, "Unknown action")


def should_execute_trade(action: str) -> bool:
    """
    Check if action allows trade execution.
    
    Args:
        action: Action string
    
    Returns:
        True if trade can be executed
    """
    return action in ("open_or_scale", "pending_only")


def get_risk_multiplier(action: str) -> float:
    """
    Get risk multiplier for action type.
    
    Args:
        action: Action string
    
    Returns:
        Risk multiplier (0.0 to 1.0)
    """
    multipliers = {
        "observe": 0.0,
        "pending_only": 0.5,  # Half risk
        "wait_rr": 0.0,
        "open_or_scale": 1.0,  # Full risk
    }
    return multipliers.get(action, 0.0)

