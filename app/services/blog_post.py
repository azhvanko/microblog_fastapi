from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from .. import models, schemas
from ..core import settings
from ..database.session import get_db_session


class BlogPostService:

    @classmethod
    def _create_exception(
            cls,
            detail: str,
            status_code: int = HTTP_422_UNPROCESSABLE_ENTITY
    ) -> Exception:
        return HTTPException(
            status_code=status_code,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'}
        )

    def __init__(self, db_session: Session = Depends(get_db_session)):
        self.db_session = db_session

    def _is_existing_blog_post(self, post_id: int) -> bool:
        blog_post = (
            self.db_session
                .query(func.count('*'))
                .select_from(models.Post)
                .filter(models.Post.id == post_id)
                .scalar()
        )

        return bool(blog_post)

    def _is_blog_post_author(self, user_id: int, post_id: int) -> bool:
        post_relationship = (
            self.db_session
                .query(func.count('*'))
                .select_from(models.PostRelationship)
                .filter(
                    (models.PostRelationship.post_id == post_id) &
                    (models.PostRelationship.user_id == user_id) &
                    (models.PostRelationship.is_owner)
                )
                .scalar()
        )

        return bool(post_relationship)

    def _get_blog_post(self, post_id: int) -> Optional[models.Post]:
        blog_post = (
            self.db_session
                .query(models.Post)
                .filter(models.Post.id == post_id)
                .first()
        )

        return blog_post

    def _get_blog_post_relationship(
            self,
            user_id: int,
            post_id: int
    ) -> Optional[models.PostRelationship]:
        post_relationship = (
            self.db_session
                .query(models.PostRelationship)
                .filter(
                    (models.PostRelationship.user_id == user_id) &
                    (models.PostRelationship.post_id == post_id)
                )
                .first()
        )

        return post_relationship

    async def create_blog_post(
            self,
            user: schemas.User,
            user_data: schemas.BlogPostCreate
    ) -> schemas.BlogPost:
        blog_post = models.Post(content=user_data.content)
        self.db_session.add(blog_post)
        self.db_session.commit()

        blog_post_relationship = models.PostRelationship(
            user_id=user.id,
            post_id=blog_post.id,
            created_at=blog_post.created_at
        )

        self.db_session.add(blog_post_relationship)
        self.db_session.commit()

        return schemas.BlogPost.from_orm(blog_post)

    async def update_blog_post(
            self,
            user: schemas.User,
            user_data: schemas.BlogPostUpdate,
            post_id: int
    ) -> schemas.BlogPost:
        if not self._is_blog_post_author(user.id, post_id):
            exception = self._create_exception('invalid post relationship')
            raise exception from None

        blog_post = self._get_blog_post(post_id)

        if blog_post.content == user_data.content:
            return schemas.BlogPost.from_orm(blog_post)

        updated_at = datetime.utcnow()
        creation_timedelta = (updated_at - blog_post.created_at).total_seconds()

        if creation_timedelta > settings.BLOG_POST_EDITED_TIME_LIMIT:
            exception = self._create_exception('blog post cannot be updated')
            raise exception from None

        blog_post.content = user_data.content
        blog_post.updated_at = updated_at

        self.db_session.commit()

        return schemas.BlogPost.from_orm(blog_post)

    async def archive_blog_post(
            self,
            user: schemas.User,
            post_id: int
    ) -> None:
        if not self._is_blog_post_author(user.id, post_id):
            exception = self._create_exception('invalid post relationship')
            raise exception from None

        blog_post = self._get_blog_post(post_id)

        if blog_post.is_published:
            blog_post.is_published = False
            blog_post.updated_at = datetime.utcnow()

            self.db_session.commit()

    async def delete_blog_post(
            self,
            user: schemas.User,
            post_id: int
    ) -> None:
        if not self._is_blog_post_author(user.id, post_id):
            exception = self._create_exception('invalid post relationship')
            raise exception from None

        blog_post = self._get_blog_post(post_id)

        self.db_session.delete(blog_post)
        self.db_session.commit()

    async def add_blog_post_like(
            self,
            user: schemas.User,
            username: str,
            post_id: int
    ) -> None:
        post_relationship = (
            self.db_session
                .query(func.count('*'))
                .select_from(models.PostRelationship)
                .join(
                    models.User,
                    models.User.id == models.PostRelationship.user_id
                )
                .join(
                    models.Post,
                    models.Post.id == models.PostRelationship.post_id
                )
                .filter(
                    (models.PostRelationship.post_id == post_id) &
                    (models.User.username == username) &
                    (models.PostRelationship.is_owner) &
                    (models.Post.is_published)
                )
                .scalar()
        )

        if not post_relationship:
            exception = self._create_exception('invalid post relationship')
            raise exception from None

        blog_post_like = (
            self.db_session
                .query(models.Like)
                .filter(
                    (models.Like.post_id == post_id) &
                    (models.Like.user_id == user.id)
                )
                .first()
        )

        if blog_post_like:
            if blog_post_like.is_active:
                return
            else:
                blog_post_like.is_active = True
                blog_post_like.created_at = datetime.utcnow()
        else:
            new_blog_post_like = models.Like(
                user_id=user.id,
                post_id=post_id
            )
            self.db_session.add(new_blog_post_like)

        self.db_session.commit()

    async def remove_blog_post_like(
            self,
            user: schemas.User,
            post_id: int
    ) -> None:
        blog_post_like = (
            self.db_session
                .query(models.Like)
                .join(
                    models.Post,
                    models.Post.id == models.Like.post_id
                )
                .filter(
                    (models.Like.post_id == post_id) &
                    (models.Like.user_id == user.id) &
                    (models.Post.is_published)
                )
                .first()
        )

        if not blog_post_like:
            exception = self._create_exception(
                'the blog post hasn\'t already liked'
            )
            raise exception from None

        if blog_post_like.is_active:
            blog_post_like.is_active = False
            blog_post_like.created_at = datetime.utcnow()

            self.db_session.commit()

    async def create_blog_post_repost(
            self,
            user: schemas.User,
            post_id: int
    ) -> None:
        if not self._is_existing_blog_post(post_id):
            exception = self._create_exception('invalid blog post id')
            raise exception from None

        post_relationship = self._get_blog_post_relationship(user.id, post_id)

        if post_relationship:
            return

        blog_post_relationship = models.PostRelationship(
            user_id=user.id,
            post_id=post_id,
            is_owner=False
        )

        self.db_session.add(blog_post_relationship)
        self.db_session.commit()

    async def delete_blog_post_repost(
            self,
            user: schemas.User,
            post_id: int
    ) -> None:
        if not self._is_existing_blog_post(post_id):
            exception = self._create_exception('invalid blog post id')
            raise exception from None

        post_relationship = self._get_blog_post_relationship(user.id, post_id)

        if not post_relationship:
            exception = self._create_exception('invalid post relationship')
            raise exception from None

        if post_relationship.is_owner:
            exception = self._create_exception('cannot delete this repost')
            raise exception from None

        self.db_session.delete(post_relationship)
        self.db_session.commit()
