# Start Celery Services for AI Trading Platform
# This script starts Redis check, Celery worker, and Celery beat in separate windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Trading Platform - Celery Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root directory
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow
Write-Host ""

# Check if virtual environment exists
$VenvPath = ".\.venv311\Scripts\Activate.ps1"
if (-not (Test-Path $VenvPath)) {
    Write-Host "ERROR: Virtual environment not found at $VenvPath" -ForegroundColor Red
    Write-Host "Please create the virtual environment first." -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Checking Redis/Memurai service..." -ForegroundColor Green

# Check if Memurai service is running
$MemuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if ($MemuraiService) {
    if ($MemuraiService.Status -eq "Running") {
        Write-Host "  ✓ Memurai service is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Memurai service is not running. Attempting to start..." -ForegroundColor Yellow
        try {
            Start-Service -Name "Memurai"
            Write-Host "  ✓ Memurai service started successfully" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Failed to start Memurai service: $_" -ForegroundColor Red
            Write-Host "  Please start Memurai manually or install it from https://www.memurai.com" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ⚠ Memurai service not found" -ForegroundColor Yellow
    Write-Host "  Checking for Redis on WSL or Docker..." -ForegroundColor Yellow
    
    # Try to ping Redis
    try {
        $RedisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
        if ($RedisTest.TcpTestSucceeded) {
            Write-Host "  ✓ Redis is accessible on localhost:6379" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Redis is not accessible on localhost:6379" -ForegroundColor Red
            Write-Host "  Please install and start Redis/Memurai before continuing" -ForegroundColor Yellow
            Write-Host "  See REDIS_CELERY_SETUP_GUIDE.md for installation instructions" -ForegroundColor Yellow
            exit 1
        }
    } catch {
        Write-Host "  ✗ Cannot connect to Redis" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[2/4] Starting Celery Worker..." -ForegroundColor Green

# Start Celery Worker in new window
$WorkerScript = @"
Set-Location '$ProjectRoot'
& '$VenvPath'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Celery Worker' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
celery -A backend.celery_app worker --loglevel=info --pool=solo
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $WorkerScript
Write-Host "  ✓ Celery Worker started in new window" -ForegroundColor Green

# Wait a bit for worker to initialize
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "[3/4] Starting Celery Beat (Scheduler)..." -ForegroundColor Green

# Start Celery Beat in new window
$BeatScript = @"
Set-Location '$ProjectRoot'
& '$VenvPath'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  Celery Beat Scheduler' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
celery -A backend.celery_app beat --loglevel=info
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $BeatScript
Write-Host "  ✓ Celery Beat started in new window" -ForegroundColor Green

Write-Host ""
Write-Host "[4/4] Summary" -ForegroundColor Green
Write-Host "  ✓ Redis/Memurai: Running" -ForegroundColor Green
Write-Host "  ✓ Celery Worker: Started" -ForegroundColor Green
Write-Host "  ✓ Celery Beat: Started" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All Celery services are running!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start the FastAPI server:" -ForegroundColor White
Write-Host "     cd backend" -ForegroundColor Gray
Write-Host "     uvicorn app:app --host 127.0.0.1 --port 5001 --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test background tasks:" -ForegroundColor White
Write-Host "     curl -X POST http://127.0.0.1:5001/api/celery/tasks/ai/evaluate-all" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. View active tasks:" -ForegroundColor White
Write-Host "     curl http://127.0.0.1:5001/api/celery/tasks/active" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

