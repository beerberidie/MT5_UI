# PostgreSQL Setup Guide

This guide walks you through setting up PostgreSQL for the AI Trading Platform.

## Prerequisites

- Windows 10/11
- Python 3.11+ with virtual environment
- Administrator access (for PostgreSQL installation)

## Step 1: Install PostgreSQL 16

### Option A: Using Official Installer (Recommended)

1. **Download PostgreSQL 16**
   - Visit: https://www.postgresql.org/download/windows/
   - Download the PostgreSQL 16 installer for Windows
   - Or direct link: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

2. **Run the Installer**
   - Double-click the downloaded `.exe` file
   - Click "Next" through the welcome screen
   - Choose installation directory (default: `C:\Program Files\PostgreSQL\16`)
   - Select components:
     - ✅ PostgreSQL Server
     - ✅ pgAdmin 4 (GUI tool)
     - ✅ Command Line Tools
     - ✅ Stack Builder (optional)
   - Choose data directory (default: `C:\Program Files\PostgreSQL\16\data`)
   - **Set superuser password**: Choose a strong password (e.g., `trader123`)
     - ⚠️ **REMEMBER THIS PASSWORD** - you'll need it later!
   - Set port: `5432` (default)
   - Set locale: Default locale
   - Click "Next" and "Install"

3. **Verify Installation**
   ```powershell
   # Open PowerShell and run:
   psql --version
   # Should output: psql (PostgreSQL) 16.x
   ```

### Option B: Using Chocolatey

```powershell
# Run PowerShell as Administrator
choco install postgresql16 --params '/Password:trader123'
```

## Step 2: Create Database User

1. **Open pgAdmin 4** (installed with PostgreSQL)
   - Start Menu → PostgreSQL 16 → pgAdmin 4

2. **Connect to PostgreSQL**
   - Expand "Servers" → "PostgreSQL 16"
   - Enter the superuser password you set during installation

3. **Create User** (or use command line below)
   - Right-click "Login/Group Roles" → "Create" → "Login/Group Role"
   - General tab: Name = `trader`
   - Definition tab: Password = `trader` (or your preferred password)
   - Privileges tab: Check "Can login?"
   - Click "Save"

**OR use command line:**

```powershell
# Open PowerShell
psql -U postgres

# In psql prompt:
CREATE USER trader WITH PASSWORD 'trader';
ALTER USER trader CREATEDB;
\q
```

## Step 3: Install Python Dependencies

```powershell
# Activate your virtual environment
.\.venv311\Scripts\Activate.ps1

# Install PostgreSQL dependencies
pip install sqlalchemy[asyncio]==2.0.32
pip install asyncpg==0.29.0
pip install alembic==1.13.2
pip install psycopg2-binary==2.9.9

# Or install all requirements
pip install -r requirements.txt
```

## Step 4: Configure Database Connection

1. **Create `.env` file** in project root (if not exists):

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql+asyncpg://trader:trader@localhost:5432/ai_trader

# Storage Configuration
USE_POSTGRES=true
DUAL_WRITE=true
```

2. **Customize if needed**:
   - Replace `trader:trader` with your username:password
   - Replace `localhost` with your PostgreSQL host
   - Replace `5432` with your PostgreSQL port
   - Replace `ai_trader` with your preferred database name

## Step 5: Run Database Setup Script

```powershell
# Activate virtual environment
.\.venv311\Scripts\Activate.ps1

# Run setup script
python scripts/setup_postgres.py
```

The script will:
1. ✅ Create the `ai_trader` database
2. ✅ Create all tables (strategies, risk_config, snapshots, etc.)
3. ✅ Initialize default risk configuration
4. ✅ Optionally migrate existing CSV data to PostgreSQL
5. ✅ Verify database connection

**Expected output:**
```
============================================================
PostgreSQL Database Setup for AI Trading Platform
============================================================

Database URL: postgresql+asyncpg://trader:***@localhost:5432/ai_trader

Connecting to PostgreSQL at localhost:5432 as trader...
✅ Database 'ai_trader' created successfully!

Initializing database schema...
✅ Database schema initialized successfully!

Do you want to migrate existing CSV data to PostgreSQL? (y/n): y

Migrating CSV data to PostgreSQL...
✅ Migration complete!
   - Risk config: 1
   - Strategies: 3

Verifying database setup...
✅ Database connection verified!
   - AI Trading Enabled: False
   - Min Confidence: 90.0%

============================================================
✅ PostgreSQL setup complete!
============================================================
```

## Step 6: Verify Setup

### Using pgAdmin 4

1. Open pgAdmin 4
2. Expand: Servers → PostgreSQL 16 → Databases → ai_trader → Schemas → public → Tables
3. You should see:
   - ✅ `strategies`
   - ✅ `risk_config`
   - ✅ `snapshot_market`
   - ✅ `snapshot_indicators`
   - ✅ `snapshot_calendar`
   - ✅ `snapshot_news`
   - ✅ `snapshot_account`
   - ✅ `trade_ideas`
   - ✅ `decision_history`
   - ✅ `users`

### Using Command Line

```powershell
# Connect to database
psql -U trader -d ai_trader

# List tables
\dt

# View risk_config
SELECT * FROM risk_config;

# Exit
\q
```

## Step 7: Start Application with PostgreSQL

```powershell
# Activate virtual environment
.\.venv311\Scripts\Activate.ps1

# Start backend
cd backend
uvicorn app:app --host 127.0.0.1 --port 5001 --reload
```

The application will now:
- ✅ Read from PostgreSQL (with CSV fallback)
- ✅ Write to both PostgreSQL and CSV (dual-write mode)
- ✅ Store snapshots in PostgreSQL
- ✅ Track decision history in PostgreSQL
- ✅ Manage trade ideas in PostgreSQL

## Troubleshooting

### Error: "psql: command not found"

**Solution**: Add PostgreSQL to PATH
```powershell
# Add to PATH (replace with your PostgreSQL path)
$env:Path += ";C:\Program Files\PostgreSQL\16\bin"

# Or permanently:
[System.Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\PostgreSQL\16\bin", [System.EnvironmentVariableTarget]::User)
```

### Error: "password authentication failed for user"

**Solution**: Check credentials in `.env` file
- Verify username and password match what you set during installation
- Try connecting with `psql -U trader` to test credentials

### Error: "could not connect to server"

**Solution**: Ensure PostgreSQL is running
```powershell
# Check if PostgreSQL service is running
Get-Service -Name postgresql*

# Start service if stopped
Start-Service -Name postgresql-x64-16
```

### Error: "database does not exist"

**Solution**: Run setup script again
```powershell
python scripts/setup_postgres.py
```

### Error: "asyncpg.exceptions.InvalidPasswordError"

**Solution**: Update DATABASE_URL in `.env` with correct password

## Migration Strategies

### Strategy 1: Dual-Write Mode (Recommended)

Keep both CSV and PostgreSQL in sync:

```env
USE_POSTGRES=true
DUAL_WRITE=true
```

**Pros**:
- ✅ Safe migration path
- ✅ CSV backup always available
- ✅ Can rollback to CSV if needed

**Cons**:
- ❌ Slower writes (2x storage operations)
- ❌ More disk space

### Strategy 2: PostgreSQL-Only Mode

Use only PostgreSQL:

```env
USE_POSTGRES=true
DUAL_WRITE=false
```

**Pros**:
- ✅ Faster writes
- ✅ Less disk space
- ✅ Full PostgreSQL features

**Cons**:
- ❌ No CSV backup
- ❌ Harder to rollback

### Strategy 3: CSV-Only Mode (Legacy)

Keep using CSV:

```env
USE_POSTGRES=false
DUAL_WRITE=false
```

**Use case**: If PostgreSQL setup fails or you want to delay migration

## Database Maintenance

### Backup Database

```powershell
# Backup to file
pg_dump -U trader -d ai_trader -F c -f ai_trader_backup.dump

# Restore from backup
pg_restore -U trader -d ai_trader ai_trader_backup.dump
```

### View Database Size

```sql
SELECT pg_size_pretty(pg_database_size('ai_trader'));
```

### Clean Old Snapshots

```sql
-- Delete snapshots older than 30 days
DELETE FROM snapshot_market WHERE captured_at < NOW() - INTERVAL '30 days';
DELETE FROM snapshot_indicators WHERE captured_at < NOW() - INTERVAL '30 days';
DELETE FROM snapshot_calendar WHERE captured_at < NOW() - INTERVAL '30 days';
DELETE FROM snapshot_news WHERE captured_at < NOW() - INTERVAL '30 days';
DELETE FROM snapshot_account WHERE captured_at < NOW() - INTERVAL '30 days';
```

## Next Steps

After PostgreSQL is set up:

1. ✅ **Phase 1 Complete**: Database Migration
2. ⏳ **Phase 2**: Background Workers (Celery + Redis)
3. ⏳ **Phase 3**: Authentication (JWT)
4. ⏳ **Phase 4**: Decision History UI
5. ⏳ **Phase 5**: Trade Ideas Workflow
6. ⏳ **Phase 6**: Strategy Manager

## Support

If you encounter issues:
1. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\16\data\log\`
2. Check application logs: `logs/app.log`
3. Verify `.env` configuration
4. Test database connection with `psql -U trader -d ai_trader`

