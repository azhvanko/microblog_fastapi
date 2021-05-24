from sqlalchemy import create_engine

from .base_class import Base
from ..core import settings


def create_db_schema() -> None:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
