"""Modelos Pydantic de los usuarios: solo credenciales.

El nombre y los datos de contacto no viven aquí, sino en el `Profile`
vinculado (dominio `profiles`). Un `User` es lo justo para autenticarse.

Hay modelos separados para cada dirección:

- `UserCreate` y `UserUpdate`: lo que puede enviar el cliente. Llevan la
  contraseña en claro, que solo existe durante la petición. Rechazan
  cualquier campo que no conozcan (`extra="forbid"`): un `role` en el alta
  es un 422, así que nadie se registra como admin.
- `User`: lo que se guarda, con `hashed_password`. **Nunca sale por la API.**
- `UserPublic`: lo que devuelve la API. Sin `hashed_password`: aunque una ruta
  devolviera el `User` entero por error, FastAPI lo filtra con este modelo.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from ..profiles.schemas import ProfileFields


class Role(StrEnum):
    """Roles de la API. Cualquier otro valor es un 422."""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


# Validación de forma, sin comprobar que el buzón exista: el mismo criterio
# que proveedores, para no añadir una librería de emails. Se guarda en
# minúsculas para que Ana@nexova.es y ana@nexova.es sean la misma cuenta.
Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]

# bcrypt solo usa los primeros 72 bytes de la contraseña, y bcrypt 5 rechaza
# las más largas con un error. Se valida en bytes y no en caracteres: una
# tilde o un emoji ocupan más de uno.
MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 8


def _fits_in_bcrypt(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"La contraseña no puede ocupar más de {MAX_PASSWORD_BYTES} bytes")
    return password


Password = Annotated[str, Field(min_length=MIN_PASSWORD_LENGTH), AfterValidator(_fits_in_bcrypt)]


class UserCreate(ProfileFields):
    """`POST /users`: credenciales y, opcionalmente, el perfil inicial.

    Hereda `name`, `phone` y `address` de `ProfileFields`, con sus mismas
    reglas. El service los separa: las credenciales van al `User` y el resto
    al `Profile`, que se crea en la misma operación.
    """

    model_config = ConfigDict(extra="forbid")

    email: Email
    password: Password


class UserUpdate(BaseModel):
    """`PUT /users/{id}`: solo los campos que lleguen cambian.

    Un campo a `null` se ignora: una cuenta no puede quedarse sin email,
    contraseña ni rol.

    `role` lo puede cambiar únicamente un admin. Esa regla depende de quién
    llama, así que la comprueba el service, no el modelo.
    """

    model_config = ConfigDict(extra="forbid")

    email: Email | None = None
    password: Password | None = None
    role: Role | None = None


class UserPublic(BaseModel):
    """Lo que la API enseña de un usuario."""

    id: UUID
    email: str
    role: Role
    is_active: bool
    created_at: datetime


class User(UserPublic):
    """Lo que se guarda en TinyDB. Uso interno: nunca es un `response_model`.

    `id` es un UUID que genera la API, no el número que asigna TinyDB:
    TinyDB reutiliza los números borrados, y el token de un usuario borrado
    identificaría al siguiente que se registrase. Es el `user_uuid` con el
    que los demás módulos se refieren al usuario.
    """

    hashed_password: str
