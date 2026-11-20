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
"""

from __future__ import annotations

import logging

from fastapi import status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("nexova.errors")

GENERIC_ERROR = "Ha ocurrido un error inesperado en el servidor. Inténtalo de nuevo en unos minutos."


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
