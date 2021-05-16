from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND

from .. import models, schemas
from ..database.session import get_db_session


class FollowerService:

    @classmethod
    def _create_exception(
            cls,
            detail: str,
            status_code: int = HTTP_404_NOT_FOUND
    ) -> Exception:
        return HTTPException(
            status_code=status_code,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'}
        )

    def __init__(self, db_session: Session = Depends(get_db_session)):
        self.db_session = db_session

    def _get_user(self, username: str) -> Optional[models.User]:
        user = (
            self.db_session
                .query(models.User)
                .filter(models.User.username == username)
                .first()
        )

        return user

    async def follow_user(self, user: schemas.User, username: str) -> None:
        if user.username == username:
            return

        db_user = self._get_user(username)

        if db_user is None or not db_user.is_active:
            exception = self._create_exception('invalid username')
            raise exception from None

        follower = models.Follower(follower_id=user.id, user_id=db_user.id)

        self.db_session.add(follower)
        self.db_session.commit()

    async def unfollow_user(self, user: schemas.User, username: str) -> None:
        if user.username == username:
            return

        db_user = self._get_user(username)

        if db_user is None or not db_user.is_active:
            exception = self._create_exception('invalid username')
            raise exception from None

        follower = (
            self.db_session
                .query(models.Follower)
                .filter(
                    (models.Follower.user_id == db_user.id) &
                    (models.Follower.follower_id == user.id) &
                    (models.Follower.is_active)
                )
                .first()
        )

        if follower is None:
            exception = self._create_exception('invalid username')
            raise exception from None

        follower.is_active = False

        self.db_session.add(follower)
        self.db_session.commit()
