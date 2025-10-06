"""
Unit tests for confidence scorer
"""

import pytest
from backend.ai.confidence import (
    confidence_score,
    get_confidence_level,
    get_score_breakdown,
    WEIGHTS
)


def test_confidence_entry_only():
    """Test confidence with only entry flag."""
    flags = {"entry": True, "exit": False, "strong": False, "weak": False}
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    
    assert score == WEIGHTS["entry"]  # 30
    assert score == 30


def test_confidence_entry_strong():
    """Test confidence with entry and strong flags."""
    flags = {"entry": True, "exit": False, "strong": True, "weak": False}
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    
    expected = WEIGHTS["entry"] + WEIGHTS["strong"]  # 30 + 25 = 55
    assert score == expected
    assert score == 55


def test_confidence_with_alignment():
    """Test confidence with alignment bonus."""
    flags = {"entry": True, "exit": False, "strong": True, "weak": False}
    score = confidence_score(flags, align_ok=True, news_penalty=0)
    
    expected = WEIGHTS["entry"] + WEIGHTS["strong"] + WEIGHTS["align"]  # 30 + 25 + 10 = 65
    assert score == expected
    assert score == 65


def test_confidence_with_news_penalty():
    """Test confidence with news penalty."""
    flags = {"entry": True, "exit": False, "strong": True, "weak": False}
    score = confidence_score(flags, align_ok=True, news_penalty=-20)
    
    expected = 65 - 20  # 45
    assert score == expected
    assert score == 45


def test_confidence_with_weak_signal():
    """Test confidence with weak signal penalty."""
    flags = {"entry": True, "exit": False, "strong": False, "weak": True}
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    
    expected = WEIGHTS["entry"] + WEIGHTS["weak"]  # 30 + (-15) = 15
    assert score == expected
    assert score == 15


def test_confidence_with_exit_signal():
    """Test confidence with exit signal (strong penalty)."""
    flags = {"entry": True, "exit": True, "strong": False, "weak": False}
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    
    expected = WEIGHTS["entry"] + WEIGHTS["exit"]  # 30 + (-40) = -10, clamped to 0
    assert score == 0  # Clamped to minimum


def test_confidence_clamping_minimum():
    """Test that confidence is clamped to 0."""
    flags = {"entry": False, "exit": True, "strong": False, "weak": True}
    score = confidence_score(flags, align_ok=False, news_penalty=-50)
    
    # Exit (-40) + Weak (-15) + Penalty (-50) = -105, clamped to 0
    assert score == 0


def test_confidence_clamping_maximum():
    """Test that confidence is clamped to 100."""
    # This is theoretical since our weights max out at 65 + align
    flags = {"entry": True, "exit": False, "strong": True, "weak": False}
    score = confidence_score(flags, align_ok=True, news_penalty=50)  # Positive bonus (unusual)
    
    # 30 + 25 + 10 + 50 = 115, clamped to 100
    assert score == 100


def test_confidence_all_flags_true():
    """Test with all flags true (conflicting signals)."""
    flags = {"entry": True, "exit": True, "strong": True, "weak": True}
    score = confidence_score(flags, align_ok=True, news_penalty=0)
    
    # 30 + (-40) + 25 + (-15) + 10 = 10
    expected = 30 - 40 + 25 - 15 + 10
    assert score == expected
    assert score == 10


def test_confidence_all_flags_false():
    """Test with all flags false."""
    flags = {"entry": False, "exit": False, "strong": False, "weak": False}
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    
    assert score == 0


def test_get_confidence_level_high():
    """Test confidence level classification - HIGH."""
    assert get_confidence_level(75) == "HIGH"
    assert get_confidence_level(80) == "HIGH"
    assert get_confidence_level(100) == "HIGH"


def test_get_confidence_level_medium():
    """Test confidence level classification - MEDIUM."""
    assert get_confidence_level(60) == "MEDIUM"
    assert get_confidence_level(65) == "MEDIUM"
    assert get_confidence_level(74) == "MEDIUM"


def test_get_confidence_level_low():
    """Test confidence level classification - LOW."""
    assert get_confidence_level(0) == "LOW"
    assert get_confidence_level(30) == "LOW"
    assert get_confidence_level(59) == "LOW"


def test_get_score_breakdown():
    """Test score breakdown calculation."""
    flags = {"entry": True, "exit": False, "strong": True, "weak": False}
    breakdown = get_score_breakdown(flags, align_ok=True, news_penalty=-10)
    
    assert breakdown["entry"] == 30
    assert breakdown["exit"] == 0
    assert breakdown["strong"] == 25
    assert breakdown["weak"] == 0
    assert breakdown["align"] == 10
    assert breakdown["news_penalty"] == -10
    assert breakdown["raw_total"] == 55  # 30 + 25 + 10 - 10
    assert breakdown["final_score"] == 55


def test_get_score_breakdown_with_clamping():
    """Test score breakdown with clamping."""
    flags = {"entry": False, "exit": True, "strong": False, "weak": True}
    breakdown = get_score_breakdown(flags, align_ok=False, news_penalty=-50)
    
    assert breakdown["exit"] == -40
    assert breakdown["weak"] == -15
    assert breakdown["news_penalty"] == -50
    assert breakdown["raw_total"] == -105
    assert breakdown["final_score"] == 0  # Clamped


def test_confidence_realistic_scenario_bullish():
    """Test realistic bullish scenario."""
    # Strong bullish setup: entry + strong + alignment, no negatives
    flags = {"entry": True, "exit": False, "strong": True, "weak": False}
    score = confidence_score(flags, align_ok=True, news_penalty=0)
    
    assert score == 65  # Should trigger "open_or_scale" action (>= 75 needed)
    assert get_confidence_level(score) == "MEDIUM"


def test_confidence_realistic_scenario_weak_bullish():
    """Test realistic weak bullish scenario."""
    # Weak bullish: entry only, no alignment
    flags = {"entry": True, "exit": False, "strong": False, "weak": False}
    score = confidence_score(flags, align_ok=False, news_penalty=0)
    
    assert score == 30  # Should trigger "observe" action (< 60)
    assert get_confidence_level(score) == "LOW"


def test_confidence_realistic_scenario_exit():
    """Test realistic exit scenario."""
    # Exit signal present
    flags = {"entry": True, "exit": True, "strong": True, "weak": False}
    score = confidence_score(flags, align_ok=True, news_penalty=0)
    
    # 30 - 40 + 25 + 10 = 25
    assert score == 25
    assert get_confidence_level(score) == "LOW"

