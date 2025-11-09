"""
Background tasks package for AI Trading Platform.

This package contains Celery tasks for:
- AI strategy evaluation
- Data collection
- Maintenance operations
"""

from backend.tasks.ai_tasks import (
    evaluate_all_strategies,
    evaluate_single_symbol,
    backtest_strategy
)

from backend.tasks.data_tasks import (
    collect_market_data,
    update_economic_calendar,
    collect_rss_news,
    update_symbol_info
)

from backend.tasks.maintenance_tasks import (
    cleanup_old_logs,
    cleanup_cache,
    archive_old_trades,
    system_health_check,
    optimize_csv_files
)

__all__ = [
    # AI tasks
    "evaluate_all_strategies",
    "evaluate_single_symbol",
    "backtest_strategy",
    
    # Data tasks
    "collect_market_data",
    "update_economic_calendar",
    "collect_rss_news",
    "update_symbol_info",
    
    # Maintenance tasks
    "cleanup_old_logs",
    "cleanup_cache",
    "archive_old_trades",
    "system_health_check",
    "optimize_csv_files",
]

