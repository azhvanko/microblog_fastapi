import json
import pytest
from aioredis import Redis
from httpx import AsyncClient
from passlib.hash import bcrypt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from app.database import session
from app.database.base_class import Base
from app.models import User


class BaseTestCase:
    user = {
        'username': 'test_user',
        'email': 'test_user@example.com',
        'password': '1Password'
    }

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: Session, redis_session: Redis):
        # delete all keys in the current database.
        await redis_session.flushdb()
        # clear all db tables
        engine = create_engine(session.DATABASE, pool_pre_ping=True)
        for t in reversed(Base.metadata.sorted_tables):
            engine.execute(t.delete())

    @staticmethod
    def add_user(db_session: Session, user: dict[str, str]) -> None:
        new_user = User(
            username=user['username'],
            email=user['email'],
            password_hash=bcrypt.hash(user['password'])
        )

        db_session.add(new_user)
        db_session.commit()

    @staticmethod
    async def register_user(
            test_app: AsyncClient,
            user: dict[str, str]
    ) -> str:
        response = await test_app.post(
            '/api/v1/auth/sign-up',
            content=json.dumps(user)
        )

        return response.cookies.get('refresh_token')

    @staticmethod
    async def authorize_user(
            test_app: AsyncClient,
            user: dict[str, str]
    ) -> str:
        headers = {'content-type': 'application/x-www-form-urlencoded', }
        data = {
            'username': user['username'],
            'password': user['password']
        }

        response = await test_app.post(
            '/api/v1/auth/sign-in',
            headers=headers,
            data=data
        )

        return response.cookies.get('refresh_token')

    @staticmethod
    def check_is_db_user(db_session: Session, username: str) -> bool:
        is_db_user = (
            db_session
                .query(func.count('*'))
                .select_from(User)
                .filter(User.username == username)
                .scalar()
        )

        return bool(is_db_user)

    @staticmethod
    def get_user_id(db_session: Session, username: str) -> int:
        user = (
            db_session
                .query(User)
                .with_entities(User.id)
                .filter(User.username == username)
                .first()
        )

        return user.id
