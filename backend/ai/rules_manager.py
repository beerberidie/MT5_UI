"""
EMNR Rules Management

Handles loading, saving, and validation of EMNR strategy rules.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class EMNRRules:
    """EMNR strategy rules for a symbol/timeframe combination."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize EMNR rules from dictionary.

        Args:
            data: Rules data dictionary
        """
        self.symbol = data.get("symbol", "")
        self.timeframe = data.get("timeframe", "H1")
        self.sessions = data.get("sessions", [])

        self.indicators = data.get("indicators", {})
        self.conditions = data.get(
            "conditions", {"entry": [], "exit": [], "strong": [], "weak": []}
        )

        strategy = data.get("strategy", {})
        self.direction = strategy.get("direction", "long")
        self.min_rr = strategy.get("min_rr", 2.0)
        self.news_embargo_minutes = strategy.get("news_embargo_minutes", 30)
        self.invalidations = strategy.get("invalidations", [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert rules to dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "sessions": self.sessions,
            "indicators": self.indicators,
            "conditions": self.conditions,
            "strategy": {
                "direction": self.direction,
                "min_rr": self.min_rr,
                "news_embargo_minutes": self.news_embargo_minutes,
                "invalidations": self.invalidations,
            },
        }


def load_rules(
    rules_dir: Path, symbol: str, timeframe: str = "H1"
) -> Optional[EMNRRules]:
    """
    Load EMNR rules from JSON file.

    Args:
        rules_dir: Directory containing rules JSON files
        symbol: Symbol name (e.g., 'EURUSD')
        timeframe: Timeframe (e.g., 'H1')

    Returns:
        EMNRRules object or None if not found

    Example:
        >>> from pathlib import Path
        >>> rules = load_rules(Path('config/ai/strategies'), 'EURUSD', 'H1')
        >>> rules.symbol if rules else None
        'EURUSD'
    """
    # Convert to Path if string
    rules_dir_path = Path(rules_dir) if isinstance(rules_dir, str) else rules_dir
    rules_path = rules_dir_path / f"{symbol}_{timeframe}.json"

    if not rules_path.exists():
        return None

    try:
        with open(rules_path, "r") as f:
            data = json.load(f)
        return EMNRRules(data)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading rules for {symbol} {timeframe}: {e}")
        return None


def save_rules(rules_dir: Path, symbol: str, rules: EMNRRules) -> bool:
    """
    Save EMNR rules to JSON file.

    Args:
        rules_dir: Directory to save rules JSON files
        symbol: Symbol name
        rules: EMNRRules object to save

    Returns:
        True if successful, False otherwise
    """
    # Convert to Path if string
    rules_dir_path = Path(rules_dir) if isinstance(rules_dir, str) else rules_dir
    rules_dir_path.mkdir(parents=True, exist_ok=True)
    rules_path = rules_dir_path / f"{symbol}_{rules.timeframe}.json"

    try:
        with open(rules_path, "w") as f:
            json.dump(rules.to_dict(), f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving rules for {symbol} {rules.timeframe}: {e}")
        return False


def delete_rules(rules_dir: Path, symbol: str, timeframe: str = "H1") -> bool:
    """
    Delete EMNR rules.

    Args:
        rules_dir: Directory containing rules JSON files
        symbol: Symbol name
        timeframe: Timeframe

    Returns:
        True if deleted, False if not found or error
    """
    # Convert to Path if string
    rules_dir_path = Path(rules_dir) if isinstance(rules_dir, str) else rules_dir
    rules_path = rules_dir_path / f"{symbol}_{timeframe}.json"

    if not rules_path.exists():
        return False

    try:
        rules_path.unlink()
        return True
    except IOError as e:
        print(f"Error deleting rules for {symbol} {timeframe}: {e}")
        return False


def list_rules(rules_dir: Path) -> List[Dict[str, str]]:
    """
    List all available strategy rules.

    Args:
        rules_dir: Directory containing rules JSON files

    Returns:
        List of dictionaries with 'symbol' and 'timeframe' keys
    """
    if not rules_dir.exists():
        return []

    rules_list = []
    for path in rules_dir.glob("*.json"):
        # Parse filename: SYMBOL_TIMEFRAME.json
        parts = path.stem.split("_")
        if len(parts) >= 2:
            symbol = "_".join(parts[:-1])  # Handle symbols with underscores
            timeframe = parts[-1]
            rules_list.append({"symbol": symbol, "timeframe": timeframe})

    return sorted(rules_list, key=lambda x: (x["symbol"], x["timeframe"]))


def validate_rules(rules: EMNRRules) -> List[str]:
    """
    Validate EMNR rules.

    Args:
        rules: EMNRRules to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not rules.symbol:
        errors.append("Symbol name is required")

    if not rules.timeframe:
        errors.append("Timeframe is required")

    valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    if rules.timeframe not in valid_timeframes:
        errors.append(f"Invalid timeframe: {rules.timeframe}")

    if rules.direction not in ["long", "short"]:
        errors.append(f"Direction must be 'long' or 'short', got: {rules.direction}")

    if rules.min_rr < 1.0:
        errors.append("Minimum RR must be >= 1.0")

    if rules.news_embargo_minutes < 0:
        errors.append("News embargo minutes must be >= 0")

    # Validate conditions structure
    required_condition_keys = {"entry", "exit", "strong", "weak"}
    if not required_condition_keys.issubset(rules.conditions.keys()):
        errors.append("Conditions must have entry, exit, strong, weak keys")

    for key in required_condition_keys:
        if key in rules.conditions:
            if not isinstance(rules.conditions[key], list):
                errors.append(f"Condition '{key}' must be a list")

    # Validate indicators structure
    if not isinstance(rules.indicators, dict):
        errors.append("Indicators must be a dictionary")

    # Validate sessions
    valid_sessions = ["London", "NewYork", "Tokyo", "Sydney"]
    for session in rules.sessions:
        if session not in valid_sessions:
            errors.append(f"Invalid session: {session}")

    return errors


def create_default_rules(symbol: str, timeframe: str = "H1") -> EMNRRules:
    """
    Create default EMNR rules for a symbol.

    Args:
        symbol: Symbol name
        timeframe: Timeframe (default 'H1')

    Returns:
        EMNRRules with default settings
    """
    default_data = {
        "symbol": symbol,
        "timeframe": timeframe,
        "sessions": ["London", "NewYork"],
        "indicators": {
            "ema": {"fast": 20, "slow": 50},
            "rsi": {"period": 14, "overbought": 70, "oversold": 30},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "atr": {"period": 14, "multiplier": 1.5},
        },
        "conditions": {
            "entry": ["ema_fast_gt_slow", "rsi_between_40_60"],
            "exit": ["rsi_gt_70"],
            "strong": ["macd_hist_gt_0"],
            "weak": ["long_upper_wick"],
        },
        "strategy": {
            "direction": "long",
            "min_rr": 2.0,
            "news_embargo_minutes": 30,
            "invalidations": ["price_close_lt_ema_slow"],
        },
    }

    return EMNRRules(default_data)
