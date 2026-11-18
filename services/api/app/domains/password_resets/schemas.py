"""Modelos del restablecimiento y el cambio de contraseña.

Las entradas (`*Request`) rechazan campos que no conocen y validan el email
y la contraseña con las mismas reglas que el alta (`users.schemas`).

`ResetToken` es lo que se guarda de cada enlace enviado. **No guarda el
token**, solo su hash: quien lea el fichero de TinyDB (una copia de
seguridad, un disco robado) no puede usar ningún enlace pendiente. Es el
mismo motivo por el que no se guardan las contraseñas, solo su hash.

`AuditEntry` es una línea del registro de auditoría: qué pasó, cuándo, desde
qué IP y con qué cuenta. Decidido con Diego el 18/11/2026: **la cuenta se
anota por su `user_id`, nunca por el email** (un email sin cuenta no se
guarda: no acumulamos direcciones de terceros), la IP va completa y las
entradas se borran solas a los 90 días.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..users.schemas import Email, Password

# Un token emitido mide 43 caracteres. El límite solo frena a quien envíe un
# texto enorme para que la API lo procese.
MAX_TOKEN_LENGTH = 128


class ResetToken(BaseModel):
    """Un enlace de restablecimiento emitido. Uso interno: nunca sale por la API."""

    id: UUID
    user_id: UUID
    # SHA-256 del token en hexadecimal. El token en claro solo existe en el
    # email y durante la petición que lo emite.
    token_hash: str
    created_at: datetime
    expires_at: datetime
    # Cuándo se usó para cambiar la contraseña. Con fecha, ya no vale: es lo
    # que impide que el mismo enlace sirva dos veces.
    used_at: datetime | None = None


class AuditEvent(StrEnum):
    """Qué pasó. Cada petición de las tres rutas deja exactamente una entrada.

    Excepción: un enlace emitido cuyo email falla deja dos, `reset_link_issued`
    y `reset_link_not_sent` con `delivery_failed`.
    """

    # forgot-password. `issued` es lo que cuenta para el límite por hora.
    RESET_LINK_ISSUED = "reset_link_issued"
    RESET_LINK_NOT_SENT = "reset_link_not_sent"
    # reset-password
    PASSWORD_RESET = "password_reset"
    PASSWORD_RESET_FAILED = "password_reset_failed"
    # change-password
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_CHANGE_FAILED = "password_change_failed"


class NotSentReason(StrEnum):
    """Por qué `forgot-password` no envió el enlace. La respuesta no lo dice."""

    UNKNOWN_ACCOUNT = "unknown_account"
    INACTIVE_ACCOUNT = "inactive_account"
    RATE_LIMITED = "rate_limited"
    DELIVERY_FAILED = "delivery_failed"


class ChangeFailedReason(StrEnum):
    WRONG_CURRENT_PASSWORD = "wrong_current_password"
    SAME_PASSWORD = "same_password"


class AuditEntry(BaseModel):
    """Una línea del registro. Uso interno: nunca sale por la API."""

    id: UUID
    created_at: datetime
    event: AuditEvent
    # `None` cuando no hay cuenta: un email sin registrar o un enlace inventado.
    user_id: UUID | None = None
    # La IP que ve la API (`request.client.host`). Detrás de un proxy sería
    # la del proxy: ver "Limitaciones conocidas" en el README.
    ip: str | None = None
    # Uno de los `*Reason` de arriba o `InvalidResetReason`, según `event`.
    reason: str | None = None


class ForgotPasswordRequest(BaseModel):
    """`POST /auth/forgot-password`."""

    model_config = ConfigDict(extra="forbid")

    email: Email


class ResetPasswordRequest(BaseModel):
    """`POST /auth/reset-password`: el token del enlace y la contraseña nueva."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1, max_length=MAX_TOKEN_LENGTH)
    new_password: Password


class ChangePasswordRequest(BaseModel):
    """`POST /auth/change-password`: con sesión iniciada y la contraseña actual."""

    model_config = ConfigDict(extra="forbid")

    # La actual no pasa por `Password`: si alguien la tiene de 7 caracteres
    # de antes de la regla, tiene que poder cambiarla. Basta con que coincida.
    current_password: str = Field(min_length=1, max_length=256)
    new_password: Password


class Message(BaseModel):
    """Respuesta de las rutas que solo confirman: `{"message": "..."}`."""

    message: str
