"""El candado de las rutas protegidas: `get_current_user`.

Una ruta se protege pidiendo el usuario actual:

    def mi_ruta(caller: CurrentUser): ...

FastAPI ejecuta `get_current_user` antes que la ruta. Si no hay token, o no
vale, responde 401 y la ruta ni se ejecuta. Si vale, la ruta recibe el
`User` de la base de datos, con su rol de ahora, no el de cuando hizo login.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ...config import Settings
from ...dependencies import get_settings
from ..users import service as users_service
from ..users.database import UserRepository
from ..users.dependencies import get_user_repository
from ..users.exceptions import UserNotFoundError
from ..users.schemas import User
from .exceptions import InvalidTokenError
from .security import decode_access_token

# Lee `Authorization: Bearer <token>`. `tokenUrl` le dice a `/docs` dónde
# hacer login con el botón *Authorize*. `auto_error=False`: sin cabecera
# devuelve None y el 401 lo damos nosotros, con un mensaje en español.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def unauthorized(detail: str) -> HTTPException:
    # `WWW-Authenticate: Bearer` es lo que exige el estándar en un 401:
    # le dice al cliente con qué esquema autenticarse.
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """El usuario dueño del token. 401 ante cualquier fallo, sin decir cuál."""
    if not token:
        raise unauthorized("Falta el token. Inicia sesión en POST /auth/login.")
    try:
        user_id = decode_access_token(token, settings.require_jwt_secret())
        # Un token bien firmado de una cuenta ya borrada tampoco vale.
        user = users_service.get_user(users, user_id)
    except (InvalidTokenError, UserNotFoundError):
        raise unauthorized("Token no válido o caducado.") from None
    if not user.is_active:
        raise unauthorized("Token no válido o caducado.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
