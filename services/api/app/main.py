"""Punto de entrada de la API de Nexova: compone la app y nada más.

Arranque, desde services/api:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, load_settings
from .domains.incidents.router import router as incidents_router
from .domains.incidents.service import ResultsStore


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea la app. Las pruebas pasan su propia configuración."""
    settings = settings or load_settings()

    app = FastAPI(
        title="Nexova API",
        version="0.1.0",
        description="Backend de Nexova Solutions. Un monolito modular por dominios.",
    )
    app.state.settings = settings
    app.state.incident_results = ResultsStore()

    # El backoffice corre en otro origen (:3000): sin esto, el navegador
    # bloquea las respuestas. Lista explícita, nunca '*'.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        # Para que el frontend pueda leer el nombre del fichero descargado.
        expose_headers=["Content-Disposition"],
    )

    app.include_router(incidents_router)
    return app


# Se crea al importar el módulo: una configuración inválida impide arrancar.
app = create_app()
