from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String
)

from ..database.base_class import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    date_joined = Column(DateTime, default=datetime.utcnow())
    is_active = Column(Boolean(), default=True)
    is_staff = Column(Boolean(), default=False)
    is_superuser = Column(Boolean(), default=False)
