"""Modelos Pydantic de los perfiles: nombre y datos de contacto.

Cada `User` tiene exactamente un `Profile`, vinculado por `user_id`. Se crea
con el usuario (`POST /users`) y se borra con él (`DELETE /users/{id}`).

Son datos personales: no se escriben en logs ni en mensajes de error.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

# Sin espacios sobrantes y no vacío: "  " no es un nombre. Para borrar un
# dato se envía null.
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
# Formato libre pero de teléfono: Valencia (+34) y Miami (+1) los escriben
# distinto, con espacios, guiones o paréntesis.
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()\-]{6,20}$")]
Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ProfileFields(BaseModel):
    """Los datos que escribe la persona. Todos opcionales."""

    name: Name | None = None
    phone: Phone | None = None
    address: Address | None = None


class ProfileUpdate(ProfileFields):
    """`PUT /profiles/me`: solo cambian los campos que lleguen.

    Un campo ausente se queda como estaba; uno a `null` se borra.
    """

    model_config = ConfigDict(extra="forbid")


class Profile(ProfileFields):
    """Lo que se guarda y lo que devuelve la API."""

    id: UUID
    user_id: UUID
