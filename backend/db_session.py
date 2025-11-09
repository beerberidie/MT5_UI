"""
Database session management for PostgreSQL.

Provides async database session handling with connection pooling.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os
from contextlib import asynccontextmanager

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://trader:trader@localhost:5432/ai_trader"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max overflow connections
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database session.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Use db session
            pass
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database session (for use outside FastAPI).
    
    Usage:
        async with get_db_context() as db:
            # Use db session
            pass
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database schema.
    
    Creates all tables defined in database.py if they don't exist.
    Should be called on application startup.
    """
    from backend.database import Base
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Initialize risk_config with default values if not exists
        from backend.database import RiskConfig
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RiskConfig))
            risk_config = result.scalar_one_or_none()
            
            if not risk_config:
                # Create default risk config
                default_config = RiskConfig(
                    id=True,
                    ai_trading_enabled=False,
                    min_confidence_threshold=90.0,
                    max_lot_size=1.0,
                    max_concurrent_trades=3,
                    daily_profit_target=2000.0,
                    stop_after_target=True,
                    max_drawdown_amount=1000.0,
                    halt_on_drawdown=True,
                    allow_off_watchlist_autotrade=False,
                    last_halt_reason=None
                )
                session.add(default_config)
                await session.commit()


async def close_db():
    """
    Close database connections.
    
    Should be called on application shutdown.
    """
    await engine.dispose()


# For testing: create engine with NullPool
def create_test_engine(database_url: str = None):
    """
    Create a test database engine with NullPool.
    
    Args:
        database_url: Optional test database URL
    
    Returns:
        AsyncEngine: Test database engine
    """
    test_url = database_url or "postgresql+asyncpg://trader:trader@localhost:5432/ai_trader_test"
    
    return create_async_engine(
        test_url,
        echo=True,
        future=True,
        poolclass=NullPool,  # No connection pooling for tests
    )

