"""Rutas HTTP de los usuarios.

`POST /users` es la única pública: es el registro. Las demás piden token
(`CurrentUser`), y quién puede hacer qué lo decide el service.

| Código | Cuándo |
| --- | --- |
| 200 | Lectura o cambio correcto |
| 201 | Cuenta creada, con su perfil |
| 204 | Cuenta borrada, con su perfil |
| 401 | Sin token, o token no válido o caducado |
| 403 | La cuenta no es la tuya y no eres admin, o cambias un rol sin ser admin |
| 404 | El ID no existe. Solo lo ve un admin: a los demás les llega antes el 403 |
| 409 | El email ya tiene cuenta |
| 422 | El cuerpo no cumple las reglas (lo responde FastAPI) |
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ...schemas import ErrorResponse
from ..auth.dependencies import UNAUTHORIZED, CurrentUser
from ..profiles.database import ProfileRepository
from ..profiles.dependencies import get_profile_repository
from . import service
from .database import UserRepository
from .dependencies import get_user_repository
from .exceptions import EmailAlreadyRegisteredError, NotAllowedError, UserNotFoundError
from .schemas import User, UserCreate, UserCreated, UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

Users = Annotated[UserRepository, Depends(get_user_repository)]
Profiles = Annotated[ProfileRepository, Depends(get_profile_repository)]

# Cada error del dominio, con su código HTTP.
_STATUS = {
    NotAllowedError: status.HTTP_403_FORBIDDEN,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    EmailAlreadyRegisteredError: status.HTTP_409_CONFLICT,
}
DomainError = (NotAllowedError, UserNotFoundError, EmailAlreadyRegisteredError)


def _http_error(error: Exception) -> HTTPException:
    return HTTPException(_STATUS[type(error)], str(error))


def _doc(description: str) -> dict:
    return {"model": ErrorResponse, "description": description}


FORBIDDEN = {403: _doc("La cuenta no es la tuya y no eres admin")}
NOT_FOUND = {404: _doc("No existe ningún usuario con ese ID")}
CONFLICT = {409: _doc("Ya existe una cuenta con ese email")}


@router.post(
    "",
    response_model=UserCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Registrarse (pública): crea la cuenta y su perfil",
    responses=CONFLICT,
)
def create_user(data: UserCreate, users: Users, profiles: Profiles, response: Response) -> UserCreated:
    """Siempre crea una cuenta `user`: el rol no se puede elegir al registrarse."""
    try:
        user, profile = service.create_user(users, profiles, data)
    except EmailAlreadyRegisteredError as error:
        raise _http_error(error) from error
    response.headers["Location"] = f"{router.prefix}/{user.id}"
    return UserCreated(**user.model_dump(exclude={"hashed_password"}), profile=profile)


@router.get(
    "",
    response_model=list[UserPublic],
    summary="Listar usuarios (solo admin)",
    responses={**UNAUTHORIZED, 403: _doc("Solo un admin puede listar usuarios")},
)
def list_users(caller: CurrentUser, users: Users) -> list[User]:
    try:
        return service.list_users(users, caller)
    except NotAllowedError as error:
        raise _http_error(error) from error


@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Consultar un usuario (el tuyo, o cualquiera si eres admin)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **NOT_FOUND},
)
def get_user(user_id: UUID, caller: CurrentUser, users: Users) -> User:
    try:
        return service.get_user_for(users, user_id, caller)
    except DomainError as error:
        raise _http_error(error) from error


@router.put(
    "/{user_id}",
    response_model=UserPublic,
    summary="Editar email, contraseña o rol (el rol, solo un admin)",
    responses={
        **UNAUTHORIZED,
        403: _doc("La cuenta no es la tuya, o cambias un rol sin ser admin"),
        **NOT_FOUND,
        **CONFLICT,
    },
)
def update_user(user_id: UUID, data: UserUpdate, caller: CurrentUser, users: Users) -> User:
    """Solo cambian los campos enviados. El perfil se edita en `PUT /profiles/me`."""
    try:
        return service.update_user(users, user_id, data, caller)
    except DomainError as error:
        raise _http_error(error) from error


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una cuenta y su perfil",
    responses={**UNAUTHORIZED, **FORBIDDEN, **NOT_FOUND},
)
def delete_user(user_id: UUID, caller: CurrentUser, users: Users, profiles: Profiles) -> None:
    """Sus tokens dejan de valer en el acto: el candado no encuentra la cuenta."""
    try:
        service.delete_user(users, profiles, user_id, caller)
    except DomainError as error:
        raise _http_error(error) from error
