"""
Database Connection Manager
"""
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from loguru import logger

from core.config import config
from .base import Base


class DatabaseManager:
    """Database connection manager"""
    
    _instance = None
    _engine: AsyncEngine = None
    _session_factory: async_sessionmaker = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self, database_url: str = None):
        """Initialize database connection"""
        url = database_url or config.DATABASE_URL
        
        # Add timeout for SQLite to avoid "database is locked" errors
        connect_args = {}
        if "sqlite" in url:
            connect_args = {"timeout": 30}
        
        self._engine = create_async_engine(
            url,
            echo=config.DEBUG,
            future=True,
            connect_args=connect_args
        )
        
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        logger.info(f"Database initialized: {url}")
    
    async def create_tables(self):
        """Create all tables"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)"""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection closed")


# Global instance
db_manager = DatabaseManager()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async with db_manager.session() as session:
        yield session


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session"""
    async with db_manager.session() as session:
        yield session
