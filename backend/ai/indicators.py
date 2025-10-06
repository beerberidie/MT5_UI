"""
Technical Indicator Calculator

Calculates EMA, RSI, MACD, ATR using pandas for efficiency.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: List of closing prices
        period: EMA period (e.g., 20, 50)
    
    Returns:
        List of EMA values (same length as prices, NaN for initial values)
    
    Example:
        >>> prices = [1.0850, 1.0855, 1.0860, 1.0865, 1.0870]
        >>> ema = calculate_ema(prices, 3)
        >>> len(ema) == len(prices)
        True
    """
    if not prices or period <= 0:
        return []
    
    series = pd.Series(prices)
    ema = series.ewm(span=period, adjust=False).mean()
    return ema.tolist()


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: List of closing prices
        period: RSI period (default 14)
    
    Returns:
        List of RSI values (0-100)
    
    Example:
        >>> prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28]
        >>> rsi = calculate_rsi(prices, 14)
        >>> 0 <= rsi[-1] <= 100
        True
    """
    if not prices or period <= 0 or len(prices) < period + 1:
        return [np.nan] * len(prices)
    
    series = pd.Series(prices)
    delta = series.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.tolist()


def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Dict[str, List[float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        prices: List of closing prices
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)
    
    Returns:
        Dictionary with 'macd', 'signal', 'histogram' keys
    
    Example:
        >>> prices = [1.0850] * 50  # Flat prices for simplicity
        >>> macd_data = calculate_macd(prices)
        >>> 'macd' in macd_data and 'signal' in macd_data and 'histogram' in macd_data
        True
    """
    if not prices or len(prices) < slow:
        empty = [np.nan] * len(prices)
        return {'macd': empty, 'signal': empty, 'histogram': empty}
    
    series = pd.Series(prices)
    
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.tolist(),
        'signal': signal_line.tolist(),
        'histogram': histogram.tolist()
    }


def calculate_atr(bars: List[Dict[str, float]], period: int = 14) -> List[float]:
    """
    Calculate Average True Range.
    
    Args:
        bars: List of OHLC bars with 'high', 'low', 'close' keys
        period: ATR period (default 14)
    
    Returns:
        List of ATR values
    
    Example:
        >>> bars = [
        ...     {'high': 1.0860, 'low': 1.0840, 'close': 1.0850},
        ...     {'high': 1.0870, 'low': 1.0845, 'close': 1.0865},
        ... ]
        >>> atr = calculate_atr(bars, 2)
        >>> len(atr) == len(bars)
        True
    """
    if not bars or period <= 0 or len(bars) < 2:
        return [np.nan] * len(bars)
    
    df = pd.DataFrame(bars)
    
    # Ensure required columns exist
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return [np.nan] * len(bars)
    
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr.tolist()


def calculate_all_indicators(
    bars: List[Dict[str, float]],
    config: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate all indicators based on configuration.
    
    Args:
        bars: List of OHLC bars
        config: Indicator configuration with ema, rsi, macd, atr settings
    
    Returns:
        Dictionary with latest indicator values
    
    Example:
        >>> bars = [{'open': 1.08, 'high': 1.09, 'low': 1.07, 'close': 1.085}] * 50
        >>> config = {
        ...     'ema': {'fast': 20, 'slow': 50},
        ...     'rsi': {'period': 14},
        ...     'macd': {'fast': 12, 'slow': 26, 'signal': 9},
        ...     'atr': {'period': 14}
        ... }
        >>> indicators = calculate_all_indicators(bars, config)
        >>> 'ema_fast' in indicators
        True
    """
    if not bars:
        return {}
    
    closes = [b['close'] for b in bars]
    indicators = {}
    
    # EMA
    if 'ema' in config:
        ema_config = config['ema']
        if 'fast' in ema_config:
            ema_fast = calculate_ema(closes, ema_config['fast'])
            indicators['ema_fast'] = ema_fast[-1] if ema_fast else np.nan
        if 'slow' in ema_config:
            ema_slow = calculate_ema(closes, ema_config['slow'])
            indicators['ema_slow'] = ema_slow[-1] if ema_slow else np.nan
    
    # RSI
    if 'rsi' in config:
        rsi_config = config['rsi']
        period = rsi_config.get('period', 14)
        rsi = calculate_rsi(closes, period)
        indicators['rsi'] = rsi[-1] if rsi else np.nan
    
    # MACD
    if 'macd' in config:
        macd_config = config['macd']
        macd_data = calculate_macd(
            closes,
            macd_config.get('fast', 12),
            macd_config.get('slow', 26),
            macd_config.get('signal', 9)
        )
        indicators['macd'] = macd_data['macd'][-1] if macd_data['macd'] else np.nan
        indicators['macd_signal'] = macd_data['signal'][-1] if macd_data['signal'] else np.nan
        indicators['macd_hist'] = macd_data['histogram'][-1] if macd_data['histogram'] else np.nan
    
    # ATR
    if 'atr' in config:
        atr_config = config['atr']
        period = atr_config.get('period', 14)
        atr = calculate_atr(bars, period)
        indicators['atr'] = atr[-1] if atr else np.nan
        
        # Calculate ATR median for comparison
        if len(atr) >= 50:
            atr_values = [v for v in atr[-50:] if not pd.isna(v)]
            if atr_values:
                indicators['atr_median'] = float(np.median(atr_values))
    
    return indicators


def generate_facts_from_indicators(
    bars: List[Dict[str, float]],
    indicators: Dict[str, float],
    config: Dict[str, Any]
) -> Dict[str, bool]:
    """
    Generate boolean facts from indicator values.
    
    Args:
        bars: List of OHLC bars
        indicators: Dictionary of indicator values
        config: Indicator configuration
    
    Returns:
        Dictionary of condition_name -> bool
    
    Example:
        >>> bars = [{'close': 1.085}]
        >>> indicators = {'ema_fast': 1.084, 'ema_slow': 1.083, 'rsi': 55}
        >>> config = {'rsi': {'overbought': 70, 'oversold': 30}}
        >>> facts = generate_facts_from_indicators(bars, indicators, config)
        >>> 'ema_fast_gt_slow' in facts
        True
    """
    facts = {}
    
    if not bars:
        return facts
    
    current_price = bars[-1]['close']
    
    # EMA facts
    if 'ema_fast' in indicators and 'ema_slow' in indicators:
        ema_fast = indicators['ema_fast']
        ema_slow = indicators['ema_slow']
        
        if not pd.isna(ema_fast) and not pd.isna(ema_slow):
            facts['ema_fast_gt_slow'] = ema_fast > ema_slow
            facts['ema_fast_lt_slow'] = ema_fast < ema_slow
            facts['price_above_ema_fast'] = current_price > ema_fast
            facts['price_below_ema_fast'] = current_price < ema_fast
            facts['price_close_lt_ema_slow'] = current_price < ema_slow
            facts['price_above_ema_slow'] = current_price > ema_slow
    
    # RSI facts
    if 'rsi' in indicators and 'rsi' in config:
        rsi = indicators['rsi']
        rsi_config = config['rsi']
        
        if not pd.isna(rsi):
            oversold = rsi_config.get('oversold', 30)
            overbought = rsi_config.get('overbought', 70)
            
            facts['rsi_lt_30'] = rsi < oversold
            facts['rsi_gt_70'] = rsi > overbought
            facts['rsi_between_40_60'] = 40 <= rsi <= 60
    
    # MACD facts
    if 'macd_hist' in indicators:
        macd_hist = indicators['macd_hist']
        
        if not pd.isna(macd_hist):
            facts['macd_hist_gt_0'] = macd_hist > 0
            facts['macd_hist_lt_0'] = macd_hist < 0
    
    # ATR facts
    if 'atr' in indicators and 'atr_median' in indicators:
        atr = indicators['atr']
        atr_median = indicators['atr_median']
        
        if not pd.isna(atr) and not pd.isna(atr_median):
            facts['atr_above_median'] = atr > atr_median
            facts['atr_below_median'] = atr < atr_median
    
    # Candlestick pattern facts
    if len(bars) > 0:
        last_bar = bars[-1]
        # Check if bar has all required OHLC data
        if all(k in last_bar for k in ['open', 'high', 'low', 'close']):
            body = abs(last_bar['close'] - last_bar['open'])
            upper_wick = last_bar['high'] - max(last_bar['open'], last_bar['close'])
            lower_wick = min(last_bar['open'], last_bar['close']) - last_bar['low']

            facts['long_upper_wick'] = upper_wick > body * 2 if body > 0 else False
            facts['long_lower_wick'] = lower_wick > body * 2 if body > 0 else False
        else:
            # Default to False if OHLC data not available
            facts['long_upper_wick'] = False
            facts['long_lower_wick'] = False

    # Placeholder for complex patterns (to be implemented)
    facts['divergence_bearish'] = False
    facts['divergence_bullish'] = False

    return facts

