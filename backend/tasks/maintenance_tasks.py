"""
Maintenance background tasks for Celery.

This module contains tasks for:
- Log file cleanup
- Cache cleanup
- Trade log archival
- System health checks
- Database optimization
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import os

from backend.celery_app import celery_app
from backend.storage.file_storage import FileStorage
from backend.mt5_client import MT5Client

logger = logging.getLogger(__name__)


@celery_app.task(name="backend.tasks.maintenance_tasks.cleanup_old_logs", bind=True)
def cleanup_old_logs(self, days_to_keep: int = 30):
    """
    Clean up log files older than specified days.

    Args:
        days_to_keep: Number of days to keep logs (default: 30)

    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Starting log cleanup task (keeping {days_to_keep} days)")

        logs_dir = Path("logs")
        if not logs_dir.exists():
            return {
                "success": True,
                "message": "Logs directory does not exist",
                "files_deleted": 0,
            }

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        files_deleted = 0
        bytes_freed = 0

        # Scan log files
        for log_file in logs_dir.glob("*.log*"):
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                if file_mtime < cutoff_date:
                    file_size = log_file.stat().st_size
                    log_file.unlink()
                    files_deleted += 1
                    bytes_freed += file_size
                    logger.info(f"Deleted old log file: {log_file.name}")

            except Exception as e:
                logger.error(f"Error deleting {log_file}: {e}")

        logger.info(
            f"Log cleanup complete: {files_deleted} files deleted, "
            f"{bytes_freed / 1024 / 1024:.2f} MB freed"
        )

        return {
            "success": True,
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed,
            "mb_freed": round(bytes_freed / 1024 / 1024, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in cleanup_old_logs task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.maintenance_tasks.cleanup_cache", bind=True)
def cleanup_cache(self, days_to_keep: int = 7):
    """
    Clean up cache files older than specified days.

    Args:
        days_to_keep: Number of days to keep cache (default: 7)

    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Starting cache cleanup task (keeping {days_to_keep} days)")

        cache_dir = Path("data/cache")
        if not cache_dir.exists():
            return {
                "success": True,
                "message": "Cache directory does not exist",
                "files_deleted": 0,
            }

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        files_deleted = 0
        bytes_freed = 0

        # Scan cache files
        for cache_file in cache_dir.rglob("*"):
            if not cache_file.is_file():
                continue

            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)

                if file_mtime < cutoff_date:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    files_deleted += 1
                    bytes_freed += file_size
                    logger.info(f"Deleted old cache file: {cache_file.name}")

            except Exception as e:
                logger.error(f"Error deleting {cache_file}: {e}")

        logger.info(
            f"Cache cleanup complete: {files_deleted} files deleted, "
            f"{bytes_freed / 1024 / 1024:.2f} MB freed"
        )

        return {
            "success": True,
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed,
            "mb_freed": round(bytes_freed / 1024 / 1024, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in cleanup_cache task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.maintenance_tasks.archive_old_trades", bind=True)
def archive_old_trades(self, days_to_keep: int = 90):
    """
    Archive trade logs older than specified days.

    Args:
        days_to_keep: Number of days to keep in active logs (default: 90)

    Returns:
        Dict with archival results
    """
    try:
        logger.info(f"Starting trade log archival task (keeping {days_to_keep} days)")

        logs_dir = Path("logs")
        archive_dir = Path("logs/archive")
        archive_dir.mkdir(parents=True, exist_ok=True)

        if not logs_dir.exists():
            return {
                "success": True,
                "message": "Logs directory does not exist",
                "files_archived": 0,
            }

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        files_archived = 0

        # Find trade log files
        for log_file in logs_dir.glob("trades_*.csv"):
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

                if file_mtime < cutoff_date:
                    # Move to archive
                    archive_path = archive_dir / log_file.name
                    shutil.move(str(log_file), str(archive_path))
                    files_archived += 1
                    logger.info(f"Archived trade log: {log_file.name}")

            except Exception as e:
                logger.error(f"Error archiving {log_file}: {e}")

        logger.info(f"Trade log archival complete: {files_archived} files archived")

        return {
            "success": True,
            "files_archived": files_archived,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in archive_old_trades task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.maintenance_tasks.system_health_check", bind=True)
def system_health_check(self):
    """
    Perform system health check.

    This task:
    1. Checks MT5 connection
    2. Checks disk space
    3. Checks log file sizes
    4. Checks cache sizes
    5. Reports any issues

    Returns:
        Dict with health check results
    """
    try:
        logger.info("Starting system health check task")

        health_status = {
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {},
            "warnings": [],
            "errors": [],
        }

        # Check MT5 connection
        try:
            mt5_client = MT5Client()
            if mt5_client.connect():
                health_status["checks"]["mt5_connection"] = "OK"
                mt5_client.disconnect()
            else:
                health_status["checks"]["mt5_connection"] = "FAILED"
                health_status["errors"].append("MT5 connection failed")
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["mt5_connection"] = "ERROR"
            health_status["errors"].append(f"MT5 check error: {str(e)}")
            health_status["status"] = "unhealthy"

        # Check disk space
        try:
            disk_usage = shutil.disk_usage(".")
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            percent_free = (disk_usage.free / disk_usage.total) * 100

            health_status["checks"]["disk_space"] = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_free": round(percent_free, 2),
            }

            if percent_free < 10:
                health_status["errors"].append(
                    f"Low disk space: {percent_free:.1f}% free"
                )
                health_status["status"] = "unhealthy"
            elif percent_free < 20:
                health_status["warnings"].append(
                    f"Disk space warning: {percent_free:.1f}% free"
                )
                if health_status["status"] == "healthy":
                    health_status["status"] = "warning"

        except Exception as e:
            health_status["checks"]["disk_space"] = "ERROR"
            health_status["errors"].append(f"Disk space check error: {str(e)}")

        # Check log directory size
        try:
            logs_dir = Path("logs")
            if logs_dir.exists():
                total_size = sum(
                    f.stat().st_size for f in logs_dir.rglob("*") if f.is_file()
                )
                size_mb = total_size / (1024**2)

                health_status["checks"]["logs_size_mb"] = round(size_mb, 2)

                if size_mb > 1000:  # 1 GB
                    health_status["warnings"].append(
                        f"Large logs directory: {size_mb:.1f} MB"
                    )
                    if health_status["status"] == "healthy":
                        health_status["status"] = "warning"
        except Exception as e:
            health_status["checks"]["logs_size"] = "ERROR"
            health_status["warnings"].append(f"Logs size check error: {str(e)}")

        # Check cache directory size
        try:
            cache_dir = Path("data/cache")
            if cache_dir.exists():
                total_size = sum(
                    f.stat().st_size for f in cache_dir.rglob("*") if f.is_file()
                )
                size_mb = total_size / (1024**2)

                health_status["checks"]["cache_size_mb"] = round(size_mb, 2)

                if size_mb > 500:  # 500 MB
                    health_status["warnings"].append(
                        f"Large cache directory: {size_mb:.1f} MB"
                    )
                    if health_status["status"] == "healthy":
                        health_status["status"] = "warning"
        except Exception as e:
            health_status["checks"]["cache_size"] = "ERROR"
            health_status["warnings"].append(f"Cache size check error: {str(e)}")

        # Store health check results
        _store_health_check(health_status)

        logger.info(f"System health check complete: {health_status['status']}")

        return health_status

    except Exception as e:
        logger.error(f"Error in system_health_check task: {e}", exc_info=True)
        raise


@celery_app.task(name="backend.tasks.maintenance_tasks.optimize_csv_files", bind=True)
def optimize_csv_files(self):
    """
    Optimize CSV files by removing duplicates and compacting.

    Returns:
        Dict with optimization results
    """
    try:
        logger.info("Starting CSV optimization task")

        # This is a placeholder for CSV optimization logic
        # Could include:
        # - Removing duplicate entries
        # - Sorting by timestamp
        # - Compacting file size
        # - Validating data integrity

        return {
            "success": True,
            "message": "CSV optimization functionality coming soon",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in optimize_csv_files task: {e}", exc_info=True)
        raise


# Helper functions


def _store_health_check(health_status: Dict[str, Any]):
    """Store health check results."""
    try:
        health_dir = Path("data/health_checks")
        health_dir.mkdir(parents=True, exist_ok=True)

        # Store in daily file
        date_str = datetime.utcnow().strftime("%Y%m%d")
        filename = health_dir / f"health_{date_str}.json"

        # Append to file
        checks = []
        if filename.exists():
            with open(filename, "r") as f:
                checks = json.load(f)

        checks.append(health_status)

        # Keep only last 100 checks
        checks = checks[-100:]

        with open(filename, "w") as f:
            json.dump(checks, f, indent=2)

    except Exception as e:
        logger.error(f"Error storing health check: {e}")
