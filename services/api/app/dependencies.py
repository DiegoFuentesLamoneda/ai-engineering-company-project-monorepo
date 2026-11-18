"""Dependencias transversales: lo que cualquier dominio puede pedir con Depends."""

from fastapi import Request

from .config import Settings


def get_settings(request: Request) -> Settings:
    """La configuración con la que arrancó la app (ver `main.create_app`)."""
    return request.app.state.settings
