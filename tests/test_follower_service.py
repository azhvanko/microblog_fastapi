import pytest
from httpx import AsyncClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Follower
from tests.utils import BaseTestCase


class TestFollowerService(BaseTestCase):
    new_user = {
        'username': 'new_test_user',
        'email': 'new_test_user@example.com',
        'password': '1Password'
    }

    @pytest.mark.asyncio
    async def test_follow_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        self.add_user(db_session, self.user)
        refresh_token = await self.register_user(test_app, self.new_user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user = self.user['username']
        response = await test_app.post(
            f'/api/v1/users/{user}/follow',
            headers=headers
        )

        user_id = self.get_user_id(db_session, user)
        follower_id = self.get_user_id(db_session, self.new_user['username'])

        is_active_follower = (
            db_session
                .query(func.count('*'))
                .select_from(Follower)
                .filter(
                    (Follower.user_id == user_id) &
                    (Follower.follower_id == follower_id) &
                    (Follower.is_active)
                )
                .scalar()
        )

        assert response.status_code == 201
        assert is_active_follower

    @pytest.mark.asyncio
    async def test_unfollow_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        self.add_user(db_session, self.user)
        refresh_token = await self.register_user(test_app, self.new_user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user = self.user['username']
        _ = await test_app.post(
            f'/api/v1/users/{user}/follow',
            headers=headers
        )

        response = await test_app.put(
            f'/api/v1/users/{user}/unfollow',
            headers=headers
        )

        user_id = self.get_user_id(db_session, user)
        follower_id = self.get_user_id(db_session, self.new_user['username'])

        is_inactive_follower = (
            db_session
                .query(func.count('*'))
                .select_from(Follower)
                .filter(
                    (Follower.user_id == user_id) &
                    (Follower.follower_id == follower_id) &
                    (~Follower.is_active)
                )
                .scalar()
        )

        assert response.status_code == 200
        assert is_inactive_follower
