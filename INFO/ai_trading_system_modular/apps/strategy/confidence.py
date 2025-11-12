"""apps/strategy/confidence.py — Confidence scoring"""

from typing import Dict

WEIGHTS = {"entry": 30, "strong": 25, "weak": -15, "exit": -40, "align": 10}


def confidence_score(
    flags: Dict[str, bool], align_ok: bool, news_penalty: int = 0
) -> int:
    score = 0
    for k, w in WEIGHTS.items():
        if k in ("align",):
            continue
        score += w if flags.get(k, False) else 0
    if align_ok:
        score += WEIGHTS["align"]
    score += news_penalty  # negative for penalties
    return max(0, min(100, score))
