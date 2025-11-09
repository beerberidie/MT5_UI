# Redis + Celery Setup Guide

This guide walks you through setting up Redis and Celery for background task processing in the AI Trading Platform.

## Overview

**What is Redis?**
- In-memory data store used as message broker for Celery
- Handles task queues and result storage
- Fast, lightweight, easy to set up

**What is Celery?**
- Distributed task queue for Python
- Handles background jobs (AI evaluation, data collection, maintenance)
- Supports scheduled tasks (cron-like scheduling)

## Prerequisites

- Windows 10/11
- Python 3.11+ with virtual environment
- MT5_UI project already set up

---

## Step 1: Install Redis for Windows

### Option A: Using Memurai (Recommended for Windows)

**Memurai** is a Redis-compatible server optimized for Windows.

1. **Download Memurai**
   - Visit: https://www.memurai.com/get-memurai
   - Download Memurai Developer Edition (free)
   - Or direct link: https://www.memurai.com/get-memurai

2. **Install Memurai**
   - Run the installer
   - Accept the license agreement
   - Choose installation directory (default: `C:\Program Files\Memurai\`)
   - Select "Install as Windows Service" (recommended)
   - Click "Install"

3. **Verify Installation**
   ```powershell
   # Check if Memurai service is running
   Get-Service -Name Memurai
   
   # Should show: Status = Running
   ```

4. **Test Connection**
   ```powershell
   # Install redis-cli (optional)
   # Or use Memurai CLI
   "C:\Program Files\Memurai\memurai-cli.exe" ping
   
   # Should output: PONG
   ```

### Option B: Using Redis on WSL2

If you have WSL2 (Windows Subsystem for Linux):

```bash
# In WSL2 terminal
sudo apt update
sudo apt install redis-server

# Start Redis
sudo service redis-server start

# Test
redis-cli ping
# Should output: PONG
```

### Option C: Using Docker

If you have Docker Desktop:

```powershell
# Pull Redis image
docker pull redis:latest

# Run Redis container
docker run -d -p 6379:6379 --name redis redis:latest

# Test
docker exec -it redis redis-cli ping
# Should output: PONG
```

---

## Step 2: Install Python Dependencies

```powershell
# Activate virtual environment
.\.venv311\Scripts\Activate.ps1

# Install Celery and Redis client
pip install celery==5.4.0
pip install redis==5.0.1
pip install celery[redis]==5.4.0

# Or install all requirements
pip install -r requirements.txt
```

---

## Step 3: Configure Environment

Create/update `.env` file in project root:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Notes**:
- `localhost:6379` is the default Redis address
- `/0` is the database number (Redis supports 16 databases by default)
- If using Memurai, the URL is the same: `redis://localhost:6379/0`

---

## Step 4: Start Celery Worker

Open a **new PowerShell terminal** (keep it running):

```powershell
# Activate virtual environment
.\.venv311\Scripts\Activate.ps1

# Start Celery worker
celery -A backend.celery_app worker --loglevel=info --pool=solo

# For Windows, use --pool=solo (required on Windows)
```

**Expected output**:
```
 -------------- celery@YOUR-PC v5.4.0 (opalescent)
--- ***** ----- 
-- ******* ---- Windows-10-10.0.19045-SP0 2025-10-27 12:00:00
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         ai_trader:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 8 (solo)
-- ******* ---- .> task events: OFF
--- ***** ----- 
 -------------- [queues]
                .> ai_evaluation    exchange=ai_evaluation(direct) key=ai_evaluation
                .> data_collection  exchange=data_collection(direct) key=data_collection
                .> maintenance      exchange=maintenance(direct) key=maintenance
                .> monitoring       exchange=monitoring(direct) key=monitoring

[tasks]
  . backend.tasks.ai_tasks.backtest_strategy
  . backend.tasks.ai_tasks.evaluate_all_strategies
  . backend.tasks.ai_tasks.evaluate_single_symbol
  . backend.tasks.data_tasks.collect_market_data
  . backend.tasks.data_tasks.collect_rss_news
  . backend.tasks.data_tasks.update_economic_calendar
  . backend.tasks.data_tasks.update_symbol_info
  . backend.tasks.maintenance_tasks.archive_old_trades
  . backend.tasks.maintenance_tasks.cleanup_cache
  . backend.tasks.maintenance_tasks.cleanup_old_logs
  . backend.tasks.maintenance_tasks.optimize_csv_files
  . backend.tasks.maintenance_tasks.system_health_check

[2025-10-27 12:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-10-27 12:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-10-27 12:00:00,000: INFO/MainProcess] mingle: all alone
[2025-10-27 12:00:00,000: INFO/MainProcess] celery@YOUR-PC ready.
```

---

## Step 5: Start Celery Beat (Scheduler)

Open **another new PowerShell terminal** (keep it running):

```powershell
# Activate virtual environment
.\.venv311\Scripts\Activate.ps1

# Start Celery beat scheduler
celery -A backend.celery_app beat --loglevel=info
```

**Expected output**:
```
celery beat v5.4.0 (opalescent) is starting.
__    -    ... __   -        _
LocalTime -> 2025-10-27 12:00:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 minutes (300s)

[2025-10-27 12:00:00,000: INFO/MainProcess] beat: Starting...
[2025-10-27 12:00:00,000: INFO/MainProcess] Scheduler: Sending due task evaluate-ai-strategies
[2025-10-27 12:00:00,000: INFO/MainProcess] Scheduler: Sending due task collect-market-data
```

---

## Step 6: Update FastAPI Application

Add Celery routes to your FastAPI app:

<function_calls>
<invoke name="view">
<parameter name="path">backend/app.py
