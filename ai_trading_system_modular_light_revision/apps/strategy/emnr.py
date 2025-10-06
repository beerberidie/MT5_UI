"""apps/strategy/emnr.py — EMNR loader & evaluator"""
from typing import Dict, Any

def evaluate_conditions(facts: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, bool]:
    """facts: precomputed indicator facts for a symbol/timeframe, e.g.:
        {"ema_fast_gt_slow": True, "rsi_lt_30": False, ...}
       rules: {"conditions": {"entry": [...], "exit": [...], "strong": [...], "weak": [...]}}
    Returns booleans for each condition set.
    """
    conds = rules.get("conditions", {})
    out = {}
    for k in ("entry","exit","strong","weak"):
        required = conds.get(k, [])
        out[k] = all(facts.get(name, False) for name in required) if required else False
    return out
