from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from ... import schemas
from ...services.auth import get_user
from ...services.blog_post import BlogPostService


router = APIRouter(
    prefix='',
    tags=['blog_post', ],
)


@router.post(
    '/posts/create',
    response_model=schemas.BlogPost,
    status_code=status.HTTP_201_CREATED,
)
async def create_blog_post(
    user_data: schemas.BlogPostCreate,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    return await blog_post_service.create_blog_post(user, user_data)


@router.put(
    '/users/{username}/{post_id}',
    response_model=schemas.BlogPost
)
async def update_blog_post(
    username: str,
    post_id: int,
    user_data: schemas.BlogPostUpdate,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    return await blog_post_service.update_blog_post(user, user_data, post_id)


@router.put(
    '/users/{username}/{post_id}/archive'
)
async def archive_blog_post(
    username: str,
    post_id: int,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    _ = await blog_post_service.archive_blog_post(user, post_id)
    return JSONResponse({'status': 'ok'})


@router.delete(
    '/users/{username}/{post_id}'
)
async def delete_blog_post(
    username: str,
    post_id: int,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    _ = await blog_post_service.delete_blog_post(user, post_id)
    return JSONResponse({'status': 'ok'})


@router.post(
    '/users/{username}/{post_id}/repost',
)
async def create_blog_post_repost(
    username: str,
    post_id: int,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    _ = await blog_post_service.create_blog_post_repost(user, post_id)
    return JSONResponse({'status': 'ok'})


@router.delete(
    '/users/{username}/{post_id}/repost/delete',
)
async def delete_blog_post_repost(
    username: str,
    post_id: int,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    _ = await blog_post_service.delete_blog_post_repost(user, post_id)
    return JSONResponse({'status': 'ok'})


@router.post(
    '/users/{username}/{post_id}/like',
)
async def add_blog_post_like(
    username: str,
    post_id: int,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    _ = await blog_post_service.add_blog_post_like(user, username, post_id)
    return JSONResponse({'status': 'ok'})


@router.put(
    '/users/{username}/{post_id}/dislike',
)
async def remove_blog_post_like(
    username: str,
    post_id: int,
    user: schemas.User = Depends(get_user),
    blog_post_service: BlogPostService = Depends(),
):
    _ = await blog_post_service.remove_blog_post_like(user, post_id)
    return JSONResponse({'status': 'ok'})
