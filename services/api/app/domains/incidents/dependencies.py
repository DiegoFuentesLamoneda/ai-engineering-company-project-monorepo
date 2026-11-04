"""Dependencias del dominio de incidencias."""

from fastapi import Request

from .service import ResultsStore


def get_results_store(request: Request) -> ResultsStore:
    """El almacén del último análisis. Uno por app: cada app de pruebas tiene el suyo."""
    return request.app.state.incident_results
