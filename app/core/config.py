from pydantic import BaseSettings


class Settings(BaseSettings):
    PYTHONPATH: str

    SQLALCHEMY_DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES: int = 60 * 60  # 1 h.
    JWT_REFRESH_TOKEN_EXPIRES: int = 60 * 60 * 24  # 24 h.


settings = Settings()
