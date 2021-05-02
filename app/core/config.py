from pydantic import BaseSettings


class Settings(BaseSettings):
    PYTHONPATH: str
    SQLALCHEMY_DATABASE_URL: str


settings = Settings()
