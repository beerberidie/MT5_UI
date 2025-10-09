# MT5_UI Storage System

Flexible storage abstraction layer supporting file-based, database, or hybrid storage.

## Overview

The storage system provides a unified interface for storing application data with support for:

- **File-based storage** (JSON files) - Current method, simple and portable
- **Database storage** (SQLite) - Production-ready, better performance and security
- **Hybrid storage** (Synchronized) - Writes to both, seamless migration path

## Architecture

```
StorageInterface (Abstract)
    ├── FileStorage (JSON files)
    ├── DatabaseStorage (SQLite)
    └── SyncStorage (Both)
```

## Configuration

### Environment Variables

```bash
# Storage type: "file", "database", or "sync"
STORAGE_TYPE=file

# Enable synchronization between file and database
STORAGE_SYNC_ENABLED=false
```

### Usage in Code

```python
from backend.storage.storage_factory import get_storage

# Get storage instance (automatically configured)
storage = get_storage()

# Use storage
accounts = await storage.get_accounts()
await storage.add_account({
    "name": "Demo Account",
    "login": 107030709,
    "password": "password123",
    "server": "MetaQuotes-Demo"
})
```

## Storage Types

### 1. File Storage (Default)

**Pros:**
- ✅ Simple, no database setup required
- ✅ Portable, easy to backup
- ✅ Human-readable (JSON)
- ✅ Compatible with existing setup

**Cons:**
- ❌ Slower for large datasets
- ❌ No ACID guarantees
- ❌ File locking issues on concurrent access

**Files:**
- `config/accounts.json` - MT5 account credentials (encrypted)
- `config/api_integrations.json` - API keys and configurations (encrypted)
- `config/appearance.json` - UI appearance settings
- `config/rss_feeds.json` - RSS feed sources
- `data/cache/*.json` - Cached data (economic calendar, news, etc.)

### 2. Database Storage

**Pros:**
- ✅ Better performance
- ✅ ACID transactions
- ✅ Concurrent access support
- ✅ Query capabilities
- ✅ Production-ready

**Cons:**
- ❌ Requires database file
- ❌ Less portable
- ❌ Not human-readable

**Database:**
- `data/mt5_ui.db` - SQLite database file

**Tables:**
- `accounts` - MT5 account credentials
- `api_integrations` - API keys and configurations
- `appearance_settings` - UI appearance settings
- `cache` - Cached data with TTL
- `rss_feeds` - RSS feed sources

### 3. Hybrid Storage (Sync Mode)

**Pros:**
- ✅ Best of both worlds
- ✅ Seamless migration path
- ✅ Data redundancy
- ✅ Easy rollback

**Cons:**
- ❌ Slower writes (writes to both)
- ❌ More disk space
- ❌ Potential sync issues

**How it works:**
1. Reads from primary storage (file or database)
2. Writes to both storages
3. Logs warnings if secondary write fails
4. Allows switching primary without data loss

## Migration

### Migrate from File to Database

```bash
# Dry run (preview what will be migrated)
python -m backend.storage.migrate file-to-db --dry-run

# Actual migration
python -m backend.storage.migrate file-to-db
```

### Migrate from Database to File

```bash
python -m backend.storage.migrate db-to-file --dry-run
python -m backend.storage.migrate db-to-file
```

### Verify Synchronization

```bash
python -m backend.storage.migrate verify
```

## Security

### Encryption

All sensitive data (passwords, API keys) is encrypted using Fernet (AES 128-bit):

- Encryption key stored in `config/.encryption_key`
- Key is auto-generated on first run
- **IMPORTANT:** Add `.encryption_key` to `.gitignore`
- **IMPORTANT:** Backup encryption key securely

### Best Practices

1. ✅ **Never commit encryption key to git**
2. ✅ **Never log decrypted passwords or API keys**
3. ✅ **Use HTTPS for all API calls**
4. ✅ **Mask sensitive data in UI** (show last 4 characters only)
5. ✅ **Backup encryption key separately** from data files
6. ✅ **Rotate API keys periodically**

## API Reference

### Accounts

```python
# Get all accounts
accounts = await storage.get_accounts()

# Get specific account
account = await storage.get_account(account_id)

# Add account
new_account = await storage.add_account({
    "name": "Demo Account",
    "login": 107030709,
    "password": "password123",
    "server": "MetaQuotes-Demo"
})

# Update account
updated = await storage.update_account(account_id, {
    "name": "Updated Name",
    "password": "new_password"
})

# Remove account
success = await storage.remove_account(account_id)

# Get active account
active = await storage.get_active_account()

# Set active account
success = await storage.set_active_account(account_id)
```

### API Integrations

```python
# Get all integrations
integrations = await storage.get_api_integrations()

# Add integration
new_integration = await storage.add_api_integration({
    "name": "NewsAPI",
    "type": "news",
    "api_key": "your_api_key_here",
    "base_url": "https://newsapi.org/v2",
    "config": {"pageSize": 50}
})

# Update integration
updated = await storage.update_api_integration(integration_id, {
    "api_key": "new_api_key",
    "status": "active"
})

# Remove integration
success = await storage.remove_api_integration(integration_id)
```

### Appearance Settings

```python
# Get settings
settings = await storage.get_appearance_settings()

# Update settings
updated = await storage.update_appearance_settings({
    "density": "compact",
    "theme": "dark",
    "fontSize": 12
})
```

### Cache

```python
# Get cached data
data = await storage.get_cached_data("economic_calendar")

# Set cached data (with 6-hour TTL)
await storage.set_cached_data("economic_calendar", data, ttl_seconds=21600)

# Clear cache
await storage.clear_cache("economic_calendar")  # Specific cache
await storage.clear_cache()  # All caches
```

### RSS Feeds

```python
# Get all feeds
feeds = await storage.get_rss_feeds()

# Add feed
new_feed = await storage.add_rss_feed({
    "name": "Forex Live",
    "url": "https://www.forexlive.com/feed/news",
    "enabled": True
})

# Update feed
updated = await storage.update_rss_feed(feed_id, {
    "enabled": False
})

# Remove feed
success = await storage.remove_rss_feed(feed_id)
```

## Switching Storage Types

### Option 1: Environment Variable

```bash
# Use file storage (default)
STORAGE_TYPE=file python start_app.py

# Use database storage
STORAGE_TYPE=database python start_app.py

# Use sync mode (writes to both)
STORAGE_TYPE=file STORAGE_SYNC_ENABLED=true python start_app.py
```

### Option 2: Code Configuration

```python
from backend.storage.storage_factory import StorageFactory

# Create specific storage type
file_storage = StorageFactory.create_storage("file")
db_storage = StorageFactory.create_storage("database")
sync_storage = StorageFactory.create_storage("file", sync_enabled=True)
```

## Recommended Migration Path

### Phase 1: Current State (File Storage)
```bash
STORAGE_TYPE=file
STORAGE_SYNC_ENABLED=false
```

### Phase 2: Enable Sync (Dual Write)
```bash
STORAGE_TYPE=file
STORAGE_SYNC_ENABLED=true
```
- Writes to both file and database
- Reads from file (primary)
- Builds up database in background

### Phase 3: Verify Sync
```bash
python -m backend.storage.migrate verify
```
- Ensure both storages have same data

### Phase 4: Switch Primary to Database
```bash
STORAGE_TYPE=database
STORAGE_SYNC_ENABLED=true
```
- Reads from database (primary)
- Still writes to both (safety net)

### Phase 5: Database Only
```bash
STORAGE_TYPE=database
STORAGE_SYNC_ENABLED=false
```
- Fully migrated to database
- File storage can be archived

## Troubleshooting

### Encryption Key Lost

If encryption key is lost, encrypted data cannot be recovered. You'll need to:

1. Delete `config/.encryption_key`
2. Delete encrypted data files
3. Re-add accounts and API keys

### Database Corruption

```bash
# Restore from file storage
python -m backend.storage.migrate file-to-db
```

### File Storage Corruption

```bash
# Restore from database
python -m backend.storage.migrate db-to-file
```

### Sync Issues

```bash
# Verify synchronization
python -m backend.storage.migrate verify

# Re-sync if needed
python -m backend.storage.migrate file-to-db
```

## Testing

```python
import pytest
from backend.storage.storage_factory import StorageFactory, reset_storage

@pytest.fixture
def storage():
    # Create test storage
    storage = StorageFactory.create_storage("file")
    yield storage
    # Cleanup
    reset_storage()

async def test_add_account(storage):
    account = await storage.add_account({
        "name": "Test Account",
        "login": 12345,
        "password": "test123",
        "server": "Test-Server"
    })
    assert account["name"] == "Test Account"
    assert "id" in account
```

## Performance Considerations

### File Storage
- Fast for small datasets (< 100 records)
- Reads entire file into memory
- No indexing

### Database Storage
- Fast for large datasets
- Indexed queries
- Supports pagination
- Better for concurrent access

### Caching
- Use cache for expensive operations
- Set appropriate TTL
- Clear cache when data changes

## Future Enhancements

- [ ] PostgreSQL support for multi-user deployments
- [ ] Redis cache layer for distributed systems
- [ ] Automatic backup and restore
- [ ] Data encryption at rest (full database encryption)
- [ ] Audit logging for all data changes
- [ ] Data export/import utilities

