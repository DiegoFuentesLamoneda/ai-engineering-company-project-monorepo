"""Reglas del restablecimiento y el cambio de contraseña.

Dos niveles:

- **Tokens:** `issue_token` y `consume_token`, emitirlos y gastarlos.
- **Flujos de las rutas:** `request_reset` (pedir el enlace), `reset_password`
  (usarlo) y `change_password` (cambiarla con la actual). El router solo
  traduce sus errores a códigos HTTP.

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
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from ...config import Settings
from ...mailer import EmailDeliveryError, Mailer, mask_email
from ..users import service as users_service
from ..users.database import UserRepository
from ..users.schemas import User
from .database import PasswordResetRepository
from .emails import build_reset_email, reset_link
from .exceptions import (
    InvalidResetReason,
    InvalidResetTokenError,
    SamePasswordError,
    WrongCurrentPasswordError,
)
from .schemas import ResetToken

logger = logging.getLogger("nexova.password_resets")

# Lo que responde `POST /auth/forgot-password` siempre, exista la cuenta o no.
FORGOT_PASSWORD_MESSAGE = "Si esa dirección está registrada, recibirás un enlace en breve."

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


# --- Flujos de las rutas ---------------------------------------------------


def request_reset(
    users: UserRepository,
    resets: PasswordResetRepository,
    mailer: Mailer,
    settings: Settings,
    email: str,
) -> None:
    """Si `email` es de una cuenta activa, le envía un enlace. Si no, nada.

    No devuelve nada **a propósito**: la ruta responde lo mismo en los dos
    casos y llama a esto *después* de responder (una tarea en segundo plano).
    Si buscase la cuenta y enviase el email antes de responder, una cuenta
    existente tardaría más en contestar, y el tiempo de respuesta delataría
    qué emails están registrados.

    Un fallo de Resend se queda en el log: la respuesta ya salió, y a quien
    lo pidió tampoco se le podría decir sin revelar que la cuenta existe.
    """
    user = users.get_by_email(email)
    # Una cuenta desactivada no puede iniciar sesión: un enlace no le serviría.
    if user is None or not user.is_active:
        return
    token = issue_token(resets, user.id, settings.reset_token_expire_minutes)
    message = build_reset_email(
        user.email,
        reset_link(settings.frontend_url, token),
        settings.reset_token_expire_minutes,
    )
    try:
        mailer.send(message)
    except EmailDeliveryError as error:
        logger.error("No se pudo enviar el enlace a %s: %s", mask_email(user.email), error)


def reset_password(
    users: UserRepository,
    resets: PasswordResetRepository,
    token: str,
    new_password: str,
    now: datetime | None = None,
) -> User:
    """Gasta el token y pone la contraseña nueva. `InvalidResetTokenError` si no vale.

    Primero se gasta el token y después se cambia la contraseña: si dos
    peticiones llegan con el mismo enlace, solo la que gana cambia nada.
    """
    user_id = consume_token(resets, token, now)
    user = users.get(user_id)
    # La cuenta se borró o se desactivó después de pedir el enlace.
    if user is None or not user.is_active:
        raise InvalidResetTokenError(InvalidResetReason.UNKNOWN)
    return users_service.set_password(users, user_id, new_password, now)


def change_password(
    users: UserRepository,
    resets: PasswordResetRepository,
    user: User,
    current_password: str,
    new_password: str,
    now: datetime | None = None,
) -> User:
    """Cambia la contraseña de quien tiene la sesión, si sabe la actual.

    Pedir la actual aunque haya sesión: si alguien se deja el portátil
    abierto, quien se siente delante no puede quedarse con la cuenta.
    """
    if not users_service.verify_password(current_password, user.hashed_password):
        raise WrongCurrentPasswordError()
    if new_password == current_password:
        raise SamePasswordError()
    updated = users_service.set_password(users, user.id, new_password, now)
    # Un enlace de restablecimiento pendiente ya no tiene sentido.
    resets.delete_pending_for_user(user.id)
    return updated
