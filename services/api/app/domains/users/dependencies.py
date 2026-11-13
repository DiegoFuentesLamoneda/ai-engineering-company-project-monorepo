"""Dependencias del dominio de usuarios."""

from fastapi import Request

from .database import UserRepository


def get_user_repository(request: Request) -> UserRepository:
    """El repositorio que abrió la app al arrancar (ver `main.lifespan`)."""
    return request.app.state.users
