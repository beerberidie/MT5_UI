"""
AI Trading Engine - Orchestrates all AI modules for trade evaluation.

This module coordinates:
- Fetching historical bars from MT5
- Calculating technical indicators
- Generating facts from indicators
- Evaluating EMNR conditions
- Calculating confidence scores
- Scheduling trading actions
- Creating trade ideas
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz

from backend.mt5_client import MT5Client
from backend.ai.indicators import calculate_all_indicators, generate_facts_from_indicators
from backend.ai.emnr import evaluate_conditions
from backend.ai.confidence import confidence_score
from backend.ai.scheduler import schedule_action
from backend.ai.rules_manager import load_rules
from backend.ai.symbol_profiles import load_profile
from backend.ai.ai_logger import log_decision
from backend.models import TradeIdea, EMNRFlags, IndicatorValues, ExecutionPlan
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AIEngine:
    """
    AI Trading Engine that orchestrates all AI modules.
    
    Responsibilities:
    - Fetch historical data from MT5
    - Calculate indicators
    - Evaluate EMNR conditions
    - Generate trade ideas
    - Log decisions
    """
    
    def __init__(
        self,
        mt5_client: MT5Client,
        config_dir: str = "config/ai",
        data_dir: str = "data/ai"
    ):
        """
        Initialize AI Engine.
        
        Args:
            mt5_client: MT5Client instance for fetching data
            config_dir: Directory containing AI configuration files
            data_dir: Directory for AI data (logs, indicators)
        """
        self.mt5_client = mt5_client
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        
        # Load global settings
        settings_path = self.config_dir / "settings.json"
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "enabled": True,
                "mode": "semi-auto",
                "confidence_threshold": 75,
                "min_rr_ratio": 2.0,
                "max_concurrent_positions": 3,
                "max_positions_per_symbol": 1,
                "default_risk_pct": 0.01,
                "news_embargo_minutes": 30,
                "timezone": "Africa/Johannesburg"
            }
        
        self.timezone = pytz.timezone(self.settings.get("timezone", "Africa/Johannesburg"))
        logger.info(f"AI Engine initialized with config_dir={config_dir}, data_dir={data_dir}")
    
    def evaluate(
        self,
        symbol: str,
        timeframe: str = "H1",
        force: bool = False
    ) -> Optional[TradeIdea]:
        """
        Evaluate a symbol and generate a trade idea if conditions are met.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Timeframe for analysis (e.g., "H1", "M15")
            force: Force evaluation even if AI is disabled
            
        Returns:
            TradeIdea if conditions are met, None otherwise
        """
        try:
            # Check if AI is enabled
            if not self.settings.get("enabled", True) and not force:
                logger.info(f"AI evaluation skipped for {symbol} - AI is disabled")
                return None
            
            # Load EMNR rules for this symbol/timeframe
            rules = load_rules(
                str(self.config_dir / "strategies"),
                symbol,
                timeframe
            )
            if not rules:
                logger.warning(f"No EMNR rules found for {symbol} {timeframe}")
                return None
            
            # Load symbol profile
            profile = load_profile(
                str(self.config_dir / "profiles"),
                symbol
            )
            if not profile:
                logger.warning(f"No profile found for {symbol}")
                return None
            
            # Fetch historical bars
            bars = self._fetch_bars(symbol, timeframe, count=100)
            if not bars or len(bars) < 50:
                logger.warning(f"Insufficient bars for {symbol} {timeframe}: {len(bars) if bars else 0}")
                return None
            
            # Calculate indicators
            indicators = calculate_all_indicators(bars, rules.indicators)
            if not indicators:
                logger.warning(f"Failed to calculate indicators for {symbol}")
                return None
            
            # Generate facts from indicators
            facts = generate_facts_from_indicators(bars, indicators, rules.indicators)
            
            # Evaluate EMNR conditions
            emnr_flags = evaluate_conditions(facts, rules.conditions)
            
            # Check alignment (session, timeframe, bias)
            align_ok = self._check_alignment(symbol, timeframe, profile, rules)
            
            # Calculate confidence score
            news_penalty = 0  # TODO: Implement news calendar check
            confidence = confidence_score(emnr_flags, align_ok, news_penalty)
            
            # Determine direction from strategy
            direction = rules.strategy.get("direction", "long")
            
            # Calculate SL/TP levels
            current_price = bars[-1]["close"]
            sl_price, tp_price, rr_ratio = self._calculate_sl_tp(
                current_price,
                direction,
                indicators,
                profile,
                rules
            )
            
            # Check if RR meets minimum
            min_rr_ok = rr_ratio >= rules.strategy.get("min_rr", 2.0)
            
            # Schedule action
            risk_cap = profile.style.get("maxRiskPct", 0.01)
            execution_plan = schedule_action(confidence, min_rr_ok, risk_cap)
            
            # Create trade idea
            trade_idea = TradeIdea(
                id=f"{symbol}_{timeframe}_{datetime.now(self.timezone).strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(self.timezone).isoformat(),
                symbol=symbol,
                timeframe=timeframe,
                confidence=confidence,
                action=execution_plan["action"],
                direction=direction,
                entry_price=current_price,
                stop_loss=sl_price,
                take_profit=tp_price,
                volume=0.01,  # Will be calculated based on risk
                rr_ratio=rr_ratio,
                emnr_flags=EMNRFlags(**emnr_flags),
                indicators=IndicatorValues(**{k: v for k, v in indicators.items() if k in IndicatorValues.__annotations__}),
                execution_plan=ExecutionPlan(**execution_plan),
                status="pending_approval"
            )
            
            # Log decision
            log_path = self.data_dir / "indicators" / f"{symbol}_decisions.csv"
            log_decision(str(log_path), {
                "timestamp": trade_idea.timestamp,
                "symbol": symbol,
                "timeframe": timeframe,
                "confidence": confidence,
                "action": execution_plan["action"],
                "direction": direction,
                "entry": current_price,
                "sl": sl_price,
                "tp": tp_price,
                "rr": rr_ratio
            })
            
            logger.info(f"Trade idea generated for {symbol}: confidence={confidence}, action={execution_plan['action']}")
            return trade_idea
            
        except Exception as e:
            logger.error(f"Error evaluating {symbol}: {e}", exc_info=True)
            return None
    
    def _fetch_bars(self, symbol: str, timeframe: str, count: int = 100) -> Optional[List[Dict]]:
        """Fetch historical bars from MT5."""
        try:
            # Import MT5 timeframe constants
            try:
                import MetaTrader5 as mt5
                # Map timeframe string to MT5 timeframe constant
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
            except ImportError:
                logger.error("MetaTrader5 module not available")
                return None

            # Fetch bars using MT5Client
            bars_data = self.mt5_client.copy_rates_from_pos(symbol, tf_constant, 0, count)
            if not bars_data:
                return None

            # Convert to list of dicts with OHLC structure
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

            return bars

        except Exception as e:
            logger.error(f"Error fetching bars for {symbol}: {e}")
            return None
    
    def _check_alignment(self, symbol: str, timeframe: str, profile, rules) -> bool:
        """Check if current conditions align with profile and rules."""
        try:
            # Check if timeframe is in best timeframes
            if timeframe not in profile.bestTimeframes:
                return False
            
            # Check if current session is in best sessions
            current_session = self._get_current_session()
            if current_session not in profile.bestSessions and current_session not in rules.sessions:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking alignment: {e}")
            return False
    
    def _get_current_session(self) -> str:
        """Determine current trading session based on time."""
        now = datetime.now(self.timezone)
        hour = now.hour
        
        # SAST timezone sessions
        if 9 <= hour < 17:
            return "London"
        elif 15 <= hour < 23:
            return "NewYork"
        elif 2 <= hour < 10:
            return "Tokyo"
        else:
            return "Sydney"
    
    def _calculate_sl_tp(
        self,
        entry_price: float,
        direction: str,
        indicators: Dict,
        profile,
        rules
    ) -> Tuple[float, float, float]:
        """Calculate stop loss and take profit levels."""
        try:
            # Use ATR for SL/TP calculation
            atr = indicators.get("atr", 0.0)
            atr_multiplier = profile.management.get("atrMultiplier", 1.5)
            
            if direction == "long":
                sl_price = entry_price - (atr * atr_multiplier)
                tp_price = entry_price + (atr * atr_multiplier * profile.style.get("rrTarget", 2.0))
            else:  # short
                sl_price = entry_price + (atr * atr_multiplier)
                tp_price = entry_price - (atr * atr_multiplier * profile.style.get("rrTarget", 2.0))
            
            # Calculate RR ratio
            risk = abs(entry_price - sl_price)
            reward = abs(tp_price - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0.0
            
            return round(sl_price, 5), round(tp_price, 5), round(rr_ratio, 2)
            
        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            # Fallback to simple percentage-based SL/TP
            if direction == "long":
                sl_price = entry_price * 0.99
                tp_price = entry_price * 1.02
            else:
                sl_price = entry_price * 1.01
                tp_price = entry_price * 0.98
            return round(sl_price, 5), round(tp_price, 5), 2.0

