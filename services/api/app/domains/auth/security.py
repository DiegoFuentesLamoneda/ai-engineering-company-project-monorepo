"""Tokens JWT: firmarlos al hacer login y comprobarlos en cada petición.

Un JWT son tres partes en base64 separadas por puntos: cabecera, datos
(*claims*) y firma. Los datos **no están cifrados**, cualquiera puede leerlos;
lo que garantiza la firma es que nadie los ha cambiado. Por eso solo llevan
el ID del usuario y las fechas, nunca el email ni el rol.

El rol tampoco va dentro por otro motivo: en cada petición se carga el
usuario de la base de datos, así que un cambio de rol o una cuenta borrada
tienen efecto en la siguiente petición, sin esperar a que el token caduque.

No importa fastapi: recibe el secreto y devuelve datos o lanza errores.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from pydantic import SecretStr

from .exceptions import InvalidTokenError

# HMAC con SHA-256: la misma clave firma y comprueba. Basta porque la API es
# la única que emite y verifica sus tokens.
ALGORITHM = "HS256"


def create_access_token(
    user_id: UUID,
    secret: SecretStr,
    expires_minutes: int,
    now: datetime | None = None,
) -> str:
    """`sub` (de *subject*): de quién es el token. `exp`: hasta cuándo vale."""
    issued_at = now or datetime.now(timezone.utc)
    claims = {
        "sub": str(user_id),
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(claims, secret.get_secret_value(), algorithm=ALGORITHM)


def decode_access_token(token: str, secret: SecretStr) -> UUID:
    """El ID del usuario del token, o `InvalidTokenError` si no se puede confiar en él."""
    try:
        claims = jwt.decode(
            token,
            secret.get_secret_value(),
            # Lista cerrada: un token con `"alg": "none"` (sin firma) o con
            # otro algoritmo se rechaza en vez de aceptarse sin comprobar.
            algorithms=[ALGORITHM],
            # Sin `exp` el token valdría para siempre; sin `sub`, no es de nadie.
            options={"require_exp": True, "require_sub": True},
        )
        return UUID(claims["sub"])
    except (JWTError, KeyError, ValueError, TypeError) as error:
        raise InvalidTokenError() from error
