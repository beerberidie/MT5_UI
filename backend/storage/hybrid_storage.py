"""
Hybrid storage implementation.

Writes to both CSV (legacy) and PostgreSQL (new) for gradual migration.
Reads from PostgreSQL by default, falls back to CSV if needed.
"""

from typing import Any, Dict, List, Optional
import logging
import os

from backend.storage.storage_interface import StorageInterface
from backend.storage.file_storage import FileStorage
from backend.storage.postgres_storage import PostgresStorage

logger = logging.getLogger(__name__)


class HybridStorage(StorageInterface):
    """
    Hybrid storage that writes to both CSV and PostgreSQL.
    
    Features:
    - Dual-write mode: All writes go to both backends
    - PostgreSQL-first reads: Read from PostgreSQL, fallback to CSV
    - Feature flag support: Can switch between backends
    - Gradual migration path
    """
    
    def __init__(self):
        """Initialize hybrid storage with both backends."""
        self.file_storage = FileStorage()
        self.postgres_storage = PostgresStorage()
        
        # Feature flags (from environment)
        self.use_postgres = os.getenv("USE_POSTGRES", "true").lower() == "true"
        self.dual_write = os.getenv("DUAL_WRITE", "true").lower() == "true"
        
        logger.info(f"HybridStorage initialized: use_postgres={self.use_postgres}, dual_write={self.dual_write}")
    
    async def _read_with_fallback(self, postgres_method, file_method, *args, **kwargs):
        """
        Read from PostgreSQL first, fallback to CSV if error.
        
        Args:
            postgres_method: Async method to call on postgres_storage
            file_method: Sync method to call on file_storage
            *args, **kwargs: Arguments to pass to methods
        
        Returns:
            Data from PostgreSQL or CSV fallback
        """
        if self.use_postgres:
            try:
                return await postgres_method(*args, **kwargs)
            except Exception as e:
                logger.warning(f"PostgreSQL read failed, falling back to CSV: {e}")
                return file_method(*args, **kwargs)
        else:
            return file_method(*args, **kwargs)
    
    async def _write_dual(self, postgres_method, file_method, *args, **kwargs):
        """
        Write to both PostgreSQL and CSV.
        
        Args:
            postgres_method: Async method to call on postgres_storage
            file_method: Sync method to call on file_storage
            *args, **kwargs: Arguments to pass to methods
        
        Returns:
            Result from primary storage (PostgreSQL if enabled, else CSV)
        """
        errors = []
        result = None
        
        # Write to PostgreSQL
        if self.use_postgres:
            try:
                result = await postgres_method(*args, **kwargs)
            except Exception as e:
                logger.error(f"PostgreSQL write failed: {e}")
                errors.append(("postgres", e))
        
        # Write to CSV (if dual-write enabled or PostgreSQL disabled)
        if self.dual_write or not self.use_postgres:
            try:
                csv_result = file_method(*args, **kwargs)
                if result is None:
                    result = csv_result
            except Exception as e:
                logger.error(f"CSV write failed: {e}")
                errors.append(("csv", e))
        
        # If both failed, raise exception
        if errors and result is None:
            raise Exception(f"All storage backends failed: {errors}")
        
        return result
    
    # Settings methods
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get MT5 account configurations."""
        # Always use file storage for accounts (not migrated yet)
        return self.file_storage.get_accounts()
    
    async def save_accounts(self, accounts: List[Dict[str, Any]]) -> None:
        """Save MT5 account configurations."""
        # Always use file storage for accounts (not migrated yet)
        self.file_storage.save_accounts(accounts)
    
    async def get_api_integrations(self) -> Dict[str, Any]:
        """Get API integration settings."""
        # Always use file storage for API integrations (not migrated yet)
        return self.file_storage.get_api_integrations()
    
    async def save_api_integrations(self, integrations: Dict[str, Any]) -> None:
        """Save API integration settings."""
        # Always use file storage for API integrations (not migrated yet)
        self.file_storage.save_api_integrations(integrations)
    
    async def get_appearance(self) -> Dict[str, Any]:
        """Get appearance settings."""
        # Always use file storage for appearance (not migrated yet)
        return self.file_storage.get_appearance()
    
    async def save_appearance(self, appearance: Dict[str, Any]) -> None:
        """Save appearance settings."""
        # Always use file storage for appearance (not migrated yet)
        self.file_storage.save_appearance(appearance)
    
    async def get_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get RSS feed sources."""
        # Always use file storage for RSS feeds (not migrated yet)
        return self.file_storage.get_rss_feeds()
    
    async def save_rss_feeds(self, feeds: List[Dict[str, Any]]) -> None:
        """Save RSS feed sources."""
        # Always use file storage for RSS feeds (not migrated yet)
        self.file_storage.save_rss_feeds(feeds)
    
    # Risk Config methods (migrated to PostgreSQL)
    async def get_risk_config(self) -> Dict[str, Any]:
        """Get risk configuration."""
        return await self._read_with_fallback(
            self.postgres_storage.get_risk_config,
            self.file_storage.get_risk_config
        )
    
    async def save_risk_config(self, config: Dict[str, Any]) -> None:
        """Save risk configuration."""
        await self._write_dual(
            self.postgres_storage.save_risk_config,
            self.file_storage.save_risk_config,
            config
        )
    
    # Strategy methods (migrated to PostgreSQL)
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategies."""
        return await self._read_with_fallback(
            self.postgres_storage.get_strategies,
            self.file_storage.get_strategies
        )
    
    async def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get a single strategy by ID."""
        return await self._read_with_fallback(
            self.postgres_storage.get_strategy,
            self.file_storage.get_strategy,
            strategy_id
        )
    
    async def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Save or update a strategy."""
        return await self._write_dual(
            self.postgres_storage.save_strategy,
            self.file_storage.save_strategy,
            strategy_data
        )
    
    async def delete_strategy(self, strategy_id: str) -> None:
        """Delete a strategy."""
        await self._write_dual(
            self.postgres_storage.delete_strategy,
            self.file_storage.delete_strategy,
            strategy_id
        )
    
    # Snapshot methods (PostgreSQL only - new feature)
    async def save_market_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save market snapshot."""
        return await self.postgres_storage.save_market_snapshot(snapshot)
    
    async def save_indicators_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save indicators snapshot."""
        return await self.postgres_storage.save_indicators_snapshot(snapshot)
    
    async def save_account_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save account snapshot."""
        return await self.postgres_storage.save_account_snapshot(snapshot)
    
    async def save_calendar_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save calendar snapshot."""
        return await self.postgres_storage.save_calendar_snapshot(snapshot)
    
    async def save_news_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save news snapshot."""
        return await self.postgres_storage.save_news_snapshot(snapshot)
    
    # Trade Ideas methods (PostgreSQL only - new feature)
    async def save_trade_idea(self, idea: Dict[str, Any]) -> str:
        """Save trade idea."""
        return await self.postgres_storage.save_trade_idea(idea)
    
    async def get_active_trade_ideas(self) -> List[Dict[str, Any]]:
        """Get active trade ideas."""
        return await self.postgres_storage.get_active_trade_ideas()
    
    # Decision History methods (PostgreSQL only - new feature)
    async def save_decision(self, decision: Dict[str, Any]) -> str:
        """Save decision history entry."""
        return await self.postgres_storage.save_decision(decision)
    
    async def get_decision_history(
        self,
        symbol: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get decision history with optional filters."""
        return await self.postgres_storage.get_decision_history(symbol, action, limit)
    
    # Migration utilities
    async def migrate_csv_to_postgres(self) -> Dict[str, int]:
        """
        Migrate all CSV data to PostgreSQL.
        
        Returns:
            Dict with counts of migrated items
        """
        logger.info("Starting CSV to PostgreSQL migration...")
        
        counts = {
            "risk_config": 0,
            "strategies": 0,
            "errors": 0
        }
        
        try:
            # Migrate risk config
            risk_config = self.file_storage.get_risk_config()
            await self.postgres_storage.save_risk_config(risk_config)
            counts["risk_config"] = 1
            logger.info("Migrated risk config")
        except Exception as e:
            logger.error(f"Failed to migrate risk config: {e}")
            counts["errors"] += 1
        
        try:
            # Migrate strategies
            strategies = self.file_storage.get_strategies()
            for strategy in strategies:
                await self.postgres_storage.save_strategy(strategy)
                counts["strategies"] += 1
            logger.info(f"Migrated {counts['strategies']} strategies")
        except Exception as e:
            logger.error(f"Failed to migrate strategies: {e}")
            counts["errors"] += 1
        
        logger.info(f"Migration complete: {counts}")
        return counts

