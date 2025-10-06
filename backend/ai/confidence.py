"""
Confidence Scoring Model

Calculates a 0-100 confidence score based on EMNR flags, alignment, and news penalties.
Ported from ai_trading_system_modular_light_revision/apps/strategy/confidence.py
"""

from typing import Dict

# Scoring weights for each condition type
WEIGHTS = {
    "entry": 30,    # Entry condition met
    "strong": 25,   # Strong confirmation
    "weak": -15,    # Weak signal (penalty)
    "exit": -40,    # Exit condition met (strong penalty)
    "align": 10,    # Alignment bonus (trend/timeframe/session)
}


def confidence_score(
    emnr_flags: Dict[str, bool],
    align_ok: bool = False,
    news_penalty: int = 0
) -> int:
    """
    Calculate confidence score (0-100) based on EMNR flags and modifiers.
    
    Scoring Logic:
    - Entry condition: +30
    - Strong confirmation: +25
    - Weak signal: -15
    - Exit condition: -40
    - Alignment bonus: +10 (if align_ok=True)
    - News penalty: negative value (e.g., -20 to -40)
    
    Action Thresholds:
    - < 60: Observe only
    - 60-74: Pending orders only
    - >= 75: Market/pending orders allowed (if RR >= min_rr)
    
    Args:
        emnr_flags: Dictionary with entry, exit, strong, weak boolean flags
        align_ok: True if trend/timeframe/session are aligned
        news_penalty: Negative penalty for news events (typically -20 to -40)
    
    Returns:
        Confidence score clamped to 0-100
    
    Examples:
        >>> confidence_score({"entry": True, "exit": False, "strong": False, "weak": False}, False, 0)
        30
        
        >>> confidence_score({"entry": True, "exit": False, "strong": True, "weak": False}, True, 0)
        65  # 30 + 25 + 10
        
        >>> confidence_score({"entry": True, "exit": False, "strong": True, "weak": False}, True, -20)
        45  # 30 + 25 + 10 - 20
    """
    score = 0
    
    # Add/subtract based on EMNR flags
    if emnr_flags.get("entry", False):
        score += WEIGHTS["entry"]
    
    if emnr_flags.get("strong", False):
        score += WEIGHTS["strong"]
    
    if emnr_flags.get("weak", False):
        score += WEIGHTS["weak"]
    
    if emnr_flags.get("exit", False):
        score += WEIGHTS["exit"]
    
    # Add alignment bonus
    if align_ok:
        score += WEIGHTS["align"]
    
    # Apply news penalty (should be negative)
    score += news_penalty
    
    # Clamp to 0-100 range
    return max(0, min(100, score))


def get_confidence_level(score: int) -> str:
    """
    Get human-readable confidence level from score.
    
    Args:
        score: Confidence score (0-100)
    
    Returns:
        String describing confidence level
    """
    if score >= 75:
        return "HIGH"
    elif score >= 60:
        return "MEDIUM"
    else:
        return "LOW"


def get_score_breakdown(
    emnr_flags: Dict[str, bool],
    align_ok: bool = False,
    news_penalty: int = 0
) -> Dict[str, int]:
    """
    Get detailed breakdown of confidence score components.
    
    Args:
        emnr_flags: Dictionary with entry, exit, strong, weak boolean flags
        align_ok: True if trend/timeframe/session are aligned
        news_penalty: Negative penalty for news events
    
    Returns:
        Dictionary with component scores and total
    """
    breakdown = {
        "entry": WEIGHTS["entry"] if emnr_flags.get("entry", False) else 0,
        "strong": WEIGHTS["strong"] if emnr_flags.get("strong", False) else 0,
        "weak": WEIGHTS["weak"] if emnr_flags.get("weak", False) else 0,
        "exit": WEIGHTS["exit"] if emnr_flags.get("exit", False) else 0,
        "align": WEIGHTS["align"] if align_ok else 0,
        "news_penalty": news_penalty,
    }
    
    # Calculate total before clamping
    raw_total = sum(breakdown.values())
    
    breakdown["raw_total"] = raw_total
    breakdown["final_score"] = max(0, min(100, raw_total))
    
    return breakdown

