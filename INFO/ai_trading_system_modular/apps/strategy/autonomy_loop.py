"""apps/strategy/autonomy_loop.py — One evaluation cycle"""
from typing import Dict, Any
from .emnr import evaluate_conditions
from .confidence import confidence_score
from .scheduler import schedule_action

def run_cycle(facts: Dict[str, Any], rules: Dict[str, Any], align_ok: bool, min_rr_ok: bool, news_penalty: int = 0) -> Dict[str, Any]:
    flags = evaluate_conditions(facts, rules)  # entry/exit/strong/weak
    score = confidence_score(flags, align_ok=align_ok, news_penalty=news_penalty)
    sched = schedule_action(score, min_rr_ok=min_rr_ok)
    return {
        "tradeIdea": flags,
        "confidence": score,
        "executionPlan": sched,
        "rrPlan": {"min_rr_ok": min_rr_ok},
        "monitoring": {"invalidations": rules.get("strategy", {}).get("invalidations", [])}
    }
