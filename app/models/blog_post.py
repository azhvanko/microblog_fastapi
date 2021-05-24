from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text
)
from sqlalchemy.orm import relationship

from ..database.base_class import Base


class Post(Base):
    __tablename__ = 'blog_post'

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    is_published = Column(Boolean(), default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow()
    )

    users = relationship(
        'PostRelationship',
        back_populates='post',
        cascade='all, delete, delete-orphan'
    )
    likes = relationship(
        'Like',
        back_populates='post',
        cascade='all, delete, delete-orphan'
    )


class PostRelationship(Base):
    __tablename__ = 'blog_post_relationship'

    user_id = Column(
        Integer,
        ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True
    )
    post_id = Column(
        Integer,
        ForeignKey('blog_post.id', ondelete='CASCADE'),
        primary_key=True
    )
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    is_owner = Column(Boolean(), default=True, nullable=False)

    __table_args__ = (
        Index(
            'only_one_blog_post_owner',
            post_id,
            is_owner,
            unique=True,
            postgresql_where=(is_owner)
        ),
    )

    user = relationship('User', back_populates='posts')
    post = relationship('Post', back_populates='users')


class Like(Base):
    __tablename__ = 'blog_post_like'

    user_id = Column(
        Integer,
        ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True
    )
    post_id = Column(
        Integer,
        ForeignKey('blog_post.id', ondelete='CASCADE'),
        primary_key=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
        nullable=False
    )
    is_active = Column(Boolean(), default=True, nullable=False)

    user = relationship('User', back_populates='likes')
    post = relationship('Post', back_populates='likes')
