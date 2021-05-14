from fastapi import APIRouter

from . import auth
from . import blog_post


api_router = APIRouter(
    prefix='/v1',
    tags=['v1', ]
)


api_router.include_router(auth.router)
api_router.include_router(blog_post.router)
