"""
PostgreSQL database setup script.

This script:
1. Creates the database if it doesn't exist
2. Runs Alembic migrations to create schema
3. Initializes default data (risk_config)
4. Optionally migrates CSV data to PostgreSQL
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from backend.db_session import init_db, close_db, DATABASE_URL
from backend.storage.hybrid_storage import HybridStorage


async def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    # Parse database URL
    # Format: postgresql+asyncpg://user:password@host:port/database
    parts = DATABASE_URL.replace("postgresql+asyncpg://", "").split("/")
    connection_string = parts[0]
    database_name = parts[1] if len(parts) > 1 else "ai_trader"

    user_pass_host = connection_string.split("@")
    user_pass = user_pass_host[0].split(":")
    host_port = user_pass_host[1].split(":")

    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ""
    host = host_port[0]
    port = int(host_port[1]) if len(host_port) > 1 else 5432

    print(f"Connecting to PostgreSQL at {host}:{port} as {user}...")

    try:
        # Connect to default 'postgres' database
        conn = await asyncpg.connect(
            user=user, password=password, host=host, port=port, database="postgres"
        )

        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", database_name
        )

        if not exists:
            print(f"Creating database '{database_name}'...")
            await conn.execute(f"CREATE DATABASE {database_name}")
            print(f"✅ Database '{database_name}' created successfully!")
        else:
            print(f"✅ Database '{database_name}' already exists.")

        await conn.close()

    except asyncpg.InvalidPasswordError:
        print("❌ ERROR: Invalid PostgreSQL credentials.")
        print("Please check your DATABASE_URL environment variable.")
        sys.exit(1)
    except asyncpg.CannotConnectNowError:
        print("❌ ERROR: Cannot connect to PostgreSQL server.")
        print("Please ensure PostgreSQL is running and accessible.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)


async def run_migrations():
    """Run Alembic migrations to create schema."""
    print("\nInitializing database schema...")

    try:
        await init_db()
        print("✅ Database schema initialized successfully!")
    except Exception as e:
        print(f"❌ ERROR initializing schema: {e}")
        sys.exit(1)


async def migrate_csv_data():
    """Migrate existing CSV data to PostgreSQL."""
    print("\nMigrating CSV data to PostgreSQL...")

    try:
        storage = HybridStorage()
        counts = await storage.migrate_csv_to_postgres()

        print(f"✅ Migration complete!")
        print(f"   - Risk config: {counts['risk_config']}")
        print(f"   - Strategies: {counts['strategies']}")
        if counts["errors"] > 0:
            print(f"   - Errors: {counts['errors']}")
    except Exception as e:
        print(f"❌ ERROR migrating data: {e}")
        print("You can continue without migration and migrate later.")


async def verify_setup():
    """Verify database setup."""
    print("\nVerifying database setup...")

    try:
        from backend.storage.postgres_storage import PostgresStorage

        storage = PostgresStorage()

        # Try to read risk config
        config = await storage.get_risk_config()
        print(f"✅ Database connection verified!")
        print(f"   - AI Trading Enabled: {config['ai_trading_enabled']}")
        print(f"   - Min Confidence: {config['min_confidence_threshold']}%")

    except Exception as e:
        print(f"❌ ERROR verifying setup: {e}")
        sys.exit(1)


async def main():
    """Main setup function."""
    print("=" * 60)
    print("PostgreSQL Database Setup for AI Trading Platform")
    print("=" * 60)
    print()
    print(f"Database URL: {DATABASE_URL}")
    print()

    # Step 1: Create database
    await create_database_if_not_exists()

    # Step 2: Run migrations
    await run_migrations()

    # Step 3: Ask about CSV migration
    print()
    migrate = input(
        "Do you want to migrate existing CSV data to PostgreSQL? (y/n): "
    ).lower()
    if migrate == "y":
        await migrate_csv_data()
    else:
        print("Skipping CSV migration. You can run this later if needed.")

    # Step 4: Verify setup
    await verify_setup()

    # Cleanup
    await close_db()

    print()
    print("=" * 60)
    print("✅ PostgreSQL setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Set USE_POSTGRES=true in your .env file to enable PostgreSQL")
    print("2. Set DUAL_WRITE=true to write to both CSV and PostgreSQL")
    print("3. Restart your application")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
