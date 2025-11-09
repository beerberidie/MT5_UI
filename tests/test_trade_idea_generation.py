"""
Test Trade Idea Generation

This script tests the AI evaluation system and shows detailed diagnostics
about why trade ideas are or are not being generated.
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.mt5_client import MT5Client
from backend.ai.engine import AIEngine
from backend.ai.indicators import calculate_all_indicators, generate_facts_from_indicators
from backend.ai.emnr import evaluate_conditions
from backend.ai.confidence import confidence_score, get_score_breakdown
from backend.ai.scheduler import schedule_action, get_action_description
from backend.ai.rules_manager import load_rules
from backend.ai.symbol_profiles import load_profile


def test_evaluation(symbol: str = "EURUSD", timeframe: str = "H1"):
    """
    Test AI evaluation with detailed diagnostics.
    
    Args:
        symbol: Trading symbol (default: EURUSD)
        timeframe: Timeframe (default: H1)
    """
    print("=" * 80)
    print(f"TRADE IDEA GENERATION DIAGNOSTIC TEST")
    print(f"Symbol: {symbol} | Timeframe: {timeframe}")
    print("=" * 80)
    print()
    
    # Initialize MT5 client
    print("1. Initializing MT5 Client...")
    try:
        mt5_client = MT5Client()
        print("   ✅ MT5 Client initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize MT5: {e}")
        return
    
    # Initialize AI Engine
    print("\n2. Initializing AI Engine...")
    try:
        engine = AIEngine(mt5_client, config_dir="config/ai", data_dir="data/ai")
        print("   ✅ AI Engine initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize AI Engine: {e}")
        return
    
    # Load rules
    print(f"\n3. Loading EMNR Rules for {symbol} {timeframe}...")
    try:
        rules = load_rules("config/ai/strategies", symbol, timeframe)
        if rules:
            print(f"   ✅ Rules loaded: {symbol}_{timeframe}.json")
            print(f"   Entry conditions: {rules.conditions.get('entry', [])}")
            print(f"   Strong conditions: {rules.conditions.get('strong', [])}")
            print(f"   Weak conditions: {rules.conditions.get('weak', [])}")
            print(f"   Exit conditions: {rules.conditions.get('exit', [])}")
        else:
            print(f"   ❌ No rules found for {symbol} {timeframe}")
            print(f"   Available strategies:")
            strategies_dir = Path("config/ai/strategies")
            for file in strategies_dir.glob("*.json"):
                print(f"      - {file.name}")
            return
    except Exception as e:
        print(f"   ❌ Failed to load rules: {e}")
        return
    
    # Load profile
    print(f"\n4. Loading Symbol Profile for {symbol}...")
    try:
        profile = load_profile("config/ai/profiles", symbol)
        if profile:
            print(f"   ✅ Profile loaded: {symbol}.json")
            print(f"   Best sessions: {profile.bestSessions}")
            print(f"   Best timeframes: {profile.bestTimeframes}")
            print(f"   RR target: {profile.style.get('rrTarget', 2.0)}")
        else:
            print(f"   ❌ No profile found for {symbol}")
            return
    except Exception as e:
        print(f"   ❌ Failed to load profile: {e}")
        return
    
    # Fetch bars
    print(f"\n5. Fetching Historical Bars...")
    try:
        import MetaTrader5 as mt5
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        tf_constant = timeframe_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        bars_data = mt5_client.copy_rates_from_pos(symbol, tf_constant, 0, 100)
        if not bars_data:
            print(f"   ❌ Failed to fetch bars for {symbol}")
            return
        
        bars = []
        for bar in bars_data:
            bars.append({
                "time": bar.get("time", 0) if isinstance(bar, dict) else bar[0],
                "open": bar.get("open", 0.0) if isinstance(bar, dict) else bar[1],
                "high": bar.get("high", 0.0) if isinstance(bar, dict) else bar[2],
                "low": bar.get("low", 0.0) if isinstance(bar, dict) else bar[3],
                "close": bar.get("close", 0.0) if isinstance(bar, dict) else bar[4],
                "volume": bar.get("tick_volume", 0) if isinstance(bar, dict) else bar[5]
            })
        
        print(f"   ✅ Fetched {len(bars)} bars")
        print(f"   Current price: {bars[-1]['close']:.5f}")
    except Exception as e:
        print(f"   ❌ Failed to fetch bars: {e}")
        return
    
    # Calculate indicators
    print(f"\n6. Calculating Technical Indicators...")
    try:
        indicators = calculate_all_indicators(bars, rules.indicators)
        if indicators:
            print(f"   ✅ Indicators calculated:")
            print(f"      EMA Fast (20): {indicators.get('ema_fast', 0):.5f}")
            print(f"      EMA Slow (50): {indicators.get('ema_slow', 0):.5f}")
            print(f"      RSI (14): {indicators.get('rsi', 0):.2f}")
            print(f"      MACD Hist: {indicators.get('macd_hist', 0):.5f}")
            print(f"      ATR: {indicators.get('atr', 0):.5f}")
        else:
            print(f"   ❌ Failed to calculate indicators")
            return
    except Exception as e:
        print(f"   ❌ Error calculating indicators: {e}")
        return
    
    # Generate facts
    print(f"\n7. Generating Facts from Indicators...")
    try:
        facts = generate_facts_from_indicators(bars, indicators, rules.indicators)
        print(f"   ✅ Facts generated:")
        for fact_name, fact_value in sorted(facts.items()):
            status = "✓" if fact_value else "✗"
            print(f"      [{status}] {fact_name}: {fact_value}")
    except Exception as e:
        print(f"   ❌ Error generating facts: {e}")
        return
    
    # Evaluate EMNR conditions
    print(f"\n8. Evaluating EMNR Conditions...")
    try:
        emnr_flags = evaluate_conditions(facts, rules.conditions)
        print(f"   ✅ EMNR Flags:")
        print(f"      Entry: {emnr_flags.get('entry', False)} {'✓' if emnr_flags.get('entry') else '✗'}")
        print(f"      Strong: {emnr_flags.get('strong', False)} {'✓' if emnr_flags.get('strong') else '✗'}")
        print(f"      Weak: {emnr_flags.get('weak', False)} {'✓' if emnr_flags.get('weak') else '✗'}")
        print(f"      Exit: {emnr_flags.get('exit', False)} {'✓' if emnr_flags.get('exit') else '✗'}")
    except Exception as e:
        print(f"   ❌ Error evaluating conditions: {e}")
        return
    
    # Calculate confidence
    print(f"\n9. Calculating Confidence Score...")
    try:
        # Check alignment
        align_ok = timeframe in profile.bestTimeframes
        
        confidence = confidence_score(emnr_flags, align_ok, news_penalty=0)
        breakdown = get_score_breakdown(emnr_flags, align_ok, news_penalty=0)
        
        print(f"   ✅ Confidence Score: {confidence}")
        print(f"   Score Breakdown:")
        print(f"      Entry: {breakdown['entry']:+d}")
        print(f"      Strong: {breakdown['strong']:+d}")
        print(f"      Weak: {breakdown['weak']:+d}")
        print(f"      Exit: {breakdown['exit']:+d}")
        print(f"      Align: {breakdown['align']:+d}")
        print(f"      News Penalty: {breakdown['news_penalty']:+d}")
        print(f"      ─────────────")
        print(f"      Raw Total: {breakdown['raw_total']}")
        print(f"      Final Score: {breakdown['final_score']}")
    except Exception as e:
        print(f"   ❌ Error calculating confidence: {e}")
        return
    
    # Calculate SL/TP
    print(f"\n10. Calculating SL/TP Levels...")
    try:
        current_price = bars[-1]['close']
        direction = rules.strategy.get("direction", "long")
        atr = indicators.get("atr", 0.0)
        atr_multiplier = profile.management.get("atrMultiplier", 1.5)
        
        if direction == "long":
            sl_price = current_price - (atr * atr_multiplier)
            tp_price = current_price + (atr * atr_multiplier * profile.style.get("rrTarget", 2.0))
        else:
            sl_price = current_price + (atr * atr_multiplier)
            tp_price = current_price - (atr * atr_multiplier * profile.style.get("rrTarget", 2.0))
        
        risk = abs(current_price - sl_price)
        reward = abs(tp_price - current_price)
        rr_ratio = reward / risk if risk > 0 else 0.0
        
        print(f"   ✅ SL/TP Calculated:")
        print(f"      Direction: {direction.upper()}")
        print(f"      Entry: {current_price:.5f}")
        print(f"      Stop Loss: {sl_price:.5f}")
        print(f"      Take Profit: {tp_price:.5f}")
        print(f"      RR Ratio: {rr_ratio:.2f}")
    except Exception as e:
        print(f"   ❌ Error calculating SL/TP: {e}")
        return
    
    # Schedule action
    print(f"\n11. Scheduling Trading Action...")
    try:
        min_rr = rules.strategy.get("min_rr", 2.0)
        min_rr_ok = rr_ratio >= min_rr
        risk_cap = profile.style.get("maxRiskPct", 0.01)
        
        execution_plan = schedule_action(confidence, min_rr_ok, risk_cap)
        action = execution_plan["action"]
        
        print(f"   ✅ Action Scheduled:")
        print(f"      Confidence: {confidence}")
        print(f"      Min RR Required: {min_rr:.2f}")
        print(f"      Actual RR: {rr_ratio:.2f}")
        print(f"      RR OK: {min_rr_ok} {'✓' if min_rr_ok else '✗'}")
        print(f"      Action: {action}")
        print(f"      Risk %: {execution_plan['riskPct']}")
        print(f"      Description: {get_action_description(action)}")
    except Exception as e:
        print(f"   ❌ Error scheduling action: {e}")
        return
    
    # Final verdict
    print(f"\n" + "=" * 80)
    print(f"FINAL VERDICT")
    print("=" * 80)
    
    if action in ("open_or_scale", "pending_only"):
        print(f"✅ TRADE IDEA WILL BE GENERATED")
        print(f"   Confidence: {confidence}")
        print(f"   Action: {action}")
        print(f"   Direction: {direction.upper()}")
        print(f"   Entry: {current_price:.5f}")
        print(f"   SL: {sl_price:.5f}")
        print(f"   TP: {tp_price:.5f}")
        print(f"   RR: {rr_ratio:.2f}")
    else:
        print(f"❌ NO TRADE IDEA GENERATED")
        print(f"   Reason: {get_action_description(action)}")
        print(f"   Confidence: {confidence} (need ≥ 60 for any action, ≥ 75 for market orders)")
        print(f"\n   What's Missing:")
        if not emnr_flags.get('entry'):
            print(f"      ❌ Entry conditions not met")
            print(f"         Required: {rules.conditions.get('entry', [])}")
        if confidence < 60:
            print(f"      ❌ Confidence too low ({confidence} < 60)")
            print(f"         Need more conditions to be TRUE")
        if confidence >= 75 and not min_rr_ok:
            print(f"      ❌ RR ratio too low ({rr_ratio:.2f} < {min_rr:.2f})")
    
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test trade idea generation")
    parser.add_argument("--symbol", default="EURUSD", help="Trading symbol (default: EURUSD)")
    parser.add_argument("--timeframe", default="H1", help="Timeframe (default: H1)")
    
    args = parser.parse_args()
    
    test_evaluation(args.symbol, args.timeframe)

