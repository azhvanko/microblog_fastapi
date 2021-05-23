import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app import schemas
from app.models import Follower, Post, PostRelationship, User
from tests.utils import BaseTestCase


class TestFollowerService(BaseTestCase):
    posts_count = 10
    user = {
        'username': f'test_user_3',
        'email': f'test_user_3@example.com',
        'password': '1Password'
    }

    @staticmethod
    def get_user(db_session: Session, username: str) -> User:
        user = (
            db_session
            .query(User)
            .filter(User.username == username)
            .first()
        )
        return user

    def add_users(self, db_session: Session) -> None:
        for i in range(1, 4):
            user = {
                'username': f'test_user_{i}',
                'email': f'test_user_{i}@example.com',
                'password': '1Password'
            }
            self.add_user(db_session, user)

    def add_users_posts(self, db_session: Session) -> None:

        for i in range(1, self.posts_count + 1):
            blog_post = Post(content=f'blog_post_{i}')
            db_session.add(blog_post)
        db_session.commit()

        user1 = self.get_user(db_session, 'test_user_1')
        user2 = self.get_user(db_session, 'test_user_2')

        blog_posts = db_session.query(Post).all()

        for index, blog_post in enumerate(blog_posts, start=1):
            blog_post_relationship = PostRelationship(
                user_id=user1.id if index <= self.posts_count // 2 else user2.id,
                post_id=blog_post.id
            )
            db_session.add(blog_post_relationship)
        db_session.commit()

    def add_follower(
            self,
            db_session: Session,
            username: str,
            followername: str
    ) -> None:
        user_id = self.get_user_id(db_session, username)
        follower_id = self.get_user_id(db_session, followername)

        follower = Follower(user_id=user_id, follower_id=follower_id)

        db_session.add(follower)
        db_session.commit()

    def add_followers(self, db_session: Session) -> None:
        self.add_follower(db_session, 'test_user_1', 'test_user_3')
        self.add_follower(db_session, 'test_user_2', 'test_user_3')

    @pytest.mark.asyncio
    async def test_home_endpoint(self, test_app: AsyncClient, db_session: Session):
        self.add_users(db_session)
        self.add_users_posts(db_session)
        self.add_followers(db_session)

        refresh_token = await self.authorize_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        response = await test_app.get('/api/v1/home', headers=headers)

        assert response.status_code == 200
        assert response.json()[0].keys() == schemas.HomeBlogPost.__fields__.keys()
        assert len(response.json()) == self.posts_count
