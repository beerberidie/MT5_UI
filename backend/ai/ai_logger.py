"""
AI Decision Logger

Logs AI trading decisions to CSV for audit trail and analysis.
"""

import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


def log_decision(log_path: Path, decision: Dict[str, Any]) -> bool:
    """
    Log an AI decision to CSV file.

    Args:
        log_path: Path to CSV log file
        decision: Dictionary with decision data

    Returns:
        True if successful, False otherwise

    Expected decision fields:
        - timestamp: ISO format timestamp
        - symbol: Symbol name
        - timeframe: Timeframe
        - confidence: Confidence score (0-100)
        - action: Action taken (observe, pending_only, wait_rr, open_or_scale)
        - entry: Entry flag (True/False)
        - exit: Exit flag (True/False)
        - strong: Strong flag (True/False)
        - weak: Weak flag (True/False)
        - align_ok: Alignment flag (True/False)
        - rr_ratio: Risk/reward ratio
        - status: Status (pending_approval, approved, rejected, executed)
        - trade_id: Trade ID (if executed)
        - notes: Additional notes
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists to determine if we need to write headers
    file_exists = log_path.exists()

    fieldnames = [
        "timestamp",
        "symbol",
        "timeframe",
        "confidence",
        "action",
        "entry",
        "exit",
        "strong",
        "weak",
        "align_ok",
        "rr_ratio",
        "status",
        "trade_id",
        "notes",
    ]

    try:
        with open(log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            # Ensure all fields are present
            row = {field: decision.get(field, "") for field in fieldnames}
            writer.writerow(row)

        return True
    except IOError as e:
        print(f"Error logging decision: {e}")
        return False


def get_decisions(
    log_path: Path, symbol: Optional[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve recent AI decisions from log.

    Args:
        log_path: Path to CSV log file
        symbol: Optional symbol filter
        limit: Maximum number of decisions to return

    Returns:
        List of decision dictionaries (most recent first)
    """
    # Convert to Path if string
    log_path_obj = Path(log_path) if isinstance(log_path, str) else log_path
    if not log_path_obj.exists():
        return []

    try:
        with open(log_path_obj, "r") as f:
            reader = csv.DictReader(f)
            decisions = list(reader)

        # Filter by symbol if specified
        if symbol:
            decisions = [d for d in decisions if d.get("symbol") == symbol]

        # Return most recent first
        decisions.reverse()

        return decisions[:limit]
    except (IOError, csv.Error) as e:
        print(f"Error reading decisions: {e}")
        return []


def get_decision_stats(
    log_path: Path, symbol: Optional[str] = None, days: int = 7
) -> Dict[str, Any]:
    """
    Get statistics on AI decisions.

    Args:
        log_path: Path to CSV log file
        symbol: Optional symbol filter
        days: Number of days to analyze

    Returns:
        Dictionary with statistics
    """
    if not log_path.exists():
        return {
            "total_decisions": 0,
            "by_action": {},
            "by_status": {},
            "avg_confidence": 0,
            "avg_rr_ratio": 0,
        }

    try:
        with open(log_path, "r") as f:
            reader = csv.DictReader(f)
            decisions = list(reader)

        # Filter by symbol if specified
        if symbol:
            decisions = [d for d in decisions if d.get("symbol") == symbol]

        # Filter by date range
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
        recent_decisions = []
        for d in decisions:
            try:
                ts = datetime.fromisoformat(d.get("timestamp", "")).timestamp()
                if ts >= cutoff:
                    recent_decisions.append(d)
            except (ValueError, AttributeError):
                continue

        # Calculate statistics
        total = len(recent_decisions)

        by_action = {}
        by_status = {}
        confidences = []
        rr_ratios = []

        for d in recent_decisions:
            action = d.get("action", "unknown")
            by_action[action] = by_action.get(action, 0) + 1

            status = d.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            try:
                conf = float(d.get("confidence", 0))
                confidences.append(conf)
            except (ValueError, TypeError):
                pass

            try:
                rr = float(d.get("rr_ratio", 0))
                if rr > 0:
                    rr_ratios.append(rr)
            except (ValueError, TypeError):
                pass

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0

        return {
            "total_decisions": total,
            "by_action": by_action,
            "by_status": by_status,
            "avg_confidence": round(avg_confidence, 2),
            "avg_rr_ratio": round(avg_rr, 2),
        }
    except (IOError, csv.Error) as e:
        print(f"Error calculating stats: {e}")
        return {
            "total_decisions": 0,
            "by_action": {},
            "by_status": {},
            "avg_confidence": 0,
            "avg_rr_ratio": 0,
        }


def clear_old_decisions(log_path: Path, days_to_keep: int = 30) -> int:
    """
    Remove decisions older than specified days.

    Args:
        log_path: Path to CSV log file
        days_to_keep: Number of days to keep

    Returns:
        Number of decisions removed
    """
    if not log_path.exists():
        return 0

    try:
        with open(log_path, "r") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            decisions = list(reader)

        cutoff = datetime.now(timezone.utc).timestamp() - (days_to_keep * 86400)

        kept_decisions = []
        removed_count = 0

        for d in decisions:
            try:
                ts = datetime.fromisoformat(d.get("timestamp", "")).timestamp()
                if ts >= cutoff:
                    kept_decisions.append(d)
                else:
                    removed_count += 1
            except (ValueError, AttributeError):
                # Keep decisions with invalid timestamps
                kept_decisions.append(d)

        # Write back kept decisions
        with open(log_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept_decisions)

        return removed_count
    except (IOError, csv.Error) as e:
        print(f"Error clearing old decisions: {e}")
        return 0
