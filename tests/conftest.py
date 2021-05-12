import pytest
from aioredis import create_redis
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import settings
from app.database import session
from app.database.base_class import Base
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def init_db():
    session.DATABASE = settings.SQLALCHEMY_TEST_DATABASE_URL
    engine = create_engine(session.DATABASE, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    session.DATABASE = settings.SQLALCHEMY_DATABASE_URL


@pytest.fixture(scope="session", autouse=True)
def init_redis():
    session.REDIS = settings.REDIS_TEST_DATABASE_URL
    yield
    session.REDIS = settings.REDIS_DATABASE_URL


@pytest.fixture
async def test_app():
    async with AsyncClient(app=app, base_url='http://test') as async_client:
        yield async_client


@pytest.fixture
def db_session():
    engine = create_engine(
        settings.SQLALCHEMY_TEST_DATABASE_URL,
        pool_pre_ping=True
    )
    _session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()

    try:
        yield _session
    finally:
        _session.close()


@pytest.fixture
async def redis_session():
    redis = await create_redis(settings.REDIS_TEST_DATABASE_URL, encoding='utf-8')
    try:
        yield redis
    finally:
        redis.close()
        await redis.wait_closed()
