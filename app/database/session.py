from typing import AsyncIterator, Iterator

from aioredis import create_redis, Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core import settings


DATABASE = settings.SQLALCHEMY_DATABASE_URL
REDIS = settings.REDIS_DATABASE_URL


def _create_session() -> Session:
    echo = settings.DEBUG
    engine = create_engine(DATABASE, pool_pre_ping=True, echo=echo)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return session()


def get_db_session() -> Iterator[Session]:
    session = _create_session()
    try:
        yield session
    finally:
        session.close()


async def get_redis_session() -> AsyncIterator[Redis]:
    redis = await create_redis(REDIS, encoding='utf-8')
    try:
        yield redis
    finally:
        redis.close()
        await redis.wait_closed()
