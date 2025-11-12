"""
Database Storage Implementation for MT5_UI

Stores data in SQLite database.
Production-ready alternative to file-based storage.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json

from backend.storage.storage_interface import StorageInterface
from backend.services.encryption_service import get_encryption_service


class DatabaseStorage(StorageInterface):
    """SQLite database storage implementation."""

    def __init__(self, db_path: str = "data/mt5_ui.db"):
        """
        Initialize database storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Encryption service
        self.encryption = get_encryption_service()

        # Initialize database schema
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def _initialize_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Accounts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                login INTEGER NOT NULL,
                password_encrypted TEXT NOT NULL,
                server TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # API Integrations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_integrations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('economic_calendar', 'news', 'custom')),
                api_key_encrypted TEXT NOT NULL,
                base_url TEXT,
                config TEXT,
                status TEXT DEFAULT 'inactive' CHECK(status IN ('active', 'inactive', 'error')),
                last_tested TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Appearance Settings table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS appearance_settings (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                density TEXT DEFAULT 'normal' CHECK(density IN ('compact', 'normal', 'comfortable')),
                theme TEXT DEFAULT 'dark' CHECK(theme IN ('dark', 'light', 'auto')),
                font_size INTEGER DEFAULT 14 CHECK(font_size BETWEEN 12 AND 18),
                accent_color TEXT DEFAULT '#3b82f6',
                show_animations BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Cache table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """
        )

        # RSS Feeds table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rss_feeds (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                enabled BOOLEAN DEFAULT 1,
                last_fetched TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rss_enabled ON rss_feeds(enabled)"
        )

        # Initialize appearance settings if not exists
        cursor.execute("SELECT COUNT(*) FROM appearance_settings WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """
                INSERT INTO appearance_settings (id, density, theme, font_size, accent_color, show_animations)
                VALUES (1, 'normal', 'dark', 14, '#3b82f6', 1)
            """
            )

        conn.commit()
        conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        return dict(row) if row else {}

    # ==================== ACCOUNTS ====================

    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all MT5 accounts."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        accounts = []
        for row in rows:
            account = self._row_to_dict(row)
            # Decrypt password
            if "password_encrypted" in account:
                try:
                    account["password"] = self.encryption.decrypt(
                        account["password_encrypted"]
                    )
                except Exception:
                    account["password"] = ""
            # Convert boolean
            account["is_active"] = bool(account.get("is_active", 0))
            accounts.append(account)

        return accounts

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific account by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            account = self._row_to_dict(row)
            if "password_encrypted" in account:
                try:
                    account["password"] = self.encryption.decrypt(
                        account["password_encrypted"]
                    )
                except Exception:
                    account["password"] = ""
            account["is_active"] = bool(account.get("is_active", 0))
            return account

        return None

    async def add_account(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new MT5 account."""
        conn = self._get_connection()
        cursor = conn.cursor()

        account_id = str(uuid.uuid4())
        password_encrypted = self.encryption.encrypt(account.get("password", ""))

        cursor.execute(
            """
            INSERT INTO accounts (id, name, login, password_encrypted, server, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
        """,
            (
                account_id,
                account.get("name", ""),
                account.get("login", 0),
                password_encrypted,
                account.get("server", ""),
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return await self.get_account(account_id)

    async def update_account(
        self, account_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing account."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        update_fields = []
        values = []

        if "name" in updates:
            update_fields.append("name = ?")
            values.append(updates["name"])
        if "login" in updates:
            update_fields.append("login = ?")
            values.append(updates["login"])
        if "password" in updates:
            update_fields.append("password_encrypted = ?")
            values.append(self.encryption.encrypt(updates["password"]))
        if "server" in updates:
            update_fields.append("server = ?")
            values.append(updates["server"])

        if not update_fields:
            conn.close()
            return await self.get_account(account_id)

        update_fields.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(account_id)

        query = f"UPDATE accounts SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        return await self.get_account(account_id)

    async def remove_account(self, account_id: str) -> bool:
        """Remove an account."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    async def get_active_account(self) -> Optional[Dict[str, Any]]:
        """Get the currently active account."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            account = self._row_to_dict(row)
            if "password_encrypted" in account:
                try:
                    account["password"] = self.encryption.decrypt(
                        account["password_encrypted"]
                    )
                except Exception:
                    account["password"] = ""
            account["is_active"] = True
            return account

        return None

    async def set_active_account(self, account_id: str) -> bool:
        """Set the active account."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if account exists
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE id = ?", (account_id,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return False

        # Deactivate all accounts
        cursor.execute("UPDATE accounts SET is_active = 0")

        # Activate the specified account
        cursor.execute("UPDATE accounts SET is_active = 1 WHERE id = ?", (account_id,))

        conn.commit()
        conn.close()

        return True

    # ==================== API INTEGRATIONS ====================

    async def get_api_integrations(self) -> List[Dict[str, Any]]:
        """Get all API integrations."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM api_integrations ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        integrations = []
        for row in rows:
            integration = self._row_to_dict(row)
            # Decrypt API key
            if "api_key_encrypted" in integration:
                try:
                    integration["api_key"] = self.encryption.decrypt(
                        integration["api_key_encrypted"]
                    )
                except Exception:
                    integration["api_key"] = ""
            # Parse config JSON
            if "config" in integration and integration["config"]:
                try:
                    integration["config"] = json.loads(integration["config"])
                except Exception:
                    integration["config"] = {}
            integrations.append(integration)

        return integrations

    async def get_api_integration(
        self, integration_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific API integration by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM api_integrations WHERE id = ?", (integration_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            integration = self._row_to_dict(row)
            if "api_key_encrypted" in integration:
                try:
                    integration["api_key"] = self.encryption.decrypt(
                        integration["api_key_encrypted"]
                    )
                except Exception:
                    integration["api_key"] = ""
            if "config" in integration and integration["config"]:
                try:
                    integration["config"] = json.loads(integration["config"])
                except Exception:
                    integration["config"] = {}
            return integration

        return None

    async def add_api_integration(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new API integration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        integration_id = str(uuid.uuid4())
        api_key_encrypted = self.encryption.encrypt(integration.get("api_key", ""))
        config_json = json.dumps(integration.get("config", {}))

        cursor.execute(
            """
            INSERT INTO api_integrations (id, name, type, api_key_encrypted, base_url, config, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'inactive', ?, ?)
        """,
            (
                integration_id,
                integration.get("name", ""),
                integration.get("type", "custom"),
                api_key_encrypted,
                integration.get("base_url", ""),
                config_json,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return await self.get_api_integration(integration_id)

    async def update_api_integration(
        self, integration_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing API integration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []

        if "name" in updates:
            update_fields.append("name = ?")
            values.append(updates["name"])
        if "type" in updates:
            update_fields.append("type = ?")
            values.append(updates["type"])
        if "api_key" in updates:
            update_fields.append("api_key_encrypted = ?")
            values.append(self.encryption.encrypt(updates["api_key"]))
        if "base_url" in updates:
            update_fields.append("base_url = ?")
            values.append(updates["base_url"])
        if "config" in updates:
            update_fields.append("config = ?")
            values.append(json.dumps(updates["config"]))
        if "status" in updates:
            update_fields.append("status = ?")
            values.append(updates["status"])
        if "last_tested" in updates:
            update_fields.append("last_tested = ?")
            values.append(updates["last_tested"])

        if not update_fields:
            conn.close()
            return await self.get_api_integration(integration_id)

        update_fields.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(integration_id)

        query = f"UPDATE api_integrations SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        return await self.get_api_integration(integration_id)

    async def remove_api_integration(self, integration_id: str) -> bool:
        """Remove an API integration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM api_integrations WHERE id = ?", (integration_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    # ==================== APPEARANCE SETTINGS ====================

    async def get_appearance_settings(self) -> Dict[str, Any]:
        """Get appearance settings."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM appearance_settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            settings = self._row_to_dict(row)
            settings["showAnimations"] = bool(settings.get("show_animations", 1))
            del settings["id"]
            del settings["show_animations"]
            return settings

        return {
            "density": "normal",
            "theme": "dark",
            "fontSize": 14,
            "accentColor": "#3b82f6",
            "showAnimations": True,
        }

    async def update_appearance_settings(
        self, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update appearance settings."""
        conn = self._get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []

        if "density" in settings:
            update_fields.append("density = ?")
            values.append(settings["density"])
        if "theme" in settings:
            update_fields.append("theme = ?")
            values.append(settings["theme"])
        if "fontSize" in settings:
            update_fields.append("font_size = ?")
            values.append(settings["fontSize"])
        if "accentColor" in settings:
            update_fields.append("accent_color = ?")
            values.append(settings["accentColor"])
        if "showAnimations" in settings:
            update_fields.append("show_animations = ?")
            values.append(1 if settings["showAnimations"] else 0)

        if update_fields:
            update_fields.append("updated_at = ?")
            values.append(datetime.utcnow().isoformat())

            query = f"UPDATE appearance_settings SET {', '.join(update_fields)} WHERE id = 1"
            cursor.execute(query, values)
            conn.commit()

        conn.close()

        return await self.get_appearance_settings()

    # ==================== CACHE OPERATIONS ====================

    async def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Clean up expired cache first
        cursor.execute(
            "DELETE FROM cache WHERE expires_at < ?", (datetime.utcnow().isoformat(),)
        )

        cursor.execute(
            "SELECT data FROM cache WHERE cache_key = ? AND expires_at > ?",
            (cache_key, datetime.utcnow().isoformat()),
        )
        row = cursor.fetchone()
        conn.commit()
        conn.close()

        if row:
            try:
                return json.loads(row["data"])
            except Exception:
                return None

        return None

    async def set_cached_data(
        self, cache_key: str, data: Dict[str, Any], ttl_seconds: int = 3600
    ) -> bool:
        """Set cached data with TTL."""
        conn = self._get_connection()
        cursor = conn.cursor()

        data_json = json.dumps(data)
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()

        # Use INSERT OR REPLACE to handle updates
        cursor.execute(
            """
            INSERT OR REPLACE INTO cache (cache_key, data, cached_at, expires_at)
            VALUES (?, ?, ?, ?)
        """,
            (cache_key, data_json, datetime.utcnow().isoformat(), expires_at),
        )

        conn.commit()
        conn.close()

        return True

    async def clear_cache(self, cache_key: Optional[str] = None) -> bool:
        """Clear cached data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if cache_key:
            cursor.execute("DELETE FROM cache WHERE cache_key = ?", (cache_key,))
        else:
            cursor.execute("DELETE FROM cache")

        conn.commit()
        conn.close()

        return True

    # ==================== RSS FEEDS ====================

    async def get_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get all RSS feeds."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rss_feeds ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        feeds = []
        for row in rows:
            feed = self._row_to_dict(row)
            feed["enabled"] = bool(feed.get("enabled", 1))
            feeds.append(feed)

        return feeds

    async def add_rss_feed(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new RSS feed."""
        conn = self._get_connection()
        cursor = conn.cursor()

        feed_id = str(uuid.uuid4())

        cursor.execute(
            """
            INSERT INTO rss_feeds (id, name, url, enabled, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                feed_id,
                feed.get("name", ""),
                feed.get("url", ""),
                1 if feed.get("enabled", True) else 0,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return {
            "id": feed_id,
            "name": feed.get("name", ""),
            "url": feed.get("url", ""),
            "enabled": feed.get("enabled", True),
            "last_fetched": None,
            "created_at": datetime.utcnow().isoformat(),
        }

    async def remove_rss_feed(self, feed_id: str) -> bool:
        """Remove an RSS feed."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    async def update_rss_feed(
        self, feed_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an RSS feed."""
        conn = self._get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []

        if "name" in updates:
            update_fields.append("name = ?")
            values.append(updates["name"])
        if "url" in updates:
            update_fields.append("url = ?")
            values.append(updates["url"])
        if "enabled" in updates:
            update_fields.append("enabled = ?")
            values.append(1 if updates["enabled"] else 0)
        if "last_fetched" in updates:
            update_fields.append("last_fetched = ?")
            values.append(updates["last_fetched"])

        if not update_fields:
            conn.close()
            # Return current feed
            cursor = self._get_connection().cursor()
            cursor.execute("SELECT * FROM rss_feeds WHERE id = ?", (feed_id,))
            row = cursor.fetchone()
            if row:
                feed = self._row_to_dict(row)
                feed["enabled"] = bool(feed.get("enabled", 1))
                return feed
            return None

        values.append(feed_id)

        query = f"UPDATE rss_feeds SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        # Return updated feed
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rss_feeds WHERE id = ?", (feed_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            feed = self._row_to_dict(row)
            feed["enabled"] = bool(feed.get("enabled", 1))
            return feed

        return None
