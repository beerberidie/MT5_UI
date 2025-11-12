"""
Symbol Profile Management

Handles loading, saving, and validation of symbol-specific trading profiles.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class SymbolProfile:
    """Symbol trading profile with best sessions, timeframes, and risk parameters."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize symbol profile from dictionary.

        Args:
            data: Profile data dictionary
        """
        self.symbol = data.get("symbol", "")
        self.best_sessions = data.get("bestSessions", [])
        self.best_timeframes = data.get("bestTimeframes", [])
        self.external_drivers = data.get("externalDrivers", [])

        style = data.get("style", {})
        self.bias = style.get("bias", "trend-follow")
        self.rr_target = style.get("rrTarget", 2.0)
        self.max_risk_pct = style.get("maxRiskPct", 0.01)

        management = data.get("management", {})
        self.breakeven_after_rr = management.get("breakevenAfterRR", 1.0)
        self.partial_at_rr = management.get("partialAtRR", 1.5)
        self.trail_using_atr = management.get("trailUsingATR", True)
        self.atr_multiplier = management.get("atrMultiplier", 1.5)

        self.invalidations = data.get("invalidations", [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "symbol": self.symbol,
            "bestSessions": self.best_sessions,
            "bestTimeframes": self.best_timeframes,
            "externalDrivers": self.external_drivers,
            "style": {
                "bias": self.bias,
                "rrTarget": self.rr_target,
                "maxRiskPct": self.max_risk_pct,
            },
            "management": {
                "breakevenAfterRR": self.breakeven_after_rr,
                "partialAtRR": self.partial_at_rr,
                "trailUsingATR": self.trail_using_atr,
                "atrMultiplier": self.atr_multiplier,
            },
            "invalidations": self.invalidations,
        }


def load_profile(profiles_dir: Path, symbol: str) -> Optional[SymbolProfile]:
    """
    Load symbol profile from JSON file.

    Args:
        profiles_dir: Directory containing profile JSON files
        symbol: Symbol name (e.g., 'EURUSD')

    Returns:
        SymbolProfile object or None if not found

    Example:
        >>> from pathlib import Path
        >>> profile = load_profile(Path('config/ai/profiles'), 'EURUSD')
        >>> profile.symbol if profile else None
        'EURUSD'
    """
    # Convert to Path if string
    profiles_dir_path = (
        Path(profiles_dir) if isinstance(profiles_dir, str) else profiles_dir
    )
    profile_path = profiles_dir_path / f"{symbol}.json"

    if not profile_path.exists():
        return None

    try:
        with open(profile_path, "r") as f:
            data = json.load(f)
        return SymbolProfile(data)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading profile for {symbol}: {e}")
        return None


def save_profile(profiles_dir: Path, profile: SymbolProfile) -> bool:
    """
    Save symbol profile to JSON file.

    Args:
        profiles_dir: Directory to save profile JSON files
        profile: SymbolProfile object to save

    Returns:
        True if successful, False otherwise
    """
    # Convert to Path if string
    profiles_dir_path = (
        Path(profiles_dir) if isinstance(profiles_dir, str) else profiles_dir
    )
    profiles_dir_path.mkdir(parents=True, exist_ok=True)
    profile_path = profiles_dir_path / f"{profile.symbol}.json"

    try:
        with open(profile_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving profile for {profile.symbol}: {e}")
        return False


def delete_profile(profiles_dir: Path, symbol: str) -> bool:
    """
    Delete symbol profile.

    Args:
        profiles_dir: Directory containing profile JSON files
        symbol: Symbol name

    Returns:
        True if deleted, False if not found or error
    """
    profile_path = profiles_dir / f"{symbol}.json"

    if not profile_path.exists():
        return False

    try:
        profile_path.unlink()
        return True
    except IOError as e:
        print(f"Error deleting profile for {symbol}: {e}")
        return False


def list_profiles(profiles_dir: Path) -> List[str]:
    """
    List all available symbol profiles.

    Args:
        profiles_dir: Directory containing profile JSON files

    Returns:
        List of symbol names
    """
    if not profiles_dir.exists():
        return []

    profiles = []
    for path in profiles_dir.glob("*.json"):
        symbol = path.stem
        profiles.append(symbol)

    return sorted(profiles)


def create_default_profile(symbol: str) -> SymbolProfile:
    """
    Create a default profile for a symbol.

    Args:
        symbol: Symbol name

    Returns:
        SymbolProfile with default settings
    """
    default_data = {
        "symbol": symbol,
        "bestSessions": ["London", "NewYork"],
        "bestTimeframes": ["M15", "H1", "H4"],
        "externalDrivers": [],
        "style": {"bias": "trend-follow", "rrTarget": 2.0, "maxRiskPct": 0.01},
        "management": {
            "breakevenAfterRR": 1.0,
            "partialAtRR": 1.5,
            "trailUsingATR": True,
            "atrMultiplier": 1.5,
        },
        "invalidations": [],
    }

    return SymbolProfile(default_data)


def validate_profile(profile: SymbolProfile) -> List[str]:
    """
    Validate profile data.

    Args:
        profile: SymbolProfile to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not profile.symbol:
        errors.append("Symbol name is required")

    if profile.rr_target < 1.0:
        errors.append("RR target must be >= 1.0")

    if not (0 < profile.max_risk_pct <= 0.1):
        errors.append("Max risk percentage must be between 0 and 0.1 (10%)")

    if profile.breakeven_after_rr < 0:
        errors.append("Breakeven after RR must be >= 0")

    if profile.partial_at_rr < 0:
        errors.append("Partial at RR must be >= 0")

    if profile.atr_multiplier <= 0:
        errors.append("ATR multiplier must be > 0")

    valid_sessions = ["London", "NewYork", "Tokyo", "Sydney"]
    for session in profile.best_sessions:
        if session not in valid_sessions:
            errors.append(f"Invalid session: {session}")

    valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    for tf in profile.best_timeframes:
        if tf not in valid_timeframes:
            errors.append(f"Invalid timeframe: {tf}")

    return errors
