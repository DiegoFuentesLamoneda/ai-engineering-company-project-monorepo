"""Rutas HTTP de la recuperación y el cambio de contraseña (AUTH-03).

Van bajo `/auth`, junto al login, aunque vivan en su propio dominio.

| Ruta | Código | Cuándo |
| --- | --- | --- |
| `POST /auth/forgot-password` | 200 | **Siempre**, exista la cuenta o no |
| | 422 | El email no tiene forma de email |
| `POST /auth/reset-password` | 200 | Contraseña cambiada |
| | 400 | Enlace inventado, caducado o ya usado (el mismo mensaje para los tres) |
| | 422 | La contraseña nueva no cumple las reglas |
| `POST /auth/change-password` | 200 | Contraseña cambiada: devuelve un token nuevo |
| | 400 | La actual no coincide, o la nueva es igual que la actual |
| | 401 | Sin token, o token no válido o caducado |
| | 422 | La contraseña nueva no cumple las reglas |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ...config import Settings
from ...dependencies import get_settings
from ...mailer import Mailer
from ...schemas import ErrorResponse
from ..auth.dependencies import UNAUTHORIZED, CurrentUser
from ..auth.schemas import Token
from ..auth.security import create_access_token
from ..users.database import UserRepository
from ..users.dependencies import get_user_repository
from . import service
from .database import PasswordResetRepository
from .dependencies import get_mailer, get_password_reset_repository
from .exceptions import InvalidResetTokenError, SamePasswordError, WrongCurrentPasswordError
from .schemas import ChangePasswordRequest, ForgotPasswordRequest, Message, ResetPasswordRequest

router = APIRouter(prefix="/auth", tags=["auth"])

Users = Annotated[UserRepository, Depends(get_user_repository)]
Resets = Annotated[PasswordResetRepository, Depends(get_password_reset_repository)]


@router.post(
    "/forgot-password",
    response_model=Message,
    summary="Pedir un enlace para restablecer la contraseña",
)
def forgot_password(
    data: ForgotPasswordRequest,
    background: BackgroundTasks,
    users: Users,
    resets: Resets,
    mailer: Annotated[Mailer, Depends(get_mailer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Message:
    """Responde siempre lo mismo, y enseguida.

    Buscar la cuenta y enviar el email va en una tarea que FastAPI ejecuta
    **después** de responder: así ni el texto ni el tiempo de la respuesta
    dicen si el email tiene cuenta.
    """
    background.add_task(service.request_reset, users, resets, mailer, settings, data.email)
    return Message(message=service.FORGOT_PASSWORD_MESSAGE)


@router.post(
    "/reset-password",
    response_model=Message,
    summary="Elegir una contraseña nueva con el enlace del email",
    responses={400: {"model": ErrorResponse, "description": "Enlace no válido, caducado o ya usado"}},
)
def reset_password(data: ResetPasswordRequest, users: Users, resets: Resets) -> Message:
    try:
        service.reset_password(users, resets, data.token, data.new_password)
    except InvalidResetTokenError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    return Message(message="Contraseña actualizada. Ya puedes iniciar sesión.")


@router.post(
    "/change-password",
    response_model=Token,
    summary="Cambiar la contraseña con la sesión iniciada",
    responses={
        **UNAUTHORIZED,
        400: {"model": ErrorResponse, "description": "La actual no coincide o la nueva es igual"},
    },
)
def change_password(
    data: ChangePasswordRequest,
    caller: CurrentUser,
    users: Users,
    resets: Resets,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """Devuelve un token nuevo.

    Cambiar la contraseña invalida todos los tokens emitidos antes, también
    el de esta sesión. Con el nuevo, quien la cambia sigue dentro y
    cualquier otra sesión abierta con la contraseña vieja se cierra.
    """
    try:
        service.change_password(users, resets, caller, data.current_password, data.new_password)
    except (WrongCurrentPasswordError, SamePasswordError) as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    minutes = settings.access_token_expire_minutes
    token = create_access_token(caller.id, settings.require_jwt_secret(), minutes)
    return Token(access_token=token, expires_in=minutes * 60)
