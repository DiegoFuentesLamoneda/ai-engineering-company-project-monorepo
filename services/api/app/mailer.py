"""Envío de emails transaccionales con Resend (AUTH-03).

Es el único módulo que habla con el servicio de correo. El resto de la API
construye un `EmailMessage` y llama a `mailer.send(...)` sin saber quién lo
entrega.

Dos implementaciones:

- `ResendMailer`: envía de verdad, con la API key de `NEXOVA_API_RESEND_API_KEY`.
- `LogMailer`: sin clave, escribe el email en el log de la API. Sirve para
  desarrollar y para las pruebas sin cuenta de Resend.

Va sobre `urllib` de la biblioteca estándar y no sobre el SDK de Resend: es
una sola llamada HTTP y no compensa añadir una dependencia.

Prueba de envío real, desde services/api (la persona lanza el comando y el
email solo llega a la dirección con la que se creó la cuenta de Resend):
    uv run --env-file .env python -m app.mailer tu-email@ejemplo.com
"""

from __future__ import annotations

import json
import logging
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import SecretStr

from .config import Settings, load_settings

logger = logging.getLogger("nexova.mailer")

RESEND_ENDPOINT = "https://api.resend.com/emails"
# Resend está detrás de Cloudflare, que bloquea el User-Agent por defecto de
# urllib ("Python-urllib/3.x") con un 403. Con uno propio, pasa.
USER_AGENT = "nexova-api/0.1"
TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class EmailMessage:
    """Un email listo para enviar. `text` es la versión sin HTML."""

    to: str
    subject: str
    html: str
    text: str


class Mailer(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class EmailDeliveryError(RuntimeError):
    """El servicio de correo no aceptó el email.

    El mensaje lleva el código HTTP y lo que contestó Resend, nunca la API key.
    """


def mask_email(address: str) -> str:
    """'diego@nexova.es' → 'd***@nexova.es'. Para los logs: dan pista sin exponer el email."""
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


Opener = Callable[..., Any]


class ResendMailer:
    def __init__(
        self,
        api_key: SecretStr,
        sender: str,
        opener: Opener = urllib.request.urlopen,
    ) -> None:
        # `opener` se cambia en las pruebas por uno falso: así se comprueba
        # qué se envía sin salir a internet.
        self._api_key = api_key
        self._sender = sender
        self._opener = opener

    def __repr__(self) -> str:
        return f"ResendMailer(sender={self._sender!r})"

    def send(self, message: EmailMessage) -> None:
        body = json.dumps(
            {
                "from": self._sender,
                "to": [message.to],
                "subject": message.subject,
                "html": message.html,
                "text": message.text,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            RESEND_ENDPOINT,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with self._opener(request, timeout=TIMEOUT_SECONDS) as response:
                response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:300]
            raise EmailDeliveryError(f"Resend respondió {error.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as error:
            raise EmailDeliveryError(f"No se pudo contactar con Resend: {error}") from None
        logger.info("Email enviado a %s: %s", mask_email(message.to), message.subject)


class LogMailer:
    """Sin API key: el email no sale, se escribe en el log.

    En desarrollo, el enlace de restablecimiento se copia de la consola.
    Por eso se escribe el texto entero: es la única forma de recibirlo.
    """

    def send(self, message: EmailMessage) -> None:
        logger.warning(
            "Sin NEXOVA_API_RESEND_API_KEY: el email a %s no se envía.\nAsunto: %s\n\n%s",
            mask_email(message.to),
            message.subject,
            message.text,
        )


def build_mailer(settings: Settings) -> Mailer:
    """Resend si hay clave; si no, el log. La API arranca en los dos casos."""
    if settings.resend_api_key is None:
        logger.warning(
            "NEXOVA_API_RESEND_API_KEY no está configurada: los emails se escribirán en el log."
        )
        return LogMailer()
    return ResendMailer(settings.resend_api_key, settings.email_from)


def _main(argv: list[str]) -> int:
    """Envía un email de prueba con la configuración de `.env`."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(argv) != 1:
        print("Uso: uv run --env-file .env python -m app.mailer <email-destino>")
        return 2
    mailer = build_mailer(load_settings())
    message = EmailMessage(
        to=argv[0],
        subject="Prueba de envío — Nexova Solutions",
        html="<p>Si lees esto, la API de Nexova ya envía emails con Resend.</p>",
        text="Si lees esto, la API de Nexova ya envía emails con Resend.",
    )
    try:
        mailer.send(message)
    except EmailDeliveryError as error:
        print(f"Error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
