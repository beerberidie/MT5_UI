"""
Celery application configuration for background tasks.

This module configures Celery for the AI Trading Platform with Redis as the broker.
"""

from celery import Celery
from celery.schedules import crontab
import os
from pathlib import Path

# Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "ai_trader",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "backend.tasks.ai_tasks",
        "backend.tasks.data_tasks",
        "backend.tasks.maintenance_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={"master_name": "mymaster"},
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Beat schedule (periodic tasks)
    beat_schedule={
        # AI Strategy Evaluation - Every 15 minutes during trading hours
        "evaluate-ai-strategies": {
            "task": "backend.tasks.ai_tasks.evaluate_all_strategies",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
            "options": {"queue": "ai_evaluation"},
        },
        # Market Data Collection - Every 5 minutes
        "collect-market-data": {
            "task": "backend.tasks.data_tasks.collect_market_data",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
            "options": {"queue": "data_collection"},
        },
        # Economic Calendar Update - Every hour
        "update-economic-calendar": {
            "task": "backend.tasks.data_tasks.update_economic_calendar",
            "schedule": crontab(minute=0),  # Every hour at :00
            "options": {"queue": "data_collection"},
        },
        # RSS News Collection - Every 10 minutes
        "collect-rss-news": {
            "task": "backend.tasks.data_tasks.collect_rss_news",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
            "options": {"queue": "data_collection"},
        },
        # Log Cleanup - Daily at 2 AM
        "cleanup-old-logs": {
            "task": "backend.tasks.maintenance_tasks.cleanup_old_logs",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2:00 AM
            "options": {"queue": "maintenance"},
        },
        # Cache Cleanup - Daily at 3 AM
        "cleanup-cache": {
            "task": "backend.tasks.maintenance_tasks.cleanup_cache",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM
            "options": {"queue": "maintenance"},
        },
        # Trade Log Archival - Daily at 4 AM
        "archive-old-trades": {
            "task": "backend.tasks.maintenance_tasks.archive_old_trades",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4:00 AM
            "options": {"queue": "maintenance"},
        },
        # System Health Check - Every 30 minutes
        "system-health-check": {
            "task": "backend.tasks.maintenance_tasks.system_health_check",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
            "options": {"queue": "monitoring"},
        },
    },
    # Task routing
    task_routes={
        "backend.tasks.ai_tasks.*": {"queue": "ai_evaluation"},
        "backend.tasks.data_tasks.*": {"queue": "data_collection"},
        "backend.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },
)

# Optional: Configure task result backend
celery_app.conf.result_backend = REDIS_URL

if __name__ == "__main__":
    celery_app.start()
