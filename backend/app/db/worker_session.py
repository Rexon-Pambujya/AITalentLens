"""
A SEPARATE engine/session factory from app.db.session, used only by Celery
tasks.

Why this exists: FastAPI runs one persistent event loop for the life of
the process, so a pooled asyncpg engine (app.db.session.engine) is safe -
every connection in the pool was created on, and is reused on, that same
loop.

Celery tasks are different: each task body runs inside its own
`asyncio.run(...)` call (see workers/resume_tasks.py), which creates and
tears down a NEW event loop every time. If a pooled connection created
under loop #1 is checked out again under loop #2, asyncpg raises
`RuntimeError: Future attached to a different loop`. Using NullPool here
means every task opens a fresh connection and closes it when done -
slightly more connection overhead per task, but correct.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()


def _build_worker_session_factory():
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool, echo=False)
    return engine, async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def worker_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Creates a brand-new engine + connection for the current event loop,
    yields a session, and fully disposes the engine afterward. Call this
    once per Celery task invocation - never share the result across tasks."""
    engine, session_factory = _build_worker_session_factory()
    try:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()
