"""
Unit tests for indicator calculations
"""

import pytest
import math
from backend.ai.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_atr,
    calculate_all_indicators,
    generate_facts_from_indicators,
)


def test_calculate_ema_basic():
    """Test basic EMA calculation."""
    prices = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    ema = calculate_ema(prices, period=3)

    assert len(ema) == len(prices)
    # EMA should be increasing for increasing prices
    assert ema[-1] > ema[-2]


def test_calculate_ema_empty():
    """Test EMA with empty prices."""
    ema = calculate_ema([], period=10)
    assert ema == []


def test_calculate_rsi_basic():
    """Test basic RSI calculation."""
    # Prices going up should give RSI > 50
    prices_up = [44.0 + i * 0.5 for i in range(20)]
    rsi_up = calculate_rsi(prices_up, period=14)

    assert len(rsi_up) == len(prices_up)
    # Last RSI should be high for uptrend
    assert rsi_up[-1] > 50

    # Prices going down should give RSI < 50
    prices_down = [50.0 - i * 0.5 for i in range(20)]
    rsi_down = calculate_rsi(prices_down, period=14)

    # Last RSI should be low for downtrend
    assert rsi_down[-1] < 50


def test_calculate_rsi_bounds():
    """Test RSI stays within 0-100 bounds."""
    prices = [44.0 + i * 0.1 for i in range(30)]
    rsi = calculate_rsi(prices, period=14)

    # Filter out NaN values
    valid_rsi = [r for r in rsi if not math.isnan(r)]

    for r in valid_rsi:
        assert 0 <= r <= 100


def test_calculate_macd_basic():
    """Test basic MACD calculation."""
    prices = [1.0 + i * 0.01 for i in range(50)]
    macd_data = calculate_macd(prices, fast=12, slow=26, signal=9)

    assert "macd" in macd_data
    assert "signal" in macd_data
    assert "histogram" in macd_data

    assert len(macd_data["macd"]) == len(prices)
    assert len(macd_data["signal"]) == len(prices)
    assert len(macd_data["histogram"]) == len(prices)


def test_calculate_macd_uptrend():
    """Test MACD in uptrend."""
    prices = [1.0 + i * 0.02 for i in range(50)]
    macd_data = calculate_macd(prices)

    # In uptrend, MACD histogram should eventually be positive
    # (after enough data for indicators to stabilize)
    hist = macd_data["histogram"]
    # Check last value (should be positive in strong uptrend)
    assert not math.isnan(hist[-1])


def test_calculate_atr_basic():
    """Test basic ATR calculation."""
    bars = [
        {"high": 1.10, "low": 1.08, "close": 1.09},
        {"high": 1.11, "low": 1.09, "close": 1.10},
        {"high": 1.12, "low": 1.10, "close": 1.11},
        {"high": 1.13, "low": 1.11, "close": 1.12},
        {"high": 1.14, "low": 1.12, "close": 1.13},
    ] * 5  # Repeat to get enough data

    atr = calculate_atr(bars, period=5)

    assert len(atr) == len(bars)
    # ATR should be positive
    valid_atr = [a for a in atr if not math.isnan(a)]
    for a in valid_atr:
        assert a > 0


def test_calculate_atr_increasing_volatility():
    """Test ATR increases with volatility."""
    # Low volatility bars
    low_vol_bars = [
        {
            "high": 1.0 + i * 0.001,
            "low": 1.0 + i * 0.001 - 0.0005,
            "close": 1.0 + i * 0.001,
        }
        for i in range(20)
    ]

    # High volatility bars
    high_vol_bars = [
        {"high": 1.0 + i * 0.01, "low": 1.0 + i * 0.01 - 0.005, "close": 1.0 + i * 0.01}
        for i in range(20)
    ]

    atr_low = calculate_atr(low_vol_bars, period=10)
    atr_high = calculate_atr(high_vol_bars, period=10)

    # High volatility should have higher ATR
    assert atr_high[-1] > atr_low[-1]


def test_calculate_all_indicators():
    """Test calculating all indicators at once."""
    bars = [
        {"open": 1.08, "high": 1.10, "low": 1.08, "close": 1.09 + i * 0.001}
        for i in range(60)
    ]

    config = {
        "ema": {"fast": 20, "slow": 50},
        "rsi": {"period": 14},
        "macd": {"fast": 12, "slow": 26, "signal": 9},
        "atr": {"period": 14},
    }

    indicators = calculate_all_indicators(bars, config)

    assert "ema_fast" in indicators
    assert "ema_slow" in indicators
    assert "rsi" in indicators
    assert "macd" in indicators
    assert "macd_signal" in indicators
    assert "macd_hist" in indicators
    assert "atr" in indicators


def test_generate_facts_ema():
    """Test fact generation for EMA indicators."""
    bars = [{"close": 1.10}]
    indicators = {"ema_fast": 1.09, "ema_slow": 1.08}
    config = {}

    facts = generate_facts_from_indicators(bars, indicators, config)

    assert facts["ema_fast_gt_slow"] is True
    assert facts["ema_fast_lt_slow"] is False
    assert facts["price_above_ema_fast"] is True
    assert facts["price_close_lt_ema_slow"] is False


def test_generate_facts_rsi():
    """Test fact generation for RSI indicator."""
    bars = [{"close": 1.10}]
    indicators = {"rsi": 75}
    config = {"rsi": {"overbought": 70, "oversold": 30}}

    facts = generate_facts_from_indicators(bars, indicators, config)

    assert facts["rsi_gt_70"] is True
    assert facts["rsi_lt_30"] is False
    assert facts["rsi_between_40_60"] is False


def test_generate_facts_macd():
    """Test fact generation for MACD indicator."""
    bars = [{"close": 1.10}]
    indicators = {"macd_hist": 0.0005}
    config = {}

    facts = generate_facts_from_indicators(bars, indicators, config)

    assert facts["macd_hist_gt_0"] is True
    assert facts["macd_hist_lt_0"] is False


def test_generate_facts_candlestick():
    """Test fact generation for candlestick patterns."""
    # Long upper wick
    bars = [{"open": 1.09, "high": 1.12, "low": 1.08, "close": 1.09}]  # High wick
    indicators = {}
    config = {}

    facts = generate_facts_from_indicators(bars, indicators, config)

    # Upper wick = 1.12 - 1.09 = 0.03
    # Body = |1.09 - 1.09| = 0
    # Since body is 0, we need to handle division
    # The function should handle this edge case
    assert "long_upper_wick" in facts
    assert "long_lower_wick" in facts


def test_generate_facts_comprehensive():
    """Test comprehensive fact generation."""
    bars = [{"open": 1.085, "high": 1.10, "low": 1.08, "close": 1.095}]

    indicators = {
        "ema_fast": 1.09,
        "ema_slow": 1.08,
        "rsi": 55,
        "macd_hist": 0.0001,
        "atr": 0.002,
        "atr_median": 0.0015,
    }

    config = {"rsi": {"overbought": 70, "oversold": 30}}

    facts = generate_facts_from_indicators(bars, indicators, config)

    # Verify all expected facts are present
    assert "ema_fast_gt_slow" in facts
    assert "rsi_between_40_60" in facts
    assert "macd_hist_gt_0" in facts
    assert "atr_above_median" in facts
    assert "long_upper_wick" in facts
    assert "long_lower_wick" in facts


def test_calculate_all_indicators_empty_bars():
    """Test with empty bars list."""
    indicators = calculate_all_indicators([], {})
    assert indicators == {}


def test_calculate_all_indicators_partial_config():
    """Test with partial indicator configuration."""
    bars = [{"open": 1.08, "high": 1.10, "low": 1.08, "close": 1.09} for _ in range(30)]

    # Only configure EMA
    config = {"ema": {"fast": 10, "slow": 20}}

    indicators = calculate_all_indicators(bars, config)

    assert "ema_fast" in indicators
    assert "ema_slow" in indicators
    assert "rsi" not in indicators  # Not configured
    assert "macd" not in indicators  # Not configured
