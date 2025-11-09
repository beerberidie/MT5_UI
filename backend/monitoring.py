"""
Monitoring and metrics collection for MT5_UI Trading Platform.

This module provides comprehensive monitoring capabilities including:
- Application metrics (requests, errors, latency)
- Trading metrics (orders, positions, P&L)
- System metrics (MT5 connection, data directories)
- Performance metrics (response times, throughput)
"""

import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import threading

from .config import DATA_DIR, LOG_DIR
from .csv_io import read_csv_rows, append_csv, utcnow_iso


class MetricsCollector:
    """Collect and aggregate application metrics."""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # Request metrics
        self.request_count = defaultdict(int)
        self.request_errors = defaultdict(int)
        self.request_latencies = defaultdict(lambda: deque(maxlen=1000))
        
        # Trading metrics
        self.orders_placed = 0
        self.orders_failed = 0
        self.positions_opened = 0
        self.positions_closed = 0
        
        # System metrics
        self.mt5_connection_failures = 0
        self.last_mt5_check = None
        self.mt5_connected = False
        
        # Performance metrics
        self.start_time = time.time()
        self.last_reset = datetime.now(timezone.utc)
    
    def record_request(self, endpoint: str, method: str, status_code: int, latency_ms: float):
        """Record an API request."""
        with self._lock:
            key = f"{method} {endpoint}"
            self.request_count[key] += 1
            self.request_latencies[key].append(latency_ms)
            
            if status_code >= 400:
                self.request_errors[key] += 1
    
    def record_order(self, success: bool):
        """Record an order attempt."""
        with self._lock:
            if success:
                self.orders_placed += 1
            else:
                self.orders_failed += 1
    
    def record_position_opened(self):
        """Record a position being opened."""
        with self._lock:
            self.positions_opened += 1
    
    def record_position_closed(self):
        """Record a position being closed."""
        with self._lock:
            self.positions_closed += 1
    
    def record_mt5_status(self, connected: bool):
        """Record MT5 connection status."""
        with self._lock:
            self.last_mt5_check = datetime.now(timezone.utc)
            if not connected:
                self.mt5_connection_failures += 1
            self.mt5_connected = connected
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._lock:
            uptime_seconds = time.time() - self.start_time
            
            # Calculate average latencies
            avg_latencies = {}
            p95_latencies = {}
            for endpoint, latencies in self.request_latencies.items():
                if latencies:
                    sorted_latencies = sorted(latencies)
                    avg_latencies[endpoint] = sum(latencies) / len(latencies)
                    p95_index = int(len(sorted_latencies) * 0.95)
                    p95_latencies[endpoint] = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
            
            return {
                "timestamp": utcnow_iso(),
                "uptime_seconds": uptime_seconds,
                "uptime_hours": uptime_seconds / 3600,
                "requests": {
                    "total": sum(self.request_count.values()),
                    "by_endpoint": dict(self.request_count),
                    "errors": sum(self.request_errors.values()),
                    "error_rate": sum(self.request_errors.values()) / max(sum(self.request_count.values()), 1),
                },
                "latency": {
                    "average_ms": avg_latencies,
                    "p95_ms": p95_latencies,
                },
                "trading": {
                    "orders_placed": self.orders_placed,
                    "orders_failed": self.orders_failed,
                    "order_success_rate": self.orders_placed / max(self.orders_placed + self.orders_failed, 1),
                    "positions_opened": self.positions_opened,
                    "positions_closed": self.positions_closed,
                },
                "system": {
                    "mt5_connected": self.mt5_connected,
                    "mt5_connection_failures": self.mt5_connection_failures,
                    "last_mt5_check": self.last_mt5_check.isoformat() if self.last_mt5_check else None,
                }
            }
    
    def reset_metrics(self):
        """Reset all metrics (useful for daily/hourly resets)."""
        with self._lock:
            self.request_count.clear()
            self.request_errors.clear()
            self.request_latencies.clear()
            self.orders_placed = 0
            self.orders_failed = 0
            self.positions_opened = 0
            self.positions_closed = 0
            self.mt5_connection_failures = 0
            self.last_reset = datetime.now(timezone.utc)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_trading_metrics() -> Dict[str, Any]:
    """Get trading-specific metrics from logs."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Read today's orders
        orders_path = os.path.join(LOG_DIR, "orders.csv")
        orders = read_csv_rows(orders_path) if os.path.exists(orders_path) else []
        today_orders = [o for o in orders if o.get("ts_utc", "").startswith(today)]
        
        # Read today's deals
        deals_path = os.path.join(LOG_DIR, "deals.csv")
        deals = read_csv_rows(deals_path) if os.path.exists(deals_path) else []
        today_deals = [d for d in deals if d.get("ts_utc", "").startswith(today)]
        
        # Calculate P&L
        total_pnl = sum(float(d.get("profit", 0) or 0) for d in today_deals)
        
        # Count by status
        successful_orders = len([o for o in today_orders if o.get("status") == "success"])
        failed_orders = len([o for o in today_orders if o.get("status") == "error"])
        
        return {
            "today": {
                "orders_total": len(today_orders),
                "orders_successful": successful_orders,
                "orders_failed": failed_orders,
                "deals_total": len(today_deals),
                "pnl": total_pnl,
            },
            "all_time": {
                "orders_total": len(orders),
                "deals_total": len(deals),
            }
        }
    except Exception as e:
        return {"error": str(e)}


def get_error_metrics() -> Dict[str, Any]:
    """Get error metrics from logs."""
    try:
        # Read recent errors (last 24 hours)
        errors_path = os.path.join(LOG_DIR, "errors.csv")
        if not os.path.exists(errors_path):
            return {"recent_errors": 0, "errors_by_scope": {}}
        
        errors = read_csv_rows(errors_path)
        
        # Filter last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_errors = []
        for error in errors:
            try:
                error_time = datetime.fromisoformat(error.get("ts_utc", "").replace("Z", "+00:00"))
                if error_time >= cutoff:
                    recent_errors.append(error)
            except:
                continue
        
        # Count by scope
        errors_by_scope = defaultdict(int)
        for error in recent_errors:
            scope = error.get("scope", "unknown")
            errors_by_scope[scope] += 1
        
        return {
            "recent_errors": len(recent_errors),
            "errors_by_scope": dict(errors_by_scope),
            "last_errors": recent_errors[-10:] if recent_errors else []
        }
    except Exception as e:
        return {"error": str(e)}


def get_security_metrics() -> Dict[str, Any]:
    """Get security metrics from logs."""
    try:
        security_path = os.path.join(LOG_DIR, "security.csv")
        if not os.path.exists(security_path):
            return {"recent_events": 0, "events_by_type": {}}
        
        events = read_csv_rows(security_path)
        
        # Filter last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_events = []
        for event in events:
            try:
                event_time = datetime.fromisoformat(event.get("ts_utc", "").replace("Z", "+00:00"))
                if event_time >= cutoff:
                    recent_events.append(event)
            except:
                continue
        
        # Count by type
        events_by_type = defaultdict(int)
        for event in recent_events:
            event_type = event.get("event_type", "unknown")
            events_by_type[event_type] += 1
        
        # Count invalid API key attempts
        invalid_attempts = len([e for e in recent_events if e.get("event_type") == "invalid_api_key_attempt"])
        
        return {
            "recent_events": len(recent_events),
            "events_by_type": dict(events_by_type),
            "invalid_api_key_attempts": invalid_attempts,
            "last_events": recent_events[-10:] if recent_events else []
        }
    except Exception as e:
        return {"error": str(e)}


def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status."""
    try:
        # Check data directories
        data_dir_exists = os.path.exists(DATA_DIR)
        log_dir_exists = os.path.exists(LOG_DIR)
        
        # Check disk space
        data_dir_size = 0
        log_dir_size = 0
        
        if data_dir_exists:
            for root, dirs, files in os.walk(DATA_DIR):
                data_dir_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        if log_dir_exists:
            for root, dirs, files in os.walk(LOG_DIR):
                log_dir_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        # Get metrics
        app_metrics = metrics_collector.get_metrics()
        trading_metrics = get_trading_metrics()
        error_metrics = get_error_metrics()
        security_metrics = get_security_metrics()
        
        # Determine overall health
        health_issues = []
        
        if not app_metrics["system"]["mt5_connected"]:
            health_issues.append("MT5 not connected")
        
        if app_metrics["requests"]["error_rate"] > 0.1:  # >10% error rate
            health_issues.append("High error rate")
        
        if error_metrics.get("recent_errors", 0) > 100:
            health_issues.append("High error count")
        
        if security_metrics.get("invalid_api_key_attempts", 0) > 10:
            health_issues.append("Multiple invalid API key attempts")
        
        health_status = "healthy" if not health_issues else "degraded" if len(health_issues) < 3 else "unhealthy"
        
        return {
            "status": health_status,
            "timestamp": utcnow_iso(),
            "issues": health_issues,
            "directories": {
                "data_dir_exists": data_dir_exists,
                "log_dir_exists": log_dir_exists,
                "data_dir_size_mb": data_dir_size / (1024 * 1024),
                "log_dir_size_mb": log_dir_size / (1024 * 1024),
            },
            "application": app_metrics,
            "trading": trading_metrics,
            "errors": error_metrics,
            "security": security_metrics,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": utcnow_iso(),
            "error": str(e)
        }


def log_metrics_snapshot():
    """Log current metrics to CSV for historical tracking."""
    try:
        metrics = metrics_collector.get_metrics()
        path = os.path.join(LOG_DIR, "metrics.csv")
        
        append_csv(
            path,
            {
                "ts_utc": utcnow_iso(),
                "uptime_hours": metrics["uptime_hours"],
                "total_requests": metrics["requests"]["total"],
                "total_errors": metrics["requests"]["errors"],
                "error_rate": metrics["requests"]["error_rate"],
                "orders_placed": metrics["trading"]["orders_placed"],
                "orders_failed": metrics["trading"]["orders_failed"],
                "order_success_rate": metrics["trading"]["order_success_rate"],
                "mt5_connected": metrics["system"]["mt5_connected"],
                "mt5_failures": metrics["system"]["mt5_connection_failures"],
            },
            [
                "ts_utc", "uptime_hours", "total_requests", "total_errors", "error_rate",
                "orders_placed", "orders_failed", "order_success_rate",
                "mt5_connected", "mt5_failures"
            ]
        )
    except Exception as e:
        print(f"Failed to log metrics snapshot: {e}")

