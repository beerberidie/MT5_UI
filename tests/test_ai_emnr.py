"""
Unit tests for EMNR evaluator
"""

import pytest
from backend.ai.emnr import evaluate_conditions, validate_conditions


def test_evaluate_all_conditions_met():
    """Test when all conditions are met."""
    facts = {
        "ema_fast_gt_slow": True,
        "rsi_between_40_60": True,
        "macd_hist_gt_0": True,
        "rsi_gt_70": False,
        "long_upper_wick": False
    }
    
    conditions = {
        "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
        "exit": ["rsi_gt_70"],
        "strong": ["macd_hist_gt_0"],
        "weak": ["long_upper_wick"]
    }
    
    result = evaluate_conditions(facts, conditions)
    
    assert result["entry"] is True
    assert result["exit"] is False
    assert result["strong"] is True
    assert result["weak"] is False


def test_evaluate_partial_conditions():
    """Test when only some conditions are met."""
    facts = {
        "ema_fast_gt_slow": True,
        "rsi_between_40_60": False,  # Entry condition not met
        "macd_hist_gt_0": True
    }
    
    conditions = {
        "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
        "exit": [],
        "strong": ["macd_hist_gt_0"],
        "weak": []
    }
    
    result = evaluate_conditions(facts, conditions)
    
    assert result["entry"] is False  # One condition failed
    assert result["strong"] is True


def test_evaluate_empty_conditions():
    """Test when no conditions are specified."""
    facts = {"ema_fast_gt_slow": True}
    
    conditions = {
        "entry": [],
        "exit": [],
        "strong": [],
        "weak": []
    }
    
    result = evaluate_conditions(facts, conditions)
    
    # All should be False when no conditions specified
    assert result["entry"] is False
    assert result["exit"] is False
    assert result["strong"] is False
    assert result["weak"] is False


def test_evaluate_missing_facts():
    """Test when required facts are missing."""
    facts = {
        "ema_fast_gt_slow": True
        # rsi_between_40_60 is missing
    }
    
    conditions = {
        "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
        "exit": [],
        "strong": [],
        "weak": []
    }
    
    result = evaluate_conditions(facts, conditions)
    
    # Should be False because one fact is missing
    assert result["entry"] is False


def test_validate_conditions_valid():
    """Test validation of valid conditions."""
    conditions = {
        "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
        "exit": ["rsi_gt_70"],
        "strong": ["macd_hist_gt_0"],
        "weak": ["long_upper_wick"]
    }
    
    assert validate_conditions(conditions) is True


def test_validate_conditions_missing_key():
    """Test validation fails when key is missing."""
    conditions = {
        "entry": ["ema_fast_gt_slow"],
        "exit": [],
        "strong": []
        # "weak" is missing
    }
    
    assert validate_conditions(conditions) is False


def test_validate_conditions_invalid_type():
    """Test validation fails when value is not a list."""
    conditions = {
        "entry": "ema_fast_gt_slow",  # Should be a list
        "exit": [],
        "strong": [],
        "weak": []
    }
    
    assert validate_conditions(conditions) is False


def test_validate_conditions_invalid_list_items():
    """Test validation fails when list contains non-strings."""
    conditions = {
        "entry": ["ema_fast_gt_slow", 123],  # 123 is not a string
        "exit": [],
        "strong": [],
        "weak": []
    }
    
    assert validate_conditions(conditions) is False


def test_evaluate_complex_scenario():
    """Test a complex real-world scenario."""
    facts = {
        "ema_fast_gt_slow": True,
        "rsi_between_40_60": True,
        "macd_hist_gt_0": True,
        "atr_above_median": True,
        "price_above_ema_fast": True,
        "rsi_gt_70": False,
        "long_upper_wick": True  # Weak signal present
    }
    
    conditions = {
        "entry": ["ema_fast_gt_slow", "rsi_between_40_60", "price_above_ema_fast"],
        "exit": ["rsi_gt_70"],
        "strong": ["macd_hist_gt_0", "atr_above_median"],
        "weak": ["long_upper_wick"]
    }
    
    result = evaluate_conditions(facts, conditions)
    
    assert result["entry"] is True  # All entry conditions met
    assert result["exit"] is False  # Exit condition not met
    assert result["strong"] is True  # All strong conditions met
    assert result["weak"] is True  # Weak signal present

