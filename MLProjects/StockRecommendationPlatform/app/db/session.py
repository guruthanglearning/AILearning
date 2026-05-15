from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    global _engine, _session_factory
    _engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("DB engine not initialised; call init_engine() at startup")
    async with _session_factory() as session:
        yield session


def get_engine():
    return _engine
