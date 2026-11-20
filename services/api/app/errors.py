"""El 500 de la API: un mensaje genérico para quien llama, el detalle en el log.

Sin esto, un error no previsto ya no enseña el stack trace (Starlette
responde con un texto plano, "Internal Server Error"), pero tiene dos
problemas:

- No es JSON con la forma `{"detail": "..."}` que el resto de errores.
- Lo genera la capa más externa de la app, por fuera de CORS: la respuesta
  sale sin `Access-Control-Allow-Origin` y el navegador la oculta. El
  frontend no ve un 500, ve un "Failed to fetch" sin explicación.

Por eso es un middleware y no un `exception_handler(Exception)`: se añade
antes que CORS, que queda por fuera y pone sus cabeceras también al 500.

Junto a él, dos manejadores para errores que sí se esperan y tienen su código:

- `validation_error_handler`: el 422 de FastAPI sin el campo `input`, que
  devolvía tal cual lo que escribió el usuario (contraseñas incluidas).
- `storage_unavailable_handler`: el 503 cuando no se puede leer o escribir
  un fichero de TinyDB (ver `json_storage.py`).
"""

from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("nexova.errors")

GENERIC_ERROR = "Ha ocurrido un error inesperado en el servidor. Inténtalo de nuevo en unos minutos."

STORAGE_UNAVAILABLE = "El servicio no está disponible en este momento. Inténtalo de nuevo en unos minutos."

# Lo que se devuelve de cada error de validación. Fuera quedan `input` (el
# valor recibido: una contraseña, un token) y `ctx` (que puede repetirlo).
VALIDATION_ERROR_KEYS = ("loc", "msg", "type")


class StorageUnavailableError(RuntimeError):
    """Un fichero de TinyDB no se puede leer o escribir: corrupto, sin permisos o sin disco."""


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """El 422 de siempre, con la misma lista en `detail`, pero sin repetir lo que se envió."""
    errors = [{key: error[key] for key in VALIDATION_ERROR_KEYS if key in error} for error in exc.errors()]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": errors})


async def storage_unavailable_handler(request: Request, exc: StorageUnavailableError) -> JSONResponse:
    """503: no es un fallo del código ni de la petición, es la base de datos. El detalle, al log."""
    logger.exception("Almacenamiento no disponible en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": STORAGE_UNAVAILABLE}
    )


class UnexpectedErrorMiddleware:
    """Convierte cualquier excepción no prevista en un 500 JSON sin detalles internos.

    Middleware ASGI puro (no `BaseHTTPMiddleware`): no toca el cuerpo de las
    peticiones que funcionan y no cambia cómo corren las rutas.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception:
            # El traceback entero, al log del servidor. Ni una línea a la respuesta.
            logger.exception("Error inesperado en %s %s", scope["method"], scope["path"])
            if response_started:
                # Ya salió la cabecera de otra respuesta: no se puede cambiar por un 500.
                raise
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": GENERIC_ERROR}
            )
            await response(scope, receive, send)
