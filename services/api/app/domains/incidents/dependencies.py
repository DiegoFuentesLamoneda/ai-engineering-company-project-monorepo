"""Dependencias del dominio de incidencias."""

from fastapi import Request

from .database import IncidentRepository
from .service import ResultsStore


def get_results_store(request: Request) -> ResultsStore:
    """El almacén del último análisis. Uno por app: cada app de pruebas tiene el suyo."""
    return request.app.state.incident_results


def get_incident_repository(request: Request) -> IncidentRepository:
    """El repositorio del gestor que abrió la app al arrancar (ver `main.lifespan`)."""
    return request.app.state.incidents
