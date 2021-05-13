import json

import pytest
from aioredis import Redis
from httpx import AsyncClient
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app import schemas
from app.models import User
from tests.utils import BaseTestCase


class TestAuthService(BaseTestCase):

    @staticmethod
    def add_user(db_session: Session, user: dict[str, str]) -> None:
        new_user = User(
            username=user['username'],
            email=user['email'],
            password_hash=bcrypt.hash(user['password'])
        )

        db_session.add(new_user)
        db_session.commit()

    @pytest.mark.asyncio
    async def test_sign_up_endpoint_with_new_user(
            self,
            test_app: AsyncClient,
            db_session: Session,
            redis_session: Redis
    ):
        response = await test_app.post(
            '/api/v1/auth/sign-up',
            content=json.dumps(self.user)
        )

        is_db_user = self.check_is_db_user(db_session, self.user['username'])

        refresh_token = response.cookies.get('refresh_token', None)
        refresh_tokens = await redis_session.smembers(self.user['username'])

        assert response.status_code == 201
        assert refresh_token in refresh_tokens
        assert is_db_user

    @pytest.mark.asyncio
    async def test_sign_up_endpoint_with_duplicate_user(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        self.add_user(db_session, self.user)

        response = await test_app.post(
            '/api/v1/auth/sign-up',
            content=json.dumps(self.user)
        )

        is_db_user = self.check_is_db_user(db_session, self.user['username'])

        assert response.status_code == 401
        assert is_db_user

    @pytest.mark.asyncio
    async def test_sign_in_endpoint_with_registered_user(
            self,
            test_app: AsyncClient,
            db_session: Session,
            redis_session: Redis
    ):
        self.add_user(db_session, self.user)
        headers = {'content-type': 'application/x-www-form-urlencoded', }
        data = {
            'username': self.user['username'],
            'password': self.user['password']
        }

        response = await test_app.post(
            '/api/v1/auth/sign-in',
            headers=headers,
            data=data
        )

        refresh_token = response.cookies.get('refresh_token', None)
        refresh_tokens = await redis_session.smembers(self.user['username'])

        assert response.status_code == 200
        assert all(i in response.json() for i in ('token_type', 'access_token', ))
        assert refresh_token in refresh_tokens

    @pytest.mark.asyncio
    async def test_sign_in_endpoint_with_unregistered_user(
            self,
            test_app: AsyncClient
    ):
        headers = {'content-type': 'application/x-www-form-urlencoded', }
        data = {
            'username': self.user['username'],
            'password': self.user['password']
        }

        response = await test_app.post(
            '/api/v1/auth/sign-in',
            headers=headers,
            data=data
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_endpoint_with_registered_user(
            self,
            test_app: AsyncClient,
            redis_session: Redis
    ):
        refresh_token = await self.register_user(test_app, self.user)

        headers = {'Authorization': f'Bearer {refresh_token}', }
        response = await test_app.put('/api/v1/auth/refresh', headers=headers)

        new_refresh_token = response.cookies.get('refresh_token', None)
        new_refresh_tokens = await redis_session.smembers(self.user['username'])

        assert response.status_code == 201
        assert all(i in response.json() for i in ('token_type', 'access_token', ))
        assert new_refresh_token in new_refresh_tokens

    @pytest.mark.asyncio
    async def test_get_user_endpoint_with_registered_user(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)

        headers = {'Authorization': f'Bearer {refresh_token}', }
        response = await test_app.get('/api/v1/auth/user', headers=headers)

        is_db_user = self.check_is_db_user(db_session, self.user['username'])

        assert response.status_code == 200
        assert response.json().keys() == schemas.User.__fields__.keys()
        assert is_db_user
