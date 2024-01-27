from contextvars import ContextVar, Token
from sqlalchemy import create_engine
from typing import Union

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_scoped_session,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.expression import Update, Delete, Insert

from app.core.config import config

session_context: ContextVar[str] = ContextVar("session_context")


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)


engines = {
    "writer": create_async_engine(config.WRITER_DB_URL, pool_recycle=3600),
    "reader": create_async_engine(config.READER_DB_URL, pool_recycle=3600),
}


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kw):
        if self._flushing or isinstance(clause, (Update, Delete, Insert)):
            return engines["writer"].sync_engine
        else:
            return engines["reader"].sync_engine


async_session_factory = sessionmaker(
    class_=AsyncSession,
    sync_session_class=RoutingSession,
)

session: Union[AsyncSession, async_scoped_session] = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=get_session_context,
)

def get_async_session() -> Session:
    return async_session_factory()

Base = declarative_base()

# Synchronous engine and session
sync_engines = {
    "writer": create_engine(config.WRITER_DB_URL),
    "reader": create_engine(config.READER_DB_URL),
}

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engines['writer']
)


# Sync session getter
def get_sync_session():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# from sqlalchemy import create_engine
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, declarative_base

# from app.core.config import config

# # Asynchronous engine and session
# async_engines = {
#     "writer": create_async_engine(config.WRITER_DB_URL),
#     "reader": create_async_engine(config.READER_DB_URL),
# }

# AsyncSessionLocal = sessionmaker(
#     class_=AsyncSession,
#     bind=async_engines['writer'],
#     expire_on_commit=False
# )

# # Synchronous engine and session
# sync_engines = {
#     "writer": create_engine(config.WRITER_DB_URL),
#     "reader": create_engine(config.READER_DB_URL),
# }

# SyncSessionLocal = sessionmaker(
#     autocommit=False,
#     autoflush=False,
#     bind=sync_engines['writer']
# )

# Base = declarative_base()

# # Async session getter
# async def get_async_session():
#     async with AsyncSessionLocal() as session:
#         yield session

# # Sync session getter
# def get_sync_session():
#     db = SyncSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
