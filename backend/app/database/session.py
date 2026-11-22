from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from collections.abc import AsyncIterator


def create_database_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(
        database_url, pool_pre_ping=True, pool_size=10, max_overflow=20,
        hide_parameters=True,
    )


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide an independent database session for the HTTP request."""
    async with request.app.state.database_sessions() as session:
        yield session
