from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from ... import schemas
from ...services.auth import get_user
from ...services.follower import FollowerService


router = APIRouter(
    prefix='/users',
    tags=['follower', ],
)


@router.post(
    '/{username}/follow',
    status_code=status.HTTP_201_CREATED,
)
async def follow_user(
    username: str,
    user: schemas.User = Depends(get_user),
    follower_service: FollowerService = Depends(),
):
    _ = await follower_service.follow_user(user, username)
    return JSONResponse({'status': 'ok'}, status_code=status.HTTP_201_CREATED)


@router.put(
    '/{username}/unfollow'
)
async def unfollow_user(
    username: str,
    user: schemas.User = Depends(get_user),
    follower_service: FollowerService = Depends(),
):
    _ = await follower_service.unfollow_user(user, username)
    return JSONResponse({'status': 'ok'})
