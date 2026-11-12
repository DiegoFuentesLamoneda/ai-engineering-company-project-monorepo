"""Cliente HTTP mínimo para las pruebas, solo con la biblioteca estándar.

Habla con la app como lo hace uvicorn: por ASGI, el protocolo entre el
servidor y la app. La petición recorre la app entera (CORS, rutas,
dependencias como `get_current_user`, validación y `response_model`), así
que se prueban los códigos HTTP de verdad, sin abrir un puerto.

Hace lo mismo que el `TestClient` de FastAPI, que necesita la dependencia
`httpx`. No se usa el `lifespan`: cada prueba pone sus repositorios en
`app.state`.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass
class Response:
    status_code: int
    headers: dict[str, str]
    body: bytes

    def json(self):
        return json.loads(self.body)


def request(app, method: str, path: str, *, json_body=None, form=None, token: str | None = None) -> Response:
    headers: list[tuple[bytes, bytes]] = []
    body = b""
    if json_body is not None:
        body = json.dumps(json_body).encode()
        headers.append((b"content-type", b"application/json"))
    elif form is not None:
        body = urlencode(form).encode()
        headers.append((b"content-type", b"application/x-www-form-urlencoded"))
    if token is not None:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    headers.append((b"content-length", str(len(body)).encode()))

    path, _, query = path.partition("?")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query.encode(),
        "root_path": "",
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return asyncio.run(_call(app, scope, body))


async def _call(app, scope: dict, body: bytes) -> Response:
    messages: list[dict] = []
    done = asyncio.Event()
    body_sent = False

    async def receive() -> dict:
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        # El "cliente" no se desconecta hasta tener la respuesta entera.
        await done.wait()
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        messages.append(message)
        if message["type"] == "http.response.body" and not message.get("more_body", False):
            done.set()

    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    return Response(
        status_code=start["status"],
        headers={k.decode().lower(): v.decode() for k, v in start.get("headers", [])},
        body=b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body"),
    )
