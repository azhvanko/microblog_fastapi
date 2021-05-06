from fastapi import APIRouter

from . import auth


api_router = APIRouter(
    prefix='/api/v1',
    tags=['api', ]
)


api_router.include_router(auth.router)
