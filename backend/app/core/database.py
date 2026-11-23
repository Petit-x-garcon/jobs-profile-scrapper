from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all models."""


engine = create_async_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session."""
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def task_session() -> AsyncIterator[AsyncSession]:
    """Session for Celery tasks: a throwaway NullPool engine bound to the current loop."""
    task_engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with async_sessionmaker(task_engine, expire_on_commit=False)() as session:
            yield session
    finally:
        await task_engine.dispose()
