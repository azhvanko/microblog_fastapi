import json

import pytest
from httpx import AsyncClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import schemas
from app.models import Like, Post, PostRelationship, User
from tests.utils import BaseTestCase


class TestBlogPostService(BaseTestCase):
    new_user = {
        'username': 'new_test_user',
        'email': 'new_test_user@example.com',
        'password': '1Password'
    }

    @staticmethod
    def create_blog_post(
            db_session: Session,
            user_id: int,
            content: str
    ) -> schemas.BlogPost:
        blog_post = Post(content=content)
        db_session.add(blog_post)
        db_session.commit()

        blog_post_relationship = PostRelationship(
            user_id=user_id,
            post_id=blog_post.id,
            created_at=blog_post.created_at
        )

        db_session.add(blog_post_relationship)
        db_session.commit()

        return schemas.BlogPost.from_orm(blog_post)

    @pytest.mark.asyncio
    async def test_blog_post_create_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        data = {'content': 'test message', }

        response = await test_app.post(
            '/api/v1/posts/create',
            headers=headers,
            content=json.dumps(data)
        )

        post_relationship = (
            db_session
                .query(func.count('*'))
                .select_from(PostRelationship)
                .join(
                    User,
                    User.id == PostRelationship.user_id
                )
                .join(
                    Post,
                    Post.id == PostRelationship.post_id
                )
                .filter(
                    (User.username == self.user['username']) &
                    (PostRelationship.is_owner) &
                    (Post.content == data['content']) &
                    (Post.is_published)
                )
                .scalar()
        )

        assert response.status_code == 201
        assert post_relationship
        assert response.json().keys() == schemas.BlogPost.__fields__.keys()

    @pytest.mark.asyncio
    async def test_blog_post_update_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user_id = self.get_user_id(db_session, self.user['username'])
        blog_post = self.create_blog_post(db_session, user_id, 'qwerty')

        data = {'content': 'test message', }
        username = self.user['username']
        response = await test_app.put(
            f'/api/v1/users/{username}/{blog_post.id}',
            headers=headers,
            content=json.dumps(data)
        )

        updated_blog_post = (
            db_session
                .query(Post)
                .filter(Post.id == blog_post.id)
                .first()
        )

        assert response.status_code == 200
        assert response.json()['content'] == data['content']
        assert updated_blog_post.content == data['content']
        assert response.json().keys() == schemas.BlogPost.__fields__.keys()

    @pytest.mark.asyncio
    async def test_blog_post_delete_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user_id = self.get_user_id(db_session, self.user['username'])
        blog_post = self.create_blog_post(db_session, user_id, 'qwerty')

        username = self.user['username']
        response = await test_app.delete(
            f'/api/v1/users/{username}/{blog_post.id}',
            headers=headers
        )

        is_deleted_blog_post = (
            db_session
                .query(func.count('*'))
                .select_from(Post)
                .filter(Post.id == blog_post.id)
                .scalar()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert not is_deleted_blog_post

    @pytest.mark.asyncio
    async def test_blog_post_archive_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user_id = self.get_user_id(db_session, self.user['username'])
        blog_post = self.create_blog_post(db_session, user_id, 'qwerty')

        username = self.user['username']
        response = await test_app.put(
            f'/api/v1/users/{username}/{blog_post.id}/archive',
            headers=headers
        )

        is_archived_blog_post = (
            db_session
                .query(func.count('*'))
                .select_from(Post)
                .filter(
                    (Post.id == blog_post.id) &
                    (~Post.is_published)
                )
                .scalar()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert is_archived_blog_post

    @pytest.mark.asyncio
    async def test_blog_post_repost_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        # register first user
        _ = await self.register_user(test_app, self.new_user)
        first_user_id = self.get_user_id(db_session, self.new_user['username'])
        blog_post = self.create_blog_post(db_session, first_user_id, 'qwerty')

        # register second user
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        username = self.user['username']
        response = await test_app.post(
            f'/api/v1/users/{username}/{blog_post.id}/repost',
            headers=headers
        )

        second_user_id = self.get_user_id(db_session, self.user['username'])
        is_blog_post_repost = (
            db_session
                .query(func.count('*'))
                .select_from(PostRelationship)
                .filter(
                    (PostRelationship.post_id == blog_post.id) &
                    (PostRelationship.user_id == second_user_id) &
                    (~PostRelationship.is_owner)
                )
                .scalar()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert is_blog_post_repost

    @pytest.mark.asyncio
    async def test_blog_post_repost_endpoint_with_post_owner(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user_id = self.get_user_id(db_session, self.user['username'])
        blog_post = self.create_blog_post(db_session, user_id, 'qwerty')

        username = self.user['username']
        response = await test_app.post(
            f'/api/v1/users/{username}/{blog_post.id}/repost',
            headers=headers
        )

        user_blog_reposts = (
            db_session
                .query(PostRelationship)
                .filter(PostRelationship.user_id == user_id)
                .all()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert len(user_blog_reposts) == 1

    @pytest.mark.asyncio
    async def test_blog_post_repost_delete_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        # register first user
        _ = await self.register_user(test_app, self.new_user)
        first_user_id = self.get_user_id(db_session, self.new_user['username'])
        blog_post = self.create_blog_post(db_session, first_user_id, 'qwerty')

        # register second user
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        # create repost
        username = self.user['username']
        _ = await test_app.post(
            f'/api/v1/users/{username}/{blog_post.id}/repost',
            headers=headers
        )

        response = await test_app.delete(
            f'/api/v1/users/{username}/{blog_post.id}/repost/delete',
            headers=headers
        )

        second_user_id = self.get_user_id(db_session, self.user['username'])
        user_blog_reposts = (
            db_session
                .query(PostRelationship)
                .filter(PostRelationship.user_id == second_user_id)
                .all()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert len(user_blog_reposts) == 0

    @pytest.mark.asyncio
    async def test_blog_post_like_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user_id = self.get_user_id(db_session, self.user['username'])
        blog_post = self.create_blog_post(db_session, user_id, 'qwerty')

        username = self.user['username']
        response = await test_app.post(
            f'/api/v1/users/{username}/{blog_post.id}/like',
            headers=headers
        )

        user_blog_post_like = (
            db_session
                .query(func.count('*'))
                .select_from(Like)
                .filter(
                    (Like.user_id == user_id) &
                    (Like.post_id == blog_post.id) &
                    (Like.is_active)
                )
                .scalar()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert user_blog_post_like

    @pytest.mark.asyncio
    async def test_blog_post_dislike_endpoint(
            self,
            test_app: AsyncClient,
            db_session: Session
    ):
        refresh_token = await self.register_user(test_app, self.user)
        headers = {'Authorization': f'Bearer {refresh_token}', }

        user_id = self.get_user_id(db_session, self.user['username'])
        blog_post = self.create_blog_post(db_session, user_id, 'qwerty')

        # create blog post like
        username = self.user['username']
        _ = await test_app.post(
            f'/api/v1/users/{username}/{blog_post.id}/like',
            headers=headers
        )

        response = await test_app.put(
            f'/api/v1/users/{username}/{blog_post.id}/dislike',
            headers=headers
        )

        user_blog_post_like = (
            db_session
                .query(func.count('*'))
                .select_from(Like)
                .filter(
                    (Like.user_id == user_id) &
                    (Like.post_id == blog_post.id) &
                    (~Like.is_active)
                )
                .scalar()
        )

        assert response.status_code == 200
        assert response.json()['status'] == 'ok'
        assert user_blog_post_like
