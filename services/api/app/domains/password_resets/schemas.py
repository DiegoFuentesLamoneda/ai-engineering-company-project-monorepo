"""Modelos del restablecimiento de contraseña.

`ResetToken` es lo que se guarda de cada enlace enviado. **No guarda el
token**, solo su hash: quien lea el fichero de TinyDB (una copia de
seguridad, un disco robado) no puede usar ningún enlace pendiente. Es el
mismo motivo por el que no se guardan las contraseñas, solo su hash.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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
