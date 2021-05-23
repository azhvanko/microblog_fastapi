from datetime import datetime

from aioredis import Redis
from fastapi import Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database.session import get_db_session, get_redis_session


class HomeService:

    def __init__(
            self,
            db_session: Session = Depends(get_db_session),
            redis_session: Redis = Depends(get_redis_session)
    ):
        self.db_session = db_session
        self.redis_session = redis_session

    async def home(
            self,
            user: schemas.User,
            limit: int = 50,
            expire: int = 900  # 15 min
    ) -> list[schemas.HomeBlogPost]:
        users = (
            self.db_session
                .query(models.Follower.user_id)
                .select_from(models.User)
                .join(
                    models.Follower,
                    models.User.id == models.Follower.follower_id
                )
                .filter(
                    (models.User.id == user.id) &
                    (models.Follower.is_active)
                )
                .subquery()
        )

        last_blog_post_datetime = await self.redis_session.get(
            f'home:{user.id}:last_blog_post_datetime'
        )
        condition = (models.Post.is_published)

        if (
            last_blog_post_datetime is not None and
            isinstance(datetime.fromisoformat(last_blog_post_datetime), datetime)
        ):
            condition = condition & (
                    models.PostRelationship.created_at < last_blog_post_datetime
            )

        all_posts = (
            self.db_session
                .query(
                    models.Post.id.label('post_id'),
                    models.Post.content,
                    func.max(models.PostRelationship.created_at).label('last_created_at')
                )
                .select_from(models.Post)
                .join(
                    models.PostRelationship,
                    models.PostRelationship.post_id == models.Post.id
                )
                .join(
                    users,
                    users.c.user_id == models.PostRelationship.user_id
                )
                .filter(condition)
                .group_by(
                    models.Post.id,
                    models.Post.content
                )
                .subquery()
        )

        posts = (
            self.db_session
                .query(
                    all_posts.c.post_id,
                    all_posts.c.content,
                    all_posts.c.last_created_at.label('created_at'),
                    models.User.id.label('user_id'),
                    models.User.username,
                    models.PostRelationship.is_owner
                )
                .join(
                    models.PostRelationship,
                    models.PostRelationship.post_id == all_posts.c.post_id
                )
                .join(
                    users,
                    users.c.user_id == models.PostRelationship.user_id
                )
                .join(
                    models.User,
                    models.User.id == models.PostRelationship.user_id
                )
                .filter(models.PostRelationship.created_at == all_posts.c.last_created_at)
                .order_by(desc('last_created_at'))
                .limit(limit)
                .all()
        )

        post_ids = []
        repost_ids = []
        result = {}

        if posts:
            await self.redis_session.set(
                f'home:{user.id}:last_blog_post_datetime',
                posts[-1]['created_at'].isoformat(),
                expire=expire
            )

        for post in posts:
            post_ids.append(post['post_id'])
            if not post['is_owner']:
                repost_ids.append(post['post_id'])
            blog_post = schemas.HomeBlogPost(
                post_id=post['post_id'],
                content=post['content'],
                created_at=post['created_at'],
                user=schemas.BlogPostUser(
                    id=post['user_id'],
                    username=post['username']
                )
            )
            result[post['post_id']] = blog_post

        if repost_ids:
            post_authors = (
                self.db_session
                    .query(
                        models.PostRelationship.post_id,
                        models.User.id.label('user_id'),
                        models.User.username
                    )
                    .select_from(models.User)
                    .join(
                        models.PostRelationship,
                        models.PostRelationship.user_id == models.User.id
                    )
                    .filter(
                        (models.PostRelationship.post_id.in_(repost_ids)) &
                        (models.PostRelationship.is_owner)
                    )
                    .all()
            )

            for post_author in post_authors:
                post_id = post_author['post_id']
                result[post_id].author = schemas.BlogPostUser(
                    id=post_author['user_id'],
                    username=post_author['username']
                )

        blog_post_likes = (
            self.db_session
                .query(
                    models.Like.post_id,
                    func.count('*').label('likes_count')
                )
                .filter(
                    (models.Like.post_id.in_(post_ids)) &
                    (models.Like.is_active)
                )
                .group_by(models.Like.post_id)
                .all()
        )

        for blog_post_like in blog_post_likes:
            post_id = blog_post_like['post_id']
            result[post_id].likes_count = blog_post_like['likes_count']

        blog_post_reposts = (
            self.db_session
                .query(
                    models.PostRelationship.post_id,
                    func.count('*').label('reposts_count')
                )
                .filter(
                    (models.PostRelationship.post_id.in_(post_ids)) &
                    (~models.PostRelationship.is_owner)
                )
                .group_by(models.PostRelationship.post_id)
                .all()
        )

        for blog_post_repost in blog_post_reposts:
            post_id = blog_post_repost['post_id']
            result[post_id].reposts_count = blog_post_repost['reposts_count']

        return list(result.values())
