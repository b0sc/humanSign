"""Database connection and pool management."""

import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.config import get_settings

settings = get_settings()

# Global connection pool
_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    """Initialize database connection pool."""
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=settings.database_pool_size,
        )
        print("✓ Database connection pool initialized")
    except Exception as e:
        print(f"⚠ Database connection failed: {e}")
        print("  Server running in degraded mode (no database)")
        _pool = None


async def close_db() -> None:
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Get the database connection pool."""
    if _pool is None:
        raise RuntimeError("Database not available. Start PostgreSQL: docker-compose up -d postgres")
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn
