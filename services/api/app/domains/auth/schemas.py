"""Contratos de salida de la autenticación."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from ..profiles.schemas import Profile
from ..users.schemas import Role


class Token(BaseModel):
    """La forma que espera OAuth2, y con ella el botón *Authorize* de `/docs`."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    # Segundos de validez: el frontend sabe cuándo pedir login otra vez.
    expires_in: int


class Me(BaseModel):
    """`GET /auth/me`: quién soy, con qué rol y mi perfil.

    Lleva también el `id`: el frontend lo necesita para `PUT /users/{id}`.
    """

    id: UUID
    email: str
    role: Role
    profile: Profile
