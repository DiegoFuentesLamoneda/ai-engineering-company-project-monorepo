"""Dependencias del restablecimiento de contraseña."""

from typing import Annotated

from fastapi import Depends, Request

from ...mailer import Mailer
from .database import PasswordResetRepository


def get_password_reset_repository(request: Request) -> PasswordResetRepository:
    """El repositorio que abrió la app al arrancar (ver `main.lifespan`)."""
    return request.app.state.password_resets


def get_mailer(request: Request) -> Mailer:
    """Resend o el log, según la configuración (ver `main.lifespan`)."""
    return request.app.state.mailer


def get_client_ip(request: Request) -> str | None:
    """La IP desde la que llega la petición, para la auditoría.

    Es la de quien abre la conexión con la API. Detrás de un proxy o un
    balanceador sería la suya, no la de la persona: ver "Limitaciones
    conocidas" en el README. No se lee `X-Forwarded-For` porque, sin un
    proxy de confianza delante, cualquiera puede escribir ahí lo que quiera.
    """
    return request.client.host if request.client else None


ClientIp = Annotated[str | None, Depends(get_client_ip)]
