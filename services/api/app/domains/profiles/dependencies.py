"""Dependencias del dominio de perfiles."""

from fastapi import Request

from .database import ProfileRepository


def get_profile_repository(request: Request) -> ProfileRepository:
    """El repositorio que abrió la app al arrancar (ver `main.lifespan`)."""
    return request.app.state.profiles
