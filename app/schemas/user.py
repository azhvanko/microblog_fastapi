import re
from datetime import datetime
from string import ascii_lowercase, ascii_uppercase

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    root_validator,
    validator
)

DIGITS = set(str(i) for i in range(10))
LOWERCASE_LETTERS = set(ascii_lowercase)
UPPERCASE_LETTERS = set(ascii_uppercase)


def validate_password(username: str, password: str) -> None:
    result = 0
    result += any(i in DIGITS for i in password)
    result += any(i in LOWERCASE_LETTERS for i in password)
    result += any(i in UPPERCASE_LETTERS for i in password)

    if not (result == 3 and not re.search(r'\s', password)):
        raise ValueError(
            'Your password must be at least 8 characters long, and include '
            'at least one lowercase letter, one uppercase letter, and a number.'
        ) from None

    if username == password.lower() or username == password.lower()[::-1]:
        raise ValueError(
            'Your password is too similar to your username'
        ) from None


class BaseUser(BaseModel):
    username: str = Field(..., min_length=5, max_length=128)
    email: EmailStr

    @validator('username', 'email')
    def check_username(cls, value: str) -> str:
        return value.strip().lower()


class UserCreate(BaseUser):
    password: str = Field(..., min_length=8, max_length=128)

    @root_validator
    def check(cls, values):
        username, password = values.get('username'), values.get('password')
        validate_password(username, password)
        return values


class User(BaseUser):
    id: int
    date_joined: datetime

    class Config:
        orm_mode = True


class AccessToken(BaseModel):
    token_type: str = 'bearer'
    access_token: str


class RefreshToken(AccessToken):
    refresh_token: str
