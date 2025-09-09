"""
Database configuration for OLIS Legislature Tracker
Handles async SQLAlchemy setup with PostgreSQL
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://olis_user:olis_password@localhost:5432/olis_tracker")

# Create async engine
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ENABLE_DEBUG", "false").lower() == "true",  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide database session for FastAPI endpoints
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def test_database_connection() -> bool:
    """
    Test database connection and return success status
    """
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

async def close_database_connections():
    """
    Close all database connections (for app shutdown)
    """
    await engine.dispose()