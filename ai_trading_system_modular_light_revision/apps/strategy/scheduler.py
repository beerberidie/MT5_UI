"""apps/strategy/scheduler.py — Map confidence → action/risk"""

from typing import Dict


def schedule_action(
    score: int, min_rr_ok: bool, risk_cap_pct: float = 0.03
) -> Dict[str, str]:
    if score < 60:
        return {"action": "observe", "riskPct": "0"}
    if score < 75:
        return {"action": "pending_only", "riskPct": f"{min(risk_cap_pct/2, 0.02):.2f}"}
    if not min_rr_ok:
        return {"action": "wait_rr", "riskPct": "0"}
    return {"action": "open_or_scale", "riskPct": f"{risk_cap_pct:.2f}"}
