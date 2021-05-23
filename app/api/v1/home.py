from fastapi import APIRouter, Depends

from ... import schemas
from ...services.auth import get_user
from ...services.home import HomeService


router = APIRouter(
    prefix='',
    tags=['home', ],
)


@router.get(
    '/home',
    response_model=list[schemas.HomeBlogPost]
)
async def home(
    user: schemas.User = Depends(get_user),
    home_service: HomeService = Depends(),
):
    return await home_service.home(user)
