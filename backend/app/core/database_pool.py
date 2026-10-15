import os
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class DatabasePool:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        if self.session_factory is not None:
            return

        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")

        database_url = database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

        self.engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database connection pool initialized")

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    def get_session(self) -> AsyncSession:
        if not self.session_factory:
            raise RuntimeError("Database pool not initialized")

        return self.session_factory()


db_pool = DatabasePool()


async def get_db_session():
    await db_pool.initialize()

    async with db_pool.get_session() as session:
        yield session