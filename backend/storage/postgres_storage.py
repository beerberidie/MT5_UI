"""
PostgreSQL storage implementation.

Provides async PostgreSQL storage for AI Trading Platform data.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.storage.storage_interface import StorageInterface
from backend.db_session import get_db_context
from backend.database import (
    Strategy,
    RiskConfig,
    SnapshotMarket,
    SnapshotIndicators,
    SnapshotCalendar,
    SnapshotNews,
    SnapshotAccount,
    TradeIdea,
    DecisionHistory,
    User,
    TradeIdeaStatus,
    DecisionAction,
)


class PostgresStorage(StorageInterface):
    """PostgreSQL storage implementation using SQLAlchemy async."""

    def __init__(self):
        """Initialize PostgreSQL storage."""
        pass

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        async with get_db_context() as session:
            return session

    # Settings methods
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Get MT5 account configurations."""
        # For now, delegate to file storage for accounts
        # TODO: Migrate accounts to database
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        return file_storage.get_accounts()

    async def save_accounts(self, accounts: List[Dict[str, Any]]) -> None:
        """Save MT5 account configurations."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        file_storage.save_accounts(accounts)

    async def get_api_integrations(self) -> Dict[str, Any]:
        """Get API integration settings."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        return file_storage.get_api_integrations()

    async def save_api_integrations(self, integrations: Dict[str, Any]) -> None:
        """Save API integration settings."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        file_storage.save_api_integrations(integrations)

    async def get_appearance(self) -> Dict[str, Any]:
        """Get appearance settings."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        return file_storage.get_appearance()

    async def save_appearance(self, appearance: Dict[str, Any]) -> None:
        """Save appearance settings."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        file_storage.save_appearance(appearance)

    async def get_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get RSS feed sources."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        return file_storage.get_rss_feeds()

    async def save_rss_feeds(self, feeds: List[Dict[str, Any]]) -> None:
        """Save RSS feed sources."""
        # For now, delegate to file storage
        from backend.storage.file_storage import FileStorage

        file_storage = FileStorage()
        file_storage.save_rss_feeds(feeds)

    # Risk Config methods (PostgreSQL)
    async def get_risk_config(self) -> Dict[str, Any]:
        """Get risk configuration from database."""
        async with get_db_context() as session:
            result = await session.execute(select(RiskConfig))
            config = result.scalar_one_or_none()

            if not config:
                # Return default config
                return {
                    "ai_trading_enabled": False,
                    "min_confidence_threshold": 90.0,
                    "max_lot_size": 1.0,
                    "max_concurrent_trades": 3,
                    "daily_profit_target": 2000.0,
                    "stop_after_target": True,
                    "max_drawdown_amount": 1000.0,
                    "halt_on_drawdown": True,
                    "allow_off_watchlist_autotrade": False,
                    "last_halt_reason": None,
                }

            return {
                "ai_trading_enabled": config.ai_trading_enabled,
                "min_confidence_threshold": float(config.min_confidence_threshold),
                "max_lot_size": float(config.max_lot_size),
                "max_concurrent_trades": config.max_concurrent_trades,
                "daily_profit_target": float(config.daily_profit_target),
                "stop_after_target": config.stop_after_target,
                "max_drawdown_amount": float(config.max_drawdown_amount),
                "halt_on_drawdown": config.halt_on_drawdown,
                "allow_off_watchlist_autotrade": config.allow_off_watchlist_autotrade,
                "last_halt_reason": config.last_halt_reason,
            }

    async def save_risk_config(self, config: Dict[str, Any]) -> None:
        """Save risk configuration to database."""
        async with get_db_context() as session:
            # Check if config exists
            result = await session.execute(select(RiskConfig))
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                await session.execute(update(RiskConfig).values(**config))
            else:
                # Create new
                new_config = RiskConfig(id=True, **config)
                session.add(new_config)

            await session.commit()

    # Strategy methods (PostgreSQL)
    async def get_strategies(self) -> List[Dict[str, Any]]:
        """Get all strategies from database."""
        async with get_db_context() as session:
            result = await session.execute(select(Strategy))
            strategies = result.scalars().all()

            return [
                {
                    "id": str(strategy.id),
                    "name": strategy.name,
                    "is_active": strategy.is_active,
                    "allowed_symbols": strategy.allowed_symbols,
                    "session_windows": strategy.session_windows,
                    "entry_conditions": strategy.entry_conditions,
                    "exit_rules": strategy.exit_rules,
                    "forbidden_conditions": strategy.forbidden_conditions,
                    "risk_caps": strategy.risk_caps,
                    "rr_expectation": float(strategy.rr_expectation),
                    "created_at": strategy.created_at.isoformat(),
                    "updated_at": strategy.updated_at.isoformat(),
                }
                for strategy in strategies
            ]

    async def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get a single strategy by ID."""
        async with get_db_context() as session:
            result = await session.execute(
                select(Strategy).where(Strategy.id == uuid.UUID(strategy_id))
            )
            strategy = result.scalar_one_or_none()

            if not strategy:
                return None

            return {
                "id": str(strategy.id),
                "name": strategy.name,
                "is_active": strategy.is_active,
                "allowed_symbols": strategy.allowed_symbols,
                "session_windows": strategy.session_windows,
                "entry_conditions": strategy.entry_conditions,
                "exit_rules": strategy.exit_rules,
                "forbidden_conditions": strategy.forbidden_conditions,
                "risk_caps": strategy.risk_caps,
                "rr_expectation": float(strategy.rr_expectation),
                "created_at": strategy.created_at.isoformat(),
                "updated_at": strategy.updated_at.isoformat(),
            }

    async def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Save or update a strategy."""
        async with get_db_context() as session:
            strategy_id = strategy_data.get("id")

            if strategy_id:
                # Update existing
                await session.execute(
                    update(Strategy)
                    .where(Strategy.id == uuid.UUID(strategy_id))
                    .values(**{k: v for k, v in strategy_data.items() if k != "id"})
                )
                return strategy_id
            else:
                # Create new
                new_strategy = Strategy(**strategy_data)
                session.add(new_strategy)
                await session.flush()
                return str(new_strategy.id)

    async def delete_strategy(self, strategy_id: str) -> None:
        """Delete a strategy."""
        async with get_db_context() as session:
            await session.execute(
                delete(Strategy).where(Strategy.id == uuid.UUID(strategy_id))
            )

    # Snapshot methods (PostgreSQL)
    async def save_market_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save market snapshot."""
        async with get_db_context() as session:
            new_snapshot = SnapshotMarket(**snapshot)
            session.add(new_snapshot)
            await session.flush()
            return str(new_snapshot.id)

    async def save_indicators_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save indicators snapshot."""
        async with get_db_context() as session:
            new_snapshot = SnapshotIndicators(**snapshot)
            session.add(new_snapshot)
            await session.flush()
            return str(new_snapshot.id)

    async def save_account_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save account snapshot."""
        async with get_db_context() as session:
            new_snapshot = SnapshotAccount(**snapshot)
            session.add(new_snapshot)
            await session.flush()
            return str(new_snapshot.id)

    async def save_calendar_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save calendar snapshot."""
        async with get_db_context() as session:
            new_snapshot = SnapshotCalendar(**snapshot)
            session.add(new_snapshot)
            await session.flush()
            return str(new_snapshot.id)

    async def save_news_snapshot(self, snapshot: Dict[str, Any]) -> str:
        """Save news snapshot."""
        async with get_db_context() as session:
            new_snapshot = SnapshotNews(**snapshot)
            session.add(new_snapshot)
            await session.flush()
            return str(new_snapshot.id)

    # Trade Ideas methods (PostgreSQL)
    async def save_trade_idea(self, idea: Dict[str, Any]) -> str:
        """Save trade idea."""
        async with get_db_context() as session:
            new_idea = TradeIdea(**idea)
            session.add(new_idea)
            await session.flush()
            return str(new_idea.id)

    async def get_active_trade_ideas(self) -> List[Dict[str, Any]]:
        """Get active trade ideas."""
        async with get_db_context() as session:
            result = await session.execute(
                select(TradeIdea)
                .where(
                    TradeIdea.status.in_(
                        [TradeIdeaStatus.WAITING, TradeIdeaStatus.NEEDS_APPROVAL]
                    )
                )
                .order_by(TradeIdea.created_at.desc())
            )
            ideas = result.scalars().all()

            return [
                {
                    "id": str(idea.id),
                    "symbol": idea.symbol,
                    "direction": idea.direction,
                    "entry_price": (
                        float(idea.entry_price) if idea.entry_price else None
                    ),
                    "stop_loss": float(idea.stop_loss),
                    "take_profit": [float(tp) for tp in idea.take_profit],
                    "rationale": idea.rationale,
                    "confidence_score": float(idea.confidence_score),
                    "status": idea.status.value,
                    "created_at": idea.created_at.isoformat(),
                }
                for idea in ideas
            ]

    # Decision History methods (PostgreSQL)
    async def save_decision(self, decision: Dict[str, Any]) -> str:
        """Save decision history entry."""
        async with get_db_context() as session:
            new_decision = DecisionHistory(**decision)
            session.add(new_decision)
            await session.flush()
            return str(new_decision.id)

    async def get_decision_history(
        self,
        symbol: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get decision history with optional filters."""
        async with get_db_context() as session:
            query = select(DecisionHistory)

            if symbol:
                query = query.where(DecisionHistory.symbol == symbol)
            if action:
                query = query.where(DecisionHistory.action == DecisionAction(action))

            query = query.order_by(DecisionHistory.occurred_at.desc()).limit(limit)

            result = await session.execute(query)
            decisions = result.scalars().all()

            return [
                {
                    "id": str(decision.id),
                    "occurred_at": decision.occurred_at.isoformat(),
                    "symbol": decision.symbol,
                    "action": decision.action.value,
                    "rationale": decision.rationale,
                    "confidence_score": (
                        float(decision.confidence_score)
                        if decision.confidence_score
                        else None
                    ),
                    "risk_check_result": decision.risk_check_result,
                    "human_override": decision.human_override,
                }
                for decision in decisions
            ]
