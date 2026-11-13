"""Rutas HTTP de los perfiles: solo el tuyo.

No hay `/profiles/{id}`: la ruta es `/me` y el perfil sale del token. Así no
hay forma de pedir el de otra persona, ni un 403 que comprobar.

| Código | Cuándo |
| --- | --- |
| 200 | Lectura o cambio correcto |
| 401 | Sin token, o token no válido o caducado |
| 404 | La cuenta no tiene perfil (no debería pasar: nace con ella) |
| 422 | El cuerpo no cumple las reglas (lo responde FastAPI) |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ...schemas import ErrorResponse
from ..auth.dependencies import UNAUTHORIZED, CurrentUser
from . import service
from .database import ProfileRepository
from .dependencies import get_profile_repository
from .exceptions import ProfileNotFoundError
from .schemas import Profile, ProfileUpdate

# Todas las rutas de aquí piden token: el 401 se documenta una vez.
router = APIRouter(prefix="/profiles", tags=["profiles"], responses=UNAUTHORIZED)

Profiles = Annotated[ProfileRepository, Depends(get_profile_repository)]

NOT_FOUND = {404: {"model": ErrorResponse, "description": "La cuenta no tiene perfil"}}


@router.get("/me", response_model=Profile, summary="Mi perfil", responses=NOT_FOUND)
def get_my_profile(caller: CurrentUser, profiles: Profiles) -> Profile:
    try:
        return service.get_profile(profiles, caller.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@router.put("/me", response_model=Profile, summary="Editar mi perfil", responses=NOT_FOUND)
def update_my_profile(data: ProfileUpdate, caller: CurrentUser, profiles: Profiles) -> Profile:
    """Solo cambian los campos enviados; uno a `null` se borra."""
    try:
        return service.update_profile(profiles, caller.id, data)
    except ProfileNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
