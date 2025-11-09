# Monitoring Guide - MT5_UI Trading Platform

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Endpoints](#monitoring-endpoints)
3. [Metrics Collection](#metrics-collection)
4. [Alerts and Notifications](#alerts-and-notifications)
5. [Dashboard Usage](#dashboard-usage)
6. [Log Files](#log-files)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The MT5_UI trading platform includes comprehensive monitoring capabilities to track:

- **System Health**: MT5 connection, data directories, disk space
- **Application Metrics**: Request counts, error rates, latency
- **Trading Metrics**: Orders, positions, P&L
- **Security Metrics**: Authentication attempts, security events
- **Performance Metrics**: Response times, throughput

### Architecture

```
┌─────────────────┐
│  Frontend UI    │
│  (Monitoring    │
│   Dashboard)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Monitoring     │
│  Endpoints      │
│  (/api/         │
│   monitoring/*) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Metrics        │
│  Collector      │
│  (In-Memory)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CSV Logs       │
│  (Historical    │
│   Data)         │
└─────────────────┘
```

---

## Monitoring Endpoints

### 1. Health Check

**Endpoint**: `GET /api/monitoring/health`

**Purpose**: Comprehensive system health check

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-10T12:00:00Z",
  "issues": [],
  "directories": {
    "data_dir_exists": true,
    "log_dir_exists": true,
    "data_dir_size_mb": 125.5,
    "log_dir_size_mb": 45.2
  },
  "application": {
    "uptime_hours": 24.5,
    "requests": {
      "total": 15234,
      "errors": 12,
      "error_rate": 0.0008
    },
    "trading": {
      "orders_placed": 45,
      "orders_failed": 2,
      "order_success_rate": 0.9565,
      "positions_opened": 45,
      "positions_closed": 40
    },
    "system": {
      "mt5_connected": true,
      "mt5_connection_failures": 0
    }
  },
  "trading": {
    "today": {
      "orders_total": 12,
      "orders_successful": 11,
      "orders_failed": 1,
      "deals_total": 8,
      "pnl": 125.50
    }
  },
  "errors": {
    "recent_errors": 5,
    "errors_by_scope": {
      "order_send": 2,
      "symbols": 3
    }
  },
  "security": {
    "recent_events": 10,
    "invalid_api_key_attempts": 0
  }
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some issues detected
- `unhealthy`: Critical issues

---

### 2. Application Metrics

**Endpoint**: `GET /api/monitoring/metrics`

**Purpose**: Get current application metrics

**Response**:
```json
{
  "timestamp": "2025-10-10T12:00:00Z",
  "uptime_seconds": 88200,
  "uptime_hours": 24.5,
  "requests": {
    "total": 15234,
    "by_endpoint": {
      "GET /api/account": 1200,
      "GET /api/positions": 2500,
      "POST /api/order": 45
    },
    "errors": 12,
    "error_rate": 0.0008
  },
  "latency": {
    "average_ms": {
      "GET /api/account": 45.2,
      "GET /api/positions": 32.1,
      "POST /api/order": 125.5
    },
    "p95_ms": {
      "GET /api/account": 85.0,
      "GET /api/positions": 65.0,
      "POST /api/order": 250.0
    }
  },
  "trading": {
    "orders_placed": 45,
    "orders_failed": 2,
    "order_success_rate": 0.9565,
    "positions_opened": 45,
    "positions_closed": 40
  },
  "system": {
    "mt5_connected": true,
    "mt5_connection_failures": 0,
    "last_mt5_check": "2025-10-10T11:59:30Z"
  }
}
```

---

### 3. Trading Metrics

**Endpoint**: `GET /api/monitoring/metrics/trading`

**Purpose**: Get trading-specific metrics

**Response**:
```json
{
  "today": {
    "orders_total": 12,
    "orders_successful": 11,
    "orders_failed": 1,
    "deals_total": 8,
    "pnl": 125.50
  },
  "all_time": {
    "orders_total": 1234,
    "deals_total": 890
  }
}
```

---

### 4. Error Metrics

**Endpoint**: `GET /api/monitoring/metrics/errors`

**Purpose**: Get error metrics (last 24 hours)

**Response**:
```json
{
  "recent_errors": 5,
  "errors_by_scope": {
    "order_send": 2,
    "symbols": 3
  },
  "last_errors": [
    {
      "ts_utc": "2025-10-10T11:30:00Z",
      "scope": "order_send",
      "message": "MT5 terminal not connected",
      "details": ""
    }
  ]
}
```

---

### 5. Security Metrics

**Endpoint**: `GET /api/monitoring/metrics/security`

**Purpose**: Get security metrics (last 24 hours)

**Response**:
```json
{
  "recent_events": 10,
  "events_by_type": {
    "api_key_authenticated": 8,
    "invalid_api_key_attempt": 2
  },
  "invalid_api_key_attempts": 2,
  "last_events": [
    {
      "ts_utc": "2025-10-10T11:00:00Z",
      "event_type": "invalid_api_key_attempt",
      "client_ip": "127.0.0.1",
      "details": "Invalid API key from 127.0.0.1"
    }
  ]
}
```

---

### 6. Quick Status

**Endpoint**: `GET /api/monitoring/status`

**Purpose**: Lightweight status check

**Response**:
```json
{
  "status": "healthy",
  "issues": [],
  "mt5_connected": true,
  "error_rate": 0.0008,
  "uptime_hours": 24.5,
  "timestamp": "2025-10-10T12:00:00Z"
}
```

---

### 7. Alerts

**Endpoint**: `GET /api/monitoring/alerts`

**Purpose**: Get current system alerts

**Response**:
```json
{
  "alerts": [
    {
      "severity": "warning",
      "category": "performance",
      "message": "High error rate: 12.5%",
      "timestamp": "2025-10-10T12:00:00Z"
    }
  ],
  "count": 1,
  "timestamp": "2025-10-10T12:00:00Z"
}
```

**Alert Severities**:
- `critical`: Immediate attention required
- `warning`: Should be investigated
- `info`: Informational only

**Alert Categories**:
- `system`: MT5 connection, directories
- `performance`: Error rates, latency
- `errors`: Error counts
- `security`: Authentication, security events
- `trading`: Order failures

---

### 8. Performance Metrics

**Endpoint**: `GET /api/monitoring/performance`

**Purpose**: Get performance metrics

**Response**:
```json
{
  "latency": {
    "average_ms": {...},
    "p95_ms": {...}
  },
  "throughput": {
    "requests_per_second": 0.172,
    "total_requests": 15234,
    "uptime_seconds": 88200
  },
  "errors": {
    "total": 12,
    "rate": 0.0008,
    "by_endpoint": {}
  },
  "timestamp": "2025-10-10T12:00:00Z"
}
```

---

### 9. Dashboard Data

**Endpoint**: `GET /api/monitoring/dashboard`

**Purpose**: Get all monitoring data in one request

**Response**: Combined data from health, alerts, and metrics endpoints

---

### 10. Metrics Snapshot

**Endpoint**: `POST /api/monitoring/metrics/snapshot`

**Purpose**: Create a metrics snapshot and log to CSV

**Response**:
```json
{
  "status": "success",
  "message": "Metrics snapshot created"
}
```

**Usage**: Call this endpoint periodically (e.g., every hour) to create historical metrics data in `logs/metrics.csv`

---

### 11. Reset Metrics

**Endpoint**: `POST /api/monitoring/metrics/reset`

**Purpose**: Reset application metrics

**Response**:
```json
{
  "status": "success",
  "message": "Metrics reset"
}
```

**Usage**: Call this endpoint daily to reset counters while preserving historical data in CSV logs

---

## Metrics Collection

### Automatic Collection

The monitoring middleware automatically collects:

1. **Request Metrics**
   - Request count by endpoint
   - Response times (average, p95)
   - Error rates

2. **Trading Metrics**
   - Order placements (success/failure)
   - Position openings/closings

3. **System Metrics**
   - MT5 connection status
   - Connection failures

### Manual Collection

You can manually record metrics using the `metrics_collector`:

```python
from backend.monitoring import metrics_collector

# Record order
metrics_collector.record_order(success=True)

# Record position
metrics_collector.record_position_opened()
metrics_collector.record_position_closed()

# Record MT5 status
metrics_collector.record_mt5_status(connected=True)
```

---

## Alerts and Notifications

### Alert Triggers

Alerts are automatically generated for:

1. **MT5 Disconnection** (Critical)
   - Triggered when MT5 terminal is not connected

2. **High Error Rate** (Warning)
   - Triggered when error rate > 10%

3. **High Error Count** (Warning)
   - Triggered when > 100 errors in last 24 hours

4. **Security Threats** (Warning)
   - Triggered when > 10 invalid API key attempts in last 24 hours

5. **Trading Failures** (Warning)
   - Triggered when > 10 failed orders

### Implementing Notifications

To implement email/SMS notifications, create a scheduled task:

```python
import asyncio
from backend.monitoring_routes import get_alerts

async def check_alerts():
    alerts = get_alerts(request=None)
    
    for alert in alerts["alerts"]:
        if alert["severity"] == "critical":
            # Send email/SMS
            send_notification(alert)

# Run every 5 minutes
while True:
    await check_alerts()
    await asyncio.sleep(300)
```

---

## Dashboard Usage

### Accessing the Dashboard

1. Navigate to the Monitoring page in the UI
2. View real-time metrics and alerts
3. Toggle auto-refresh (30-second interval)
4. Manually refresh data

### Dashboard Sections

1. **Status Overview**
   - System status
   - MT5 connection
   - Uptime
   - Error rate

2. **Active Alerts**
   - Current alerts with severity
   - Alert category and message
   - Timestamp

3. **Trading Metrics**
   - Today's orders
   - Positions
   - P&L

4. **Performance Metrics**
   - Request statistics
   - Latency
   - Throughput

5. **Security Metrics**
   - Security events
   - Invalid API key attempts

6. **System Metrics**
   - Storage usage
   - Directory status

---

## Log Files

### Metrics Log

**File**: `logs/metrics.csv`

**Columns**:
- `ts_utc`: Timestamp
- `uptime_hours`: Application uptime
- `total_requests`: Total requests
- `total_errors`: Total errors
- `error_rate`: Error rate
- `orders_placed`: Orders placed
- `orders_failed`: Orders failed
- `order_success_rate`: Order success rate
- `mt5_connected`: MT5 connection status
- `mt5_failures`: MT5 connection failures

**Usage**: Historical metrics data for analysis and reporting

---

## Performance Tuning

### Optimizing Metrics Collection

1. **Adjust Metrics Retention**
   - Latency deque size: `maxlen=1000` (default)
   - Increase for more accurate statistics
   - Decrease to reduce memory usage

2. **Snapshot Frequency**
   - Default: Manual
   - Recommended: Every hour
   - High-frequency: Every 15 minutes

3. **Auto-Refresh Interval**
   - Default: 30 seconds
   - Increase to reduce server load
   - Decrease for real-time monitoring

---

## Troubleshooting

### High Error Rate

**Symptoms**: Error rate > 10%

**Possible Causes**:
- MT5 terminal disconnected
- Network issues
- Invalid requests

**Solutions**:
1. Check MT5 connection
2. Review error logs (`logs/errors.csv`)
3. Check network connectivity

### MT5 Connection Failures

**Symptoms**: `mt5_connected: false`

**Possible Causes**:
- MT5 terminal not running
- MT5 not logged in
- MetaTrader5 Python package not installed

**Solutions**:
1. Start MT5 terminal
2. Log in to MT5 account
3. Reinstall MetaTrader5 package: `pip install MetaTrader5`

### High Memory Usage

**Symptoms**: Application using excessive memory

**Possible Causes**:
- Large latency deque
- Too many metrics stored

**Solutions**:
1. Reduce latency deque size
2. Call `/api/monitoring/metrics/reset` daily
3. Implement log rotation

---

## Best Practices

1. **Regular Monitoring**
   - Check dashboard daily
   - Review alerts immediately
   - Investigate degraded status

2. **Metrics Snapshots**
   - Create hourly snapshots
   - Archive old metrics logs
   - Analyze trends

3. **Alert Response**
   - Critical alerts: Immediate action
   - Warning alerts: Investigate within 1 hour
   - Info alerts: Review daily

4. **Log Management**
   - Rotate logs weekly
   - Archive old logs monthly
   - Keep 90 days of history

---

**Last Updated**: 2025-10-10  
**Version**: 1.0.0

