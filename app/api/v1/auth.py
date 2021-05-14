from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from ... import schemas
from ...core import settings
from ...services.auth import AuthService, get_user, oauth2_scheme


router = APIRouter(
    prefix='/auth',
    tags=['auth', ],
)


@router.post(
    '/sign-up',
    response_model=schemas.RefreshToken,
    status_code=status.HTTP_201_CREATED,
)
async def sign_up(
    user_data: schemas.UserCreate,
    auth_service: AuthService = Depends(),
):
    tokens = await auth_service.register_new_user(user_data)
    response = JSONResponse(
        {'token_type': tokens.token_type, 'access_token': tokens.access_token}
    )
    response.set_cookie(
        'refresh_token',
        tokens.refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRES,
        httponly=True
    )
    response.status_code = status.HTTP_201_CREATED
    return response


@router.post(
    '/sign-in',
    response_model=schemas.RefreshToken,
)
async def sign_in(
    auth_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(),
):
    tokens = await auth_service.authenticate_user(
        auth_data.username,
        auth_data.password,
    )
    response = JSONResponse(
        {'token_type': tokens.token_type, 'access_token': tokens.access_token}
    )
    response.set_cookie(
        'refresh_token',
        tokens.refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRES,
        httponly=True
    )
    return response


@router.put(
    '/refresh',
    response_model=schemas.RefreshToken,
)
async def get_refresh_token(
        token: str = Depends(oauth2_scheme),
        auth_service: AuthService = Depends()
):
    tokens = await auth_service.get_refresh_token(token)
    response = JSONResponse(
        {'token_type': tokens.token_type, 'access_token': tokens.access_token}
    )
    response.set_cookie(
        'refresh_token',
        tokens.refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRES,
        httponly=True
    )
    response.status_code = status.HTTP_201_CREATED
    return response


@router.get(
    '/user',
    response_model=schemas.User,
)
async def get_user(user: str = Depends(get_user)):
    return user
