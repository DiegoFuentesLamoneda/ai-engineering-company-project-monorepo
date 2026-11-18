"""Reglas de los tokens de restablecimiento: emitirlos y gastarlos.

Por qué un token aleatorio guardado en la base de datos y no un JWT: un JWT
con `exp` caduca solo, pero **no se puede invalidar después de usarlo**, y
el ticket exige que un enlace no sirva dos veces. Para eso el servidor
tiene que recordar algo. Aquí recuerda el hash de cada token, cuándo caduca
y si ya se usó.

No importa fastapi. `now` es un parámetro para que las pruebas fijen la
hora; en la API se queda sin pasar y vale la hora actual en UTC.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from .database import PasswordResetRepository
from .exceptions import InvalidResetReason, InvalidResetTokenError
from .schemas import ResetToken

# 32 bytes aleatorios = 256 bits: imposible de adivinar por fuerza bruta.
# `token_urlsafe` los codifica con letras, números, - y _, que viajan en una
# URL sin escapar. Salen 43 caracteres.
TOKEN_BYTES = 32


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    """SHA-256 y no bcrypt, como las contraseñas.

    bcrypt es lento a propósito porque las contraseñas las elige una
    persona y se pueden adivinar probando millones. Este token tiene 256
    bits de azar: no hay nada que adivinar, así que basta un hash rápido.
    Y al ser determinista (sin sal), se puede buscar por él en la base.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_token(
    repo: PasswordResetRepository,
    user_id: UUID,
    expire_minutes: int,
    now: datetime | None = None,
) -> str:
    """Emite un token para `user_id` y lo devuelve **en claro**, para el email.

    Es la única vez que el token existe en claro: se guarda solo su hash.
    Pedir un enlace nuevo anula los anteriores sin usar: solo vale el último
    email, y uno viejo olvidado en la bandeja de entrada deja de servir.
    """
    issued_at = _now(now)
    repo.delete_expired(issued_at)
    repo.delete_pending_for_user(user_id)
    token = secrets.token_urlsafe(TOKEN_BYTES)
    repo.insert(
        ResetToken(
            id=uuid4(),
            user_id=user_id,
            token_hash=hash_token(token),
            created_at=issued_at,
            expires_at=issued_at + timedelta(minutes=expire_minutes),
        )
    )
    return token


def consume_token(
    repo: PasswordResetRepository,
    token: str,
    now: datetime | None = None,
) -> UUID:
    """Gasta el token y devuelve de quién es. `InvalidResetTokenError` si no vale.

    Tres comprobaciones, en este orden: que exista, que no se haya usado y
    que no haya caducado. Después se marca como usado; si otra petición se
    ha adelantado con el mismo enlace, esta pierde.
    """
    current = _now(now)
    stored = repo.get_by_hash(hash_token(token))
    if stored is None:
        raise InvalidResetTokenError(InvalidResetReason.UNKNOWN)
    if stored.used_at is not None:
        raise InvalidResetTokenError(InvalidResetReason.USED)
    if stored.expires_at <= current:
        raise InvalidResetTokenError(InvalidResetReason.EXPIRED)
    if not repo.mark_used(stored.id, current):
        raise InvalidResetTokenError(InvalidResetReason.USED)
    # Si había otro enlace pendiente (no debería: emitir uno anula los
    # anteriores), tampoco sirve ya. La contraseña acaba de cambiar.
    repo.delete_pending_for_user(stored.user_id)
    return stored.user_id
