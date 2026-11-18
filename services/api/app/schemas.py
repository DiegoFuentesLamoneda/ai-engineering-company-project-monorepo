"""Modelos transversales: los que comparten todos los dominios."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Forma de todos los errores que lanza la API: `{"detail": "mensaje"}`.

    Los 422 de validación de FastAPI llevan en `detail` una lista de errores
    por campo; el backoffice entiende las dos formas (`lib/api.ts`).
    """

    detail: str
