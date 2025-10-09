"""
Storage Interface for MT5_UI

Abstract interface for storage operations supporting multiple backends
(file-based, database, or synchronized hybrid).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class StorageInterface(ABC):
    """Abstract interface for storage operations."""
    
    # ==================== ACCOUNTS ====================
    
    @abstractmethod
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all MT5 accounts.
        
        Returns:
            List of account dictionaries
        """
        pass
    
    @abstractmethod
    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific account by ID.
        
        Args:
            account_id: Account ID
            
        Returns:
            Account dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def add_account(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new MT5 account.
        
        Args:
            account: Account data (name, login, password, server)
            
        Returns:
            Created account with ID
        """
        pass
    
    @abstractmethod
    async def update_account(self, account_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing account.
        
        Args:
            account_id: Account ID
            updates: Fields to update
            
        Returns:
            Updated account or None if not found
        """
        pass
    
    @abstractmethod
    async def remove_account(self, account_id: str) -> bool:
        """
        Remove an account.
        
        Args:
            account_id: Account ID
            
        Returns:
            True if removed, False if not found
        """
        pass
    
    @abstractmethod
    async def get_active_account(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active account.
        
        Returns:
            Active account or None
        """
        pass
    
    @abstractmethod
    async def set_active_account(self, account_id: str) -> bool:
        """
        Set the active account.
        
        Args:
            account_id: Account ID to activate
            
        Returns:
            True if successful, False if account not found
        """
        pass
    
    # ==================== API INTEGRATIONS ====================
    
    @abstractmethod
    async def get_api_integrations(self) -> List[Dict[str, Any]]:
        """
        Get all API integrations.
        
        Returns:
            List of API integration dictionaries
        """
        pass
    
    @abstractmethod
    async def get_api_integration(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific API integration by ID.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def add_api_integration(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new API integration.
        
        Args:
            integration: Integration data (name, type, api_key, etc.)
            
        Returns:
            Created integration with ID
        """
        pass
    
    @abstractmethod
    async def update_api_integration(self, integration_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing API integration.
        
        Args:
            integration_id: Integration ID
            updates: Fields to update
            
        Returns:
            Updated integration or None if not found
        """
        pass
    
    @abstractmethod
    async def remove_api_integration(self, integration_id: str) -> bool:
        """
        Remove an API integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            True if removed, False if not found
        """
        pass
    
    # ==================== APPEARANCE SETTINGS ====================
    
    @abstractmethod
    async def get_appearance_settings(self) -> Dict[str, Any]:
        """
        Get appearance settings.
        
        Returns:
            Appearance settings dictionary
        """
        pass
    
    @abstractmethod
    async def update_appearance_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update appearance settings.
        
        Args:
            settings: Settings to update
            
        Returns:
            Updated settings
        """
        pass
    
    # ==================== CACHE OPERATIONS ====================
    
    @abstractmethod
    async def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key.
        
        Args:
            cache_key: Cache key (e.g., 'economic_calendar', 'market_news')
            
        Returns:
            Cached data or None if not found or expired
        """
        pass
    
    @abstractmethod
    async def set_cached_data(self, cache_key: str, data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """
        Set cached data with TTL.
        
        Args:
            cache_key: Cache key
            data: Data to cache
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def clear_cache(self, cache_key: Optional[str] = None) -> bool:
        """
        Clear cached data.
        
        Args:
            cache_key: Specific cache key to clear, or None to clear all
            
        Returns:
            True if successful
        """
        pass
    
    # ==================== RSS FEEDS ====================
    
    @abstractmethod
    async def get_rss_feeds(self) -> List[Dict[str, Any]]:
        """
        Get all RSS feeds.
        
        Returns:
            List of RSS feed dictionaries
        """
        pass
    
    @abstractmethod
    async def add_rss_feed(self, feed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new RSS feed.
        
        Args:
            feed: Feed data (name, url)
            
        Returns:
            Created feed with ID
        """
        pass
    
    @abstractmethod
    async def remove_rss_feed(self, feed_id: str) -> bool:
        """
        Remove an RSS feed.
        
        Args:
            feed_id: Feed ID
            
        Returns:
            True if removed, False if not found
        """
        pass
    
    @abstractmethod
    async def update_rss_feed(self, feed_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an RSS feed.
        
        Args:
            feed_id: Feed ID
            updates: Fields to update
            
        Returns:
            Updated feed or None if not found
        """
        pass

