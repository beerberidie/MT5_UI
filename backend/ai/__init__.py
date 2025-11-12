"""
AI Trading Module

This module provides autonomous trading capabilities including:
- EMNR (Entry/Exit/Strong/Weak) rule evaluation
- Confidence scoring (0-100 scale)
- Action scheduling based on confidence thresholds
- Technical indicator calculations
- Symbol profile management
- Strategy rule management
"""

__version__ = "1.0.0"

from .emnr import evaluate_conditions
from .confidence import confidence_score
from .scheduler import schedule_action

__all__ = [
    "evaluate_conditions",
    "confidence_score",
    "schedule_action",
]
