"""Errores del restablecimiento de contraseña.

No saben nada de HTTP: el `service` los lanza y el `router` decide el código.
"""

from __future__ import annotations

from enum import StrEnum


class InvalidResetReason(StrEnum):
    """Por qué no vale un token. Solo para el registro de auditoría."""

    UNKNOWN = "unknown"  # nunca se emitió, o se sustituyó por uno más nuevo
    EXPIRED = "expired"
    USED = "used"


class InvalidResetTokenError(Exception):
    """El token no sirve para restablecer la contraseña.

    El mensaje es el mismo sea cual sea el motivo: a quien tiene el enlace le
    basta con saber que tiene que pedir otro. El motivo concreto va en
    `reason`, para la auditoría, no para la respuesta.
    """

    def __init__(self, reason: InvalidResetReason) -> None:
        super().__init__("El enlace de restablecimiento no es válido o ha caducado. Pide uno nuevo.")
        self.reason = reason
