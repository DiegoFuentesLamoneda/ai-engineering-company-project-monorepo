"""Rutas HTTP de la autenticación.

| Código | Cuándo |
| --- | --- |
| 200 | Login correcto (devuelve el token) o `GET /auth/me` con token válido |
| 401 | Credenciales incorrectas, o token ausente, caducado o manipulado |
| 404 | La cuenta no tiene perfil (no debería pasar: nace con ella) |
| 422 | Falta el email o la contraseña en el formulario (lo responde FastAPI) |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ...config import Settings
from ...dependencies import get_settings
from ...schemas import ErrorResponse
from ..profiles import service as profiles_service
from ..profiles.database import ProfileRepository
from ..profiles.dependencies import get_profile_repository
from ..profiles.exceptions import ProfileNotFoundError
from ..users import service as users_service
from ..users.database import UserRepository
from ..users.dependencies import get_user_repository
from .dependencies import UNAUTHORIZED, CurrentUser, unauthorized
from .schemas import Me, Token
from .security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión y obtener un token",
    responses={401: {"model": ErrorResponse, "description": "Email o contraseña incorrectos"}},
)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """Formulario OAuth2: **en `username` va el email**.

    El estándar llama `username` al campo, y respetarlo es lo que permite
    hacer login desde el botón *Authorize* de `/docs`. El token se envía
    después en la cabecera `Authorization: Bearer <token>`.
    """
    user = users_service.authenticate(users, form.username, form.password)
    if user is None:
        raise unauthorized("Email o contraseña incorrectos.")
    minutes = settings.access_token_expire_minutes
    token = create_access_token(user.id, settings.require_jwt_secret(), minutes)
    return Token(access_token=token, expires_in=minutes * 60)


@router.get(
    "/me",
    response_model=Me,
    summary="Quién soy: email, rol y perfil",
    responses={
        **UNAUTHORIZED,
        404: {"model": ErrorResponse, "description": "La cuenta no tiene perfil"},
    },
)
def me(
    caller: CurrentUser,
    profiles: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> Me:
    try:
        profile = profiles_service.get_profile(profiles, caller.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from None
    return Me(id=caller.id, email=caller.email, role=caller.role, profile=profile)
