from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer
)
from sqlalchemy.orm import relationship

from ..database.base_class import Base


class Follower(Base):
    __tablename__ = 'follower'

    follower_id = Column(
        Integer,
        ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True
    )
    user_id = Column(
        Integer,
        ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
        nullable=False
    )
    is_active = Column(Boolean(), default=True)

    user = relationship('User', foreign_keys=[user_id, ])
    follower = relationship('User', foreign_keys=[follower_id, ])
