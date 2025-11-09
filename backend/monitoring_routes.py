"""
Monitoring and metrics API routes.

Provides endpoints for:
- System health checks
- Application metrics
- Trading metrics
- Error metrics
- Security metrics
- Performance metrics
"""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .monitoring import (
    metrics_collector,
    get_system_health,
    get_trading_metrics,
    get_error_metrics,
    get_security_metrics,
    log_metrics_snapshot
)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/health")
@limiter.limit("100/minute")
def get_health(request: Request):
    """
    Comprehensive health check endpoint.
    
    Returns:
    - Overall health status (healthy/degraded/unhealthy)
    - System checks (MT5 connection, directories, disk space)
    - Application metrics (requests, errors, latency)
    - Trading metrics (orders, positions, P&L)
    - Error metrics (recent errors by scope)
    - Security metrics (auth attempts, security events)
    """
    return get_system_health()


@router.get("/metrics")
@limiter.limit("100/minute")
def get_metrics(request: Request):
    """
    Get current application metrics.
    
    Returns:
    - Request counts by endpoint
    - Error rates
    - Latency statistics (average, p95)
    - Trading metrics (orders, positions)
    - System metrics (MT5 status, uptime)
    """
    return metrics_collector.get_metrics()


@router.get("/metrics/trading")
@limiter.limit("100/minute")
def get_trading_metrics_endpoint(request: Request):
    """
    Get trading-specific metrics.
    
    Returns:
    - Today's orders (total, successful, failed)
    - Today's deals and P&L
    - All-time statistics
    """
    return get_trading_metrics()


@router.get("/metrics/errors")
@limiter.limit("100/minute")
def get_error_metrics_endpoint(request: Request):
    """
    Get error metrics.
    
    Returns:
    - Recent errors (last 24 hours)
    - Errors by scope
    - Last 10 errors
    """
    return get_error_metrics()


@router.get("/metrics/security")
@limiter.limit("100/minute")
def get_security_metrics_endpoint(request: Request):
    """
    Get security metrics.
    
    Returns:
    - Recent security events (last 24 hours)
    - Events by type
    - Invalid API key attempts
    - Last 10 security events
    """
    return get_security_metrics()


@router.post("/metrics/snapshot")
@limiter.limit("10/minute")
def create_metrics_snapshot(request: Request):
    """
    Create a metrics snapshot and log to CSV.
    
    This endpoint can be called periodically (e.g., every hour)
    to create historical metrics data.
    """
    log_metrics_snapshot()
    return {"status": "success", "message": "Metrics snapshot created"}


@router.post("/metrics/reset")
@limiter.limit("5/minute")
def reset_metrics(request: Request):
    """
    Reset application metrics.
    
    This endpoint can be called daily to reset counters
    while preserving historical data in CSV logs.
    """
    metrics_collector.reset_metrics()
    return {"status": "success", "message": "Metrics reset"}


@router.get("/status")
@limiter.limit("100/minute")
def get_status(request: Request):
    """
    Quick status check (lightweight version of /health).
    
    Returns:
    - Status (healthy/degraded/unhealthy)
    - MT5 connection status
    - Error rate
    - Uptime
    """
    metrics = metrics_collector.get_metrics()
    
    # Determine status
    issues = []
    if not metrics["system"]["mt5_connected"]:
        issues.append("MT5 disconnected")
    if metrics["requests"]["error_rate"] > 0.1:
        issues.append("High error rate")
    
    status = "healthy" if not issues else "degraded" if len(issues) == 1 else "unhealthy"
    
    return {
        "status": status,
        "issues": issues,
        "mt5_connected": metrics["system"]["mt5_connected"],
        "error_rate": metrics["requests"]["error_rate"],
        "uptime_hours": metrics["uptime_hours"],
        "timestamp": metrics["timestamp"]
    }


@router.get("/alerts")
@limiter.limit("100/minute")
def get_alerts(request: Request):
    """
    Get current system alerts.
    
    Returns alerts for:
    - MT5 connection issues
    - High error rates
    - Security threats
    - Performance degradation
    """
    alerts = []
    
    metrics = metrics_collector.get_metrics()
    error_metrics = get_error_metrics()
    security_metrics = get_security_metrics()
    
    # MT5 connection alert
    if not metrics["system"]["mt5_connected"]:
        alerts.append({
            "severity": "critical",
            "category": "system",
            "message": "MT5 terminal not connected",
            "timestamp": metrics["timestamp"]
        })
    
    # High error rate alert
    if metrics["requests"]["error_rate"] > 0.1:
        alerts.append({
            "severity": "warning",
            "category": "performance",
            "message": f"High error rate: {metrics['requests']['error_rate']:.1%}",
            "timestamp": metrics["timestamp"]
        })
    
    # Recent errors alert
    if error_metrics.get("recent_errors", 0) > 100:
        alerts.append({
            "severity": "warning",
            "category": "errors",
            "message": f"{error_metrics['recent_errors']} errors in last 24 hours",
            "timestamp": metrics["timestamp"]
        })
    
    # Security alert
    invalid_attempts = security_metrics.get("invalid_api_key_attempts", 0)
    if invalid_attempts > 10:
        alerts.append({
            "severity": "warning",
            "category": "security",
            "message": f"{invalid_attempts} invalid API key attempts in last 24 hours",
            "timestamp": metrics["timestamp"]
        })
    
    # Trading failure alert
    if metrics["trading"]["orders_failed"] > 10:
        alerts.append({
            "severity": "warning",
            "category": "trading",
            "message": f"{metrics['trading']['orders_failed']} failed orders",
            "timestamp": metrics["timestamp"]
        })
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": metrics["timestamp"]
    }


@router.get("/performance")
@limiter.limit("100/minute")
def get_performance(request: Request):
    """
    Get performance metrics.
    
    Returns:
    - Request latencies (average, p95)
    - Throughput (requests per second)
    - Error rates by endpoint
    """
    metrics = metrics_collector.get_metrics()
    
    # Calculate throughput
    uptime_seconds = metrics["uptime_seconds"]
    total_requests = metrics["requests"]["total"]
    requests_per_second = total_requests / max(uptime_seconds, 1)
    
    return {
        "latency": metrics["latency"],
        "throughput": {
            "requests_per_second": requests_per_second,
            "total_requests": total_requests,
            "uptime_seconds": uptime_seconds
        },
        "errors": {
            "total": metrics["requests"]["errors"],
            "rate": metrics["requests"]["error_rate"],
            "by_endpoint": metrics["requests"].get("errors_by_endpoint", {})
        },
        "timestamp": metrics["timestamp"]
    }


@router.get("/dashboard")
@limiter.limit("100/minute")
def get_dashboard_data(request: Request):
    """
    Get all data needed for monitoring dashboard.
    
    Returns comprehensive monitoring data in a single request:
    - Health status
    - Metrics
    - Alerts
    - Recent errors
    - Recent security events
    """
    health = get_system_health()
    alerts_data = get_alerts(request)
    
    return {
        "health": health,
        "alerts": alerts_data["alerts"],
        "timestamp": health["timestamp"]
    }

