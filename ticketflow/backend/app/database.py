import asyncio
from typing import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from .config import settings

logger = logging.getLogger(__name__)

# Create Base for all models
Base = declarative_base()

DATABASE_URL = settings.DATABASE_URL

# Create async engine with connection pooling
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=10,        # Number of connections to maintain
    max_overflow=20,     # Maximum overflow connections
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def test_connection() -> bool:
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def remove_role_constraints() -> None:
    """Remove CHECK constraints on role and department columns to allow custom values"""
    try:
        async with engine.begin() as conn:
            # Remove role constraint
            try:
                await conn.execute(text("ALTER TABLE user_profile DROP CONSTRAINT IF EXISTS user_profile_role_check"))
                logger.info("✅ Removed user_profile_role_check constraint")
            except Exception as e:
                logger.warning(f"Could not remove role constraint (may not exist): {e}")
            
            # Remove department constraint
            try:
                await conn.execute(text("ALTER TABLE user_profile DROP CONSTRAINT IF EXISTS user_profile_department_check"))
                logger.info("✅ Removed user_profile_department_check constraint")
            except Exception as e:
                logger.warning(f"Could not remove department constraint (may not exist): {e}")
    except Exception as e:
        logger.warning(f"⚠️  Could not remove constraints: {e}. This is non-critical.")

# helper to create tables (call during dev or startup)
async def init_db() -> None:
    """Initialize database - create all tables"""
    try:
        # Test connection first
        if not await test_connection():
            raise Exception("Database connection test failed")
        
        # Import models here to avoid circular import
        from . import models
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        
        # Remove CHECK constraints to allow custom roles/departments
        await remove_role_constraints()
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
