from typing import AsyncIterator, Iterator

from aioredis import create_redis, Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..core import settings


_engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_engine
)


def get_db_session() -> Iterator[SessionLocal]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_redis_session() -> AsyncIterator[Redis]:
    redis = await create_redis(settings.REDIS_URL, encoding='utf-8')
    try:
        yield redis
    finally:
        redis.close()
        await redis.wait_closed()
