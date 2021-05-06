from datetime import datetime, timedelta
from typing import Any, Union

from aioredis import Redis
from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.hash import bcrypt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from .. import models, schemas
from ..core import settings
from ..database.session import get_db_session, get_redis_session


oauth2_scheme: OAuth2 = OAuth2PasswordBearer(tokenUrl='api/v1/auth/sign-in')


async def get_user(token: str = Depends(oauth2_scheme)) -> schemas.User:
    return AuthService.get_user(token)


class AuthService:

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        return bcrypt.hash(plain_password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.verify(plain_password, hashed_password)

    @classmethod
    def verify_token(cls, token: str) -> dict[str, Any]:
        exception = cls._create_exception('Could not validate credentials')

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM, ],
            )
        except JWTError:
            raise exception from None

        return payload

    @classmethod
    def create_token(cls, user: schemas.User, token_expires: int) -> str:
        now = datetime.utcnow()
        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=token_expires),
            'user': jsonable_encoder(user),
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        return token

    @classmethod
    def get_user(cls, token: str) -> schemas.User:
        exception = cls._create_exception('Could not validate credentials')
        payload = cls.verify_token(token)
        user_data = payload.get('user')

        try:
            user = schemas.User.parse_obj(user_data)
        except ValidationError:
            raise exception from None

        return user

    @classmethod
    def _create_exception(
            cls,
            detail: str,
            status_code: int = HTTP_401_UNAUTHORIZED
    ) -> Exception:
        return HTTPException(
            status_code=status_code,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'}
        )

    @classmethod
    def _create_access_token(cls, user: Union[models.User, schemas.User]) -> str:
        if isinstance(user, models.User):
            user = schemas.User.from_orm(user)
        token_expires = settings.JWT_ACCESS_TOKEN_EXPIRES

        return cls.create_token(user, token_expires)

    @classmethod
    def _create_refresh_token(cls, user: Union[models.User, schemas.User]) -> str:
        if isinstance(user, models.User):
            user = schemas.User.from_orm(user)
        token_expires = settings.JWT_REFRESH_TOKEN_EXPIRES

        return cls.create_token(user, token_expires)

    def __init__(
            self,
            db_session: Session = Depends(get_db_session),
            redis_session: Redis = Depends(get_redis_session)
    ):
        self.db_session = db_session
        self.redis_session = redis_session

    async def _create_tokens(self, user: models.User) -> schemas.RefreshToken:
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        await self.redis_session.sadd(user.username, refresh_token)

        return schemas.RefreshToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def register_new_user(
            self,
            user_data: schemas.UserCreate,
    ) -> schemas.RefreshToken:
        db_user = (
            self.db_session
                .query(models.User)
                .with_entities(models.User.username, models.User.email)
                .filter(
                    (models.User.username == user_data.username) |
                    (models.User.email == user_data.email)
                )
                .first()
        )

        if db_user:
            key = 'email address' if db_user.email == user_data.email else 'username'
            exception = self._create_exception(
                f'A user is already registered with this {key}.'
            )
            raise exception from None

        user = models.User(
            email=user_data.email,
            username=user_data.username,
            password_hash=self.hash_password(user_data.password),
        )
        self.db_session.add(user)
        self.db_session.commit()

        return await self._create_tokens(user)

    async def authenticate_user(
            self,
            username: str,
            password: str,
    ) -> schemas.RefreshToken:
        exception = self._create_exception('Incorrect username or password')

        user = (
            self.db_session
                .query(models.User)
                .filter(models.User.username == username)
                .first()
        )

        if not user or not self.verify_password(password, user.password_hash):
            raise exception from None

        return await self._create_tokens(user)

    async def get_refresh_token(self, token: str) -> schemas.RefreshToken:
        exception = self._create_exception('Could not validate credentials')
        user = self.get_user(token)
        is_valid_token = await self.redis_session.srem(user.username, token)

        if not is_valid_token:
            raise exception from None

        return await self._create_tokens(user)
