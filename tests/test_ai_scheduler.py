"""
Unit tests for action scheduler
"""

import pytest
from backend.ai.scheduler import (
    schedule_action,
    get_action_description,
    should_execute_trade,
    get_risk_multiplier,
)


def test_schedule_action_observe():
    """Test observe action for low confidence."""
    result = schedule_action(confidence=45, min_rr_ok=True, risk_cap_pct=0.03)

    assert result["action"] == "observe"
    assert result["riskPct"] == "0"


def test_schedule_action_pending_only():
    """Test pending_only action for medium confidence."""
    result = schedule_action(confidence=65, min_rr_ok=True, risk_cap_pct=0.03)

    assert result["action"] == "pending_only"
    assert float(result["riskPct"]) == 0.015  # Half of risk_cap_pct


def test_schedule_action_wait_rr():
    """Test wait_rr action when RR not met."""
    result = schedule_action(confidence=80, min_rr_ok=False, risk_cap_pct=0.03)

    assert result["action"] == "wait_rr"
    assert result["riskPct"] == "0"


def test_schedule_action_open_or_scale():
    """Test open_or_scale action for high confidence and good RR."""
    result = schedule_action(confidence=80, min_rr_ok=True, risk_cap_pct=0.03)

    assert result["action"] == "open_or_scale"
    assert result["riskPct"] == "0.030"


def test_schedule_action_boundary_60():
    """Test boundary at confidence 60."""
    # Just below threshold
    result_below = schedule_action(confidence=59, min_rr_ok=True, risk_cap_pct=0.03)
    assert result_below["action"] == "observe"

    # At threshold
    result_at = schedule_action(confidence=60, min_rr_ok=True, risk_cap_pct=0.03)
    assert result_at["action"] == "pending_only"


def test_schedule_action_boundary_75():
    """Test boundary at confidence 75."""
    # Just below threshold
    result_below = schedule_action(confidence=74, min_rr_ok=True, risk_cap_pct=0.03)
    assert result_below["action"] == "pending_only"

    # At threshold with good RR
    result_at = schedule_action(confidence=75, min_rr_ok=True, risk_cap_pct=0.03)
    assert result_at["action"] == "open_or_scale"

    # At threshold with bad RR
    result_at_bad_rr = schedule_action(
        confidence=75, min_rr_ok=False, risk_cap_pct=0.03
    )
    assert result_at_bad_rr["action"] == "wait_rr"


def test_schedule_action_pending_risk_calculation():
    """Test risk calculation for pending_only action."""
    result = schedule_action(confidence=65, min_rr_ok=True, risk_cap_pct=0.04)

    # Should be half of risk_cap_pct, but capped at 0.02
    assert float(result["riskPct"]) == 0.020  # min(0.04/2, 0.02) = 0.02


def test_schedule_action_custom_risk_cap():
    """Test with custom risk cap."""
    result = schedule_action(confidence=80, min_rr_ok=True, risk_cap_pct=0.05)

    assert result["action"] == "open_or_scale"
    assert result["riskPct"] == "0.050"


def test_get_action_description():
    """Test action descriptions."""
    assert "Observing" in get_action_description("observe")
    assert "Pending" in get_action_description("pending_only")
    assert "risk/reward" in get_action_description("wait_rr")
    assert "execute" in get_action_description("open_or_scale")
    assert "Unknown" in get_action_description("invalid_action")


def test_should_execute_trade():
    """Test trade execution check."""
    assert should_execute_trade("open_or_scale") is True
    assert should_execute_trade("pending_only") is True
    assert should_execute_trade("observe") is False
    assert should_execute_trade("wait_rr") is False


def test_get_risk_multiplier():
    """Test risk multipliers."""
    assert get_risk_multiplier("observe") == 0.0
    assert get_risk_multiplier("pending_only") == 0.5
    assert get_risk_multiplier("wait_rr") == 0.0
    assert get_risk_multiplier("open_or_scale") == 1.0
    assert get_risk_multiplier("invalid") == 0.0


def test_schedule_action_zero_confidence():
    """Test with zero confidence."""
    result = schedule_action(confidence=0, min_rr_ok=True, risk_cap_pct=0.03)

    assert result["action"] == "observe"
    assert result["riskPct"] == "0"


def test_schedule_action_max_confidence():
    """Test with maximum confidence."""
    result = schedule_action(confidence=100, min_rr_ok=True, risk_cap_pct=0.03)

    assert result["action"] == "open_or_scale"
    assert result["riskPct"] == "0.030"


def test_schedule_action_realistic_scenarios():
    """Test realistic trading scenarios."""
    # Scenario 1: Weak setup
    weak = schedule_action(confidence=30, min_rr_ok=True, risk_cap_pct=0.01)
    assert weak["action"] == "observe"

    # Scenario 2: Medium setup
    medium = schedule_action(confidence=65, min_rr_ok=True, risk_cap_pct=0.01)
    assert medium["action"] == "pending_only"
    assert float(medium["riskPct"]) <= 0.01

    # Scenario 3: Strong setup with good RR
    strong = schedule_action(confidence=85, min_rr_ok=True, risk_cap_pct=0.02)
    assert strong["action"] == "open_or_scale"
    assert strong["riskPct"] == "0.020"

    # Scenario 4: Strong setup but poor RR
    strong_poor_rr = schedule_action(confidence=85, min_rr_ok=False, risk_cap_pct=0.02)
    assert strong_poor_rr["action"] == "wait_rr"
    assert strong_poor_rr["riskPct"] == "0"
