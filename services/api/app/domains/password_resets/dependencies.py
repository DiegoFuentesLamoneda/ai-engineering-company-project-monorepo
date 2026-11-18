"""Dependencias del restablecimiento de contraseña."""

from fastapi import Request

from ...mailer import Mailer
from .database import PasswordResetRepository


def get_password_reset_repository(request: Request) -> PasswordResetRepository:
    """El repositorio que abrió la app al arrancar (ver `main.lifespan`)."""
    return request.app.state.password_resets


def get_mailer(request: Request) -> Mailer:
    """Resend o el log, según la configuración (ver `main.lifespan`)."""
    return request.app.state.mailer
