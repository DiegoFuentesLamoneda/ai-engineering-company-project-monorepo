"""Punto de entrada de la API de Nexova: compone la app y nada más.

Arranque, desde services/api:
    uv run --env-file .env uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import ExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, load_settings
from .domains.auth.router import router as auth_router
from .domains.incidents.database import IncidentRepository
from .domains.incidents.router import router as incidents_router
from .domains.incidents.service import ResultsStore
from .domains.password_resets.database import PasswordResetRepository
from .domains.password_resets.router import router as password_resets_router
from .domains.profiles.database import ProfileRepository
from .domains.profiles.router import router as profiles_router
from .domains.suppliers.database import SupplierRepository
from .domains.suppliers.router import router as suppliers_router
from .domains.users.database import UserRepository
from .domains.users.router import router as users_router
from .mailer import build_mailer


def configure_logging() -> None:
    """Que los mensajes INFO de la API (`nexova.*`) salgan en la consola.

    Uvicorn solo configura sus propios loggers. Sin esto, los de la API se
    quedan en el nivel por defecto de Python (WARNING): se ve cuándo falla un
    envío de email, pero no cuándo sale bien, y al diagnosticar «no me llega
    el correo» no hay forma de saber si llegó a salir.
    """
    logger = logging.getLogger("nexova")
    logger.setLevel(logging.INFO)
    if not logger.handlers:  # --reload vuelve a importar: un solo handler
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)-9s %(name)s - %(message)s"))
        logger.addHandler(handler)
        # Ya escribe aquí; sin esto, un handler en la raíz lo duplicaría.
        logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Comprueba el secreto y abre las bases de datos al arrancar; las cierra al parar.

    Se hace aquí y no al importar el módulo: crear la app (en las pruebas,
    o para leer el OpenAPI) no necesita secreto ni toca el fichero de TinyDB.
    Arrancar el servidor sí: sin secreto no hay forma de firmar un token.
    """
    settings: Settings = app.state.settings
    settings.require_jwt_secret()
    configure_logging()
    # ExitStack: si falla la apertura de una, se cierran las ya abiertas.
    with ExitStack() as stack:
        app.state.suppliers = stack.enter_context(SupplierRepository(settings.suppliers_db_path))
        app.state.users = stack.enter_context(UserRepository(settings.users_db_path))
        app.state.profiles = stack.enter_context(ProfileRepository(settings.profiles_db_path))
        app.state.incidents = stack.enter_context(IncidentRepository(settings.incidents_db_path))
        app.state.password_resets = stack.enter_context(
            PasswordResetRepository(settings.password_resets_db_path)
        )
        # Sin API key de Resend avisa en el log y escribe ahí los emails.
        app.state.mailer = build_mailer(settings)
        yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea la app. Las pruebas pasan su propia configuración."""
    settings = settings or load_settings()

    app = FastAPI(
        title="Nexova API",
        version="0.1.0",
        description="Backend de Nexova Solutions. Un monolito modular por dominios.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.incident_results = ResultsStore()

    # El backoffice corre en otro origen (:3000): sin esto, el navegador
    # bloquea las respuestas. Lista explícita, nunca '*'.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        # Authorization: el token viaja en `Authorization: Bearer <token>`.
        allow_headers=["Content-Type", "Authorization"],
        # Para que el frontend pueda leer el nombre del fichero descargado.
        expose_headers=["Content-Disposition"],
    )

    app.include_router(auth_router)
    app.include_router(password_resets_router)
    app.include_router(users_router)
    app.include_router(profiles_router)
    app.include_router(incidents_router)
    app.include_router(suppliers_router)
    return app


# Se crea al importar el módulo: una configuración inválida impide arrancar.
app = create_app()
