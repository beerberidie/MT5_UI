"""
Test script to verify Celery imports and configuration.

This script tests:
1. Celery app can be imported
2. All tasks can be imported
3. Task routes can be imported
4. No import errors or circular dependencies
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("  Celery Import Test")
print("=" * 60)
print()

# Test 1: Import Celery app
print("[1/5] Testing Celery app import...")
try:
    from backend.celery_app import celery_app
    print("  ✓ Celery app imported successfully")
    print(f"  - App name: {celery_app.main}")
    print(f"  - Broker: {celery_app.conf.broker_url}")
except Exception as e:
    print(f"  ✗ Failed to import Celery app: {e}")
    sys.exit(1)

# Test 2: Import AI tasks
print()
print("[2/5] Testing AI tasks import...")
try:
    from backend.tasks.ai_tasks import (
        evaluate_all_strategies,
        evaluate_single_symbol,
        backtest_strategy
    )
    print("  ✓ AI tasks imported successfully")
    print(f"  - evaluate_all_strategies: {evaluate_all_strategies.name}")
    print(f"  - evaluate_single_symbol: {evaluate_single_symbol.name}")
    print(f"  - backtest_strategy: {backtest_strategy.name}")
except Exception as e:
    print(f"  ✗ Failed to import AI tasks: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import data tasks
print()
print("[3/5] Testing data tasks import...")
try:
    from backend.tasks.data_tasks import (
        collect_market_data,
        update_economic_calendar,
        collect_rss_news,
        update_symbol_info
    )
    print("  ✓ Data tasks imported successfully")
    print(f"  - collect_market_data: {collect_market_data.name}")
    print(f"  - update_economic_calendar: {update_economic_calendar.name}")
    print(f"  - collect_rss_news: {collect_rss_news.name}")
    print(f"  - update_symbol_info: {update_symbol_info.name}")
except Exception as e:
    print(f"  ✗ Failed to import data tasks: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Import maintenance tasks
print()
print("[4/5] Testing maintenance tasks import...")
try:
    from backend.tasks.maintenance_tasks import (
        cleanup_old_logs,
        cleanup_cache,
        archive_old_trades,
        system_health_check,
        optimize_csv_files
    )
    print("  ✓ Maintenance tasks imported successfully")
    print(f"  - cleanup_old_logs: {cleanup_old_logs.name}")
    print(f"  - cleanup_cache: {cleanup_cache.name}")
    print(f"  - archive_old_trades: {archive_old_trades.name}")
    print(f"  - system_health_check: {system_health_check.name}")
    print(f"  - optimize_csv_files: {optimize_csv_files.name}")
except Exception as e:
    print(f"  ✗ Failed to import maintenance tasks: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Import Celery routes
print()
print("[5/5] Testing Celery routes import...")
try:
    from backend.celery_routes import router
    print("  ✓ Celery routes imported successfully")
    print(f"  - Router prefix: {router.prefix}")
    print(f"  - Number of routes: {len(router.routes)}")
except Exception as e:
    print(f"  ✗ Failed to import Celery routes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print()
print("=" * 60)
print("  All imports successful! ✓")
print("=" * 60)
print()
print("Registered tasks:")
print("-" * 60)

# List all registered tasks
for task_name in sorted(celery_app.tasks.keys()):
    if not task_name.startswith('celery.'):
        print(f"  - {task_name}")

print()
print("Beat schedule:")
print("-" * 60)

# List scheduled tasks
for schedule_name, schedule_config in celery_app.conf.beat_schedule.items():
    task_name = schedule_config['task']
    schedule = schedule_config['schedule']
    print(f"  - {schedule_name}")
    print(f"    Task: {task_name}")
    print(f"    Schedule: {schedule}")
    print()

print("=" * 60)
print("  Celery configuration is valid!")
print("=" * 60)

