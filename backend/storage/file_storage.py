"""
File-Based Storage Implementation for MT5_UI

Stores data in JSON files (current method).
Maintains compatibility with existing file structure.
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import asyncio

from backend.storage.storage_interface import StorageInterface
from backend.services.encryption_service import get_encryption_service


class FileStorage(StorageInterface):
    """File-based storage implementation using JSON files."""
    
    def __init__(self, config_dir: str = "config", data_dir: str = "data"):
        """
        Initialize file storage.
        
        Args:
            config_dir: Directory for configuration files
            data_dir: Directory for data/cache files
        """
        self.config_dir = Path(config_dir)
        self.data_dir = Path(data_dir)
        self.cache_dir = self.data_dir / "cache"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.accounts_file = self.config_dir / "accounts.json"
        self.integrations_file = self.config_dir / "api_integrations.json"
        self.appearance_file = self.config_dir / "appearance.json"
        self.rss_feeds_file = self.config_dir / "rss_feeds.json"
        
        # Encryption service
        self.encryption = get_encryption_service()
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize JSON files with default data if they don't exist."""
        if not self.accounts_file.exists():
            self._write_json(self.accounts_file, {
                "accounts": [],
                "active_account_id": None
            })
        
        if not self.integrations_file.exists():
            self._write_json(self.integrations_file, {"integrations": []})
        
        if not self.appearance_file.exists():
            self._write_json(self.appearance_file, {
                "density": "normal",
                "theme": "dark",
                "fontSize": 14,
                "accentColor": "#3b82f6",
                "showAnimations": True
            })
        
        if not self.rss_feeds_file.exists():
            self._write_json(self.rss_feeds_file, {"feeds": []})
    
    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return {}
    
    def _write_json(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
    
    # ==================== ACCOUNTS ====================
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all MT5 accounts."""
        data = self._read_json(self.accounts_file)
        accounts = data.get("accounts", [])
        
        # Decrypt passwords for internal use (will be masked in API responses)
        decrypted_accounts = []
        for account in accounts:
            acc = account.copy()
            if "password_encrypted" in acc:
                try:
                    acc["password"] = self.encryption.decrypt(acc["password_encrypted"])
                except Exception:
                    acc["password"] = ""
            decrypted_accounts.append(acc)
        
        return decrypted_accounts
    
    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific account by ID."""
        accounts = await self.get_accounts()
        for account in accounts:
            if account.get("id") == account_id:
                return account
        return None
    
    async def add_account(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new MT5 account."""
        data = self._read_json(self.accounts_file)
        accounts = data.get("accounts", [])
        
        # Generate ID and timestamps
        new_account = {
            "id": str(uuid.uuid4()),
            "name": account.get("name", ""),
            "login": account.get("login", 0),
            "password_encrypted": self.encryption.encrypt(account.get("password", "")),
            "server": account.get("server", ""),
            "is_active": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        accounts.append(new_account)
        data["accounts"] = accounts
        self._write_json(self.accounts_file, data)
        
        # Return account with decrypted password
        result = new_account.copy()
        result["password"] = account.get("password", "")
        return result
    
    async def update_account(self, account_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing account."""
        data = self._read_json(self.accounts_file)
        accounts = data.get("accounts", [])
        
        for i, account in enumerate(accounts):
            if account.get("id") == account_id:
                # Update fields
                if "name" in updates:
                    account["name"] = updates["name"]
                if "login" in updates:
                    account["login"] = updates["login"]
                if "password" in updates:
                    account["password_encrypted"] = self.encryption.encrypt(updates["password"])
                if "server" in updates:
                    account["server"] = updates["server"]
                
                account["updated_at"] = datetime.utcnow().isoformat()
                accounts[i] = account
                data["accounts"] = accounts
                self._write_json(self.accounts_file, data)
                
                # Return updated account
                result = account.copy()
                if "password_encrypted" in result:
                    result["password"] = self.encryption.decrypt(result["password_encrypted"])
                return result
        
        return None
    
    async def remove_account(self, account_id: str) -> bool:
        """Remove an account."""
        data = self._read_json(self.accounts_file)
        accounts = data.get("accounts", [])
        
        initial_count = len(accounts)
        accounts = [acc for acc in accounts if acc.get("id") != account_id]
        
        if len(accounts) < initial_count:
            data["accounts"] = accounts
            # Clear active account if it was removed
            if data.get("active_account_id") == account_id:
                data["active_account_id"] = None
            self._write_json(self.accounts_file, data)
            return True
        
        return False
    
    async def get_active_account(self) -> Optional[Dict[str, Any]]:
        """Get the currently active account."""
        data = self._read_json(self.accounts_file)
        active_id = data.get("active_account_id")
        
        if active_id:
            return await self.get_account(active_id)
        
        return None
    
    async def set_active_account(self, account_id: str) -> bool:
        """Set the active account."""
        data = self._read_json(self.accounts_file)
        accounts = data.get("accounts", [])
        
        # Check if account exists
        account_exists = any(acc.get("id") == account_id for acc in accounts)
        if not account_exists:
            return False
        
        # Deactivate all accounts
        for account in accounts:
            account["is_active"] = False
        
        # Activate the specified account
        for account in accounts:
            if account.get("id") == account_id:
                account["is_active"] = True
                break
        
        data["accounts"] = accounts
        data["active_account_id"] = account_id
        self._write_json(self.accounts_file, data)
        
        return True
    
    # ==================== API INTEGRATIONS ====================
    
    async def get_api_integrations(self) -> List[Dict[str, Any]]:
        """Get all API integrations."""
        data = self._read_json(self.integrations_file)
        integrations = data.get("integrations", [])
        
        # Decrypt API keys
        decrypted_integrations = []
        for integration in integrations:
            integ = integration.copy()
            if "api_key_encrypted" in integ:
                try:
                    integ["api_key"] = self.encryption.decrypt(integ["api_key_encrypted"])
                except Exception:
                    integ["api_key"] = ""
            decrypted_integrations.append(integ)
        
        return decrypted_integrations
    
    async def get_api_integration(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific API integration by ID."""
        integrations = await self.get_api_integrations()
        for integration in integrations:
            if integration.get("id") == integration_id:
                return integration
        return None
    
    async def add_api_integration(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new API integration."""
        data = self._read_json(self.integrations_file)
        integrations = data.get("integrations", [])
        
        new_integration = {
            "id": str(uuid.uuid4()),
            "name": integration.get("name", ""),
            "type": integration.get("type", "custom"),
            "api_key_encrypted": self.encryption.encrypt(integration.get("api_key", "")),
            "base_url": integration.get("base_url", ""),
            "config": integration.get("config", {}),
            "status": "inactive",
            "last_tested": None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        integrations.append(new_integration)
        data["integrations"] = integrations
        self._write_json(self.integrations_file, data)
        
        # Return with decrypted API key
        result = new_integration.copy()
        result["api_key"] = integration.get("api_key", "")
        return result

    async def update_api_integration(self, integration_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing API integration."""
        data = self._read_json(self.integrations_file)
        integrations = data.get("integrations", [])

        for i, integration in enumerate(integrations):
            if integration.get("id") == integration_id:
                # Update fields
                if "name" in updates:
                    integration["name"] = updates["name"]
                if "type" in updates:
                    integration["type"] = updates["type"]
                if "api_key" in updates:
                    integration["api_key_encrypted"] = self.encryption.encrypt(updates["api_key"])
                if "base_url" in updates:
                    integration["base_url"] = updates["base_url"]
                if "config" in updates:
                    integration["config"] = updates["config"]
                if "status" in updates:
                    integration["status"] = updates["status"]
                if "last_tested" in updates:
                    integration["last_tested"] = updates["last_tested"]

                integrations[i] = integration
                data["integrations"] = integrations
                self._write_json(self.integrations_file, data)

                # Return updated integration
                result = integration.copy()
                if "api_key_encrypted" in result:
                    result["api_key"] = self.encryption.decrypt(result["api_key_encrypted"])
                return result

        return None

    async def remove_api_integration(self, integration_id: str) -> bool:
        """Remove an API integration."""
        data = self._read_json(self.integrations_file)
        integrations = data.get("integrations", [])

        initial_count = len(integrations)
        integrations = [integ for integ in integrations if integ.get("id") != integration_id]

        if len(integrations) < initial_count:
            data["integrations"] = integrations
            self._write_json(self.integrations_file, data)
            return True

        return False

    # ==================== APPEARANCE SETTINGS ====================

    async def get_appearance_settings(self) -> Dict[str, Any]:
        """Get appearance settings."""
        return self._read_json(self.appearance_file)

    async def update_appearance_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update appearance settings."""
        current = self._read_json(self.appearance_file)
        current.update(settings)
        self._write_json(self.appearance_file, current)
        return current

    # ==================== CACHE OPERATIONS ====================

    async def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key."""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            data = self._read_json(cache_file)

            # Check if cache is expired
            if "expires_at" in data:
                expires_at = datetime.fromisoformat(data["expires_at"])
                if datetime.utcnow() > expires_at:
                    # Cache expired, remove file
                    cache_file.unlink()
                    return None

            return data.get("data")
        except Exception as e:
            print(f"Error reading cache {cache_key}: {e}")
            return None

    async def set_cached_data(self, cache_key: str, data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Set cached data with TTL."""
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            cache_data = {
                "data": data,
                "cached_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
            }
            self._write_json(cache_file, cache_data)
            return True
        except Exception as e:
            print(f"Error writing cache {cache_key}: {e}")
            return False

    async def clear_cache(self, cache_key: Optional[str] = None) -> bool:
        """Clear cached data."""
        try:
            if cache_key:
                # Clear specific cache
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()
            else:
                # Clear all caches
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

    # ==================== RSS FEEDS ====================

    async def get_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get all RSS feeds."""
        data = self._read_json(self.rss_feeds_file)
        return data.get("feeds", [])

    async def add_rss_feed(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new RSS feed."""
        data = self._read_json(self.rss_feeds_file)
        feeds = data.get("feeds", [])

        new_feed = {
            "id": str(uuid.uuid4()),
            "name": feed.get("name", ""),
            "url": feed.get("url", ""),
            "enabled": feed.get("enabled", True),
            "last_fetched": None,
            "created_at": datetime.utcnow().isoformat()
        }

        feeds.append(new_feed)
        data["feeds"] = feeds
        self._write_json(self.rss_feeds_file, data)

        return new_feed

    async def remove_rss_feed(self, feed_id: str) -> bool:
        """Remove an RSS feed."""
        data = self._read_json(self.rss_feeds_file)
        feeds = data.get("feeds", [])

        initial_count = len(feeds)
        feeds = [feed for feed in feeds if feed.get("id") != feed_id]

        if len(feeds) < initial_count:
            data["feeds"] = feeds
            self._write_json(self.rss_feeds_file, data)
            return True

        return False

    async def update_rss_feed(self, feed_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an RSS feed."""
        data = self._read_json(self.rss_feeds_file)
        feeds = data.get("feeds", [])

        for i, feed in enumerate(feeds):
            if feed.get("id") == feed_id:
                # Update fields
                if "name" in updates:
                    feed["name"] = updates["name"]
                if "url" in updates:
                    feed["url"] = updates["url"]
                if "enabled" in updates:
                    feed["enabled"] = updates["enabled"]
                if "last_fetched" in updates:
                    feed["last_fetched"] = updates["last_fetched"]

                feeds[i] = feed
                data["feeds"] = feeds
                self._write_json(self.rss_feeds_file, data)

                return feed

        return None

