"""
Storage Factory for MT5_UI

Creates storage instances based on configuration.
Supports file-based, database, or synchronized hybrid storage.
"""

import os
from typing import Optional

from backend.storage.storage_interface import StorageInterface
from backend.storage.file_storage import FileStorage
from backend.storage.database_storage import DatabaseStorage


class SyncStorage(StorageInterface):
    """
    Synchronized storage that writes to both file and database.

    Keeps both storage methods in sync for seamless migration.
    Reads from primary storage, writes to both.
    """

    def __init__(self, primary: str = "file"):
        """
        Initialize synchronized storage.

        Args:
            primary: Primary storage to read from ('file' or 'database')
        """
        self.file_storage = FileStorage()
        self.db_storage = DatabaseStorage()
        self.primary = primary

    def _get_primary(self) -> StorageInterface:
        """Get primary storage instance."""
        return self.file_storage if self.primary == "file" else self.db_storage

    def _get_secondary(self) -> StorageInterface:
        """Get secondary storage instance."""
        return self.db_storage if self.primary == "file" else self.file_storage

    # ==================== ACCOUNTS ====================

    async def get_accounts(self):
        """Get all MT5 accounts from primary storage."""
        return await self._get_primary().get_accounts()

    async def get_account(self, account_id: str):
        """Get a specific account from primary storage."""
        return await self._get_primary().get_account(account_id)

    async def add_account(self, account):
        """Add account to both storages."""
        # Add to primary first
        result = await self._get_primary().add_account(account)

        # Sync to secondary
        try:
            await self._get_secondary().add_account(account)
        except Exception as e:
            print(f"Warning: Failed to sync account to secondary storage: {e}")

        return result

    async def update_account(self, account_id: str, updates):
        """Update account in both storages."""
        result = await self._get_primary().update_account(account_id, updates)

        try:
            await self._get_secondary().update_account(account_id, updates)
        except Exception as e:
            print(f"Warning: Failed to sync account update to secondary storage: {e}")

        return result

    async def remove_account(self, account_id: str):
        """Remove account from both storages."""
        result = await self._get_primary().remove_account(account_id)

        try:
            await self._get_secondary().remove_account(account_id)
        except Exception as e:
            print(f"Warning: Failed to sync account removal to secondary storage: {e}")

        return result

    async def get_active_account(self):
        """Get active account from primary storage."""
        return await self._get_primary().get_active_account()

    async def set_active_account(self, account_id: str):
        """Set active account in both storages."""
        result = await self._get_primary().set_active_account(account_id)

        try:
            await self._get_secondary().set_active_account(account_id)
        except Exception as e:
            print(f"Warning: Failed to sync active account to secondary storage: {e}")

        return result

    # ==================== API INTEGRATIONS ====================

    async def get_api_integrations(self):
        return await self._get_primary().get_api_integrations()

    async def get_api_integration(self, integration_id: str):
        return await self._get_primary().get_api_integration(integration_id)

    async def add_api_integration(self, integration):
        result = await self._get_primary().add_api_integration(integration)
        try:
            await self._get_secondary().add_api_integration(integration)
        except Exception as e:
            print(f"Warning: Failed to sync API integration to secondary storage: {e}")
        return result

    async def update_api_integration(self, integration_id: str, updates):
        result = await self._get_primary().update_api_integration(
            integration_id, updates
        )
        try:
            await self._get_secondary().update_api_integration(integration_id, updates)
        except Exception as e:
            print(
                f"Warning: Failed to sync API integration update to secondary storage: {e}"
            )
        return result

    async def remove_api_integration(self, integration_id: str):
        result = await self._get_primary().remove_api_integration(integration_id)
        try:
            await self._get_secondary().remove_api_integration(integration_id)
        except Exception as e:
            print(
                f"Warning: Failed to sync API integration removal to secondary storage: {e}"
            )
        return result

    # ==================== APPEARANCE SETTINGS ====================

    async def get_appearance_settings(self):
        return await self._get_primary().get_appearance_settings()

    async def update_appearance_settings(self, settings):
        result = await self._get_primary().update_appearance_settings(settings)
        try:
            await self._get_secondary().update_appearance_settings(settings)
        except Exception as e:
            print(
                f"Warning: Failed to sync appearance settings to secondary storage: {e}"
            )
        return result

    # ==================== CACHE OPERATIONS ====================

    async def get_cached_data(self, cache_key: str):
        return await self._get_primary().get_cached_data(cache_key)

    async def set_cached_data(self, cache_key: str, data, ttl_seconds: int = 3600):
        result = await self._get_primary().set_cached_data(cache_key, data, ttl_seconds)
        try:
            await self._get_secondary().set_cached_data(cache_key, data, ttl_seconds)
        except Exception as e:
            print(f"Warning: Failed to sync cache to secondary storage: {e}")
        return result

    async def clear_cache(self, cache_key: Optional[str] = None):
        result = await self._get_primary().clear_cache(cache_key)
        try:
            await self._get_secondary().clear_cache(cache_key)
        except Exception as e:
            print(f"Warning: Failed to sync cache clear to secondary storage: {e}")
        return result

    # ==================== RSS FEEDS ====================

    async def get_rss_feeds(self):
        return await self._get_primary().get_rss_feeds()

    async def add_rss_feed(self, feed):
        result = await self._get_primary().add_rss_feed(feed)
        try:
            await self._get_secondary().add_rss_feed(feed)
        except Exception as e:
            print(f"Warning: Failed to sync RSS feed to secondary storage: {e}")
        return result

    async def remove_rss_feed(self, feed_id: str):
        result = await self._get_primary().remove_rss_feed(feed_id)
        try:
            await self._get_secondary().remove_rss_feed(feed_id)
        except Exception as e:
            print(f"Warning: Failed to sync RSS feed removal to secondary storage: {e}")
        return result

    async def update_rss_feed(self, feed_id: str, updates):
        result = await self._get_primary().update_rss_feed(feed_id, updates)
        try:
            await self._get_secondary().update_rss_feed(feed_id, updates)
        except Exception as e:
            print(f"Warning: Failed to sync RSS feed update to secondary storage: {e}")
        return result


class StorageFactory:
    """Factory to create storage instances based on configuration."""

    @staticmethod
    def create_storage(
        storage_type: Optional[str] = None, sync_enabled: Optional[bool] = None
    ) -> StorageInterface:
        """
        Create storage instance based on configuration.

        Args:
            storage_type: Storage type ('file', 'database', 'sync').
                         If None, reads from STORAGE_TYPE env var (default: 'file')
            sync_enabled: Enable sync mode. If None, reads from STORAGE_SYNC_ENABLED env var

        Returns:
            StorageInterface instance
        """
        if storage_type is None:
            storage_type = os.getenv("STORAGE_TYPE", "file")

        if sync_enabled is None:
            sync_enabled = os.getenv("STORAGE_SYNC_ENABLED", "false").lower() == "true"

        # If sync is enabled, use SyncStorage
        if sync_enabled:
            primary = storage_type if storage_type in ("file", "database") else "file"
            return SyncStorage(primary=primary)

        # Otherwise, use single storage type
        if storage_type == "database":
            return DatabaseStorage()
        else:
            return FileStorage()


# Global storage instance
_storage_instance: Optional[StorageInterface] = None


def get_storage() -> StorageInterface:
    """
    Get global storage instance (singleton).

    Returns:
        StorageInterface instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageFactory.create_storage()
    return _storage_instance


def reset_storage():
    """Reset global storage instance (useful for testing)."""
    global _storage_instance
    _storage_instance = None
