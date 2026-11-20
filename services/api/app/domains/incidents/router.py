"""Rutas HTTP del dominio de incidencias: el analizador de CSV y el gestor.

El router no calcula nada: recibe la petición, llama al `service` y traduce
cada error a su código HTTP. Todos los errores salen con la misma forma,
`{"detail": "..."}`. Todas las rutas piden token: sin él, 401.

Las rutas del gestor usan `IncidentManagerRoute`: si la petición no valida,
responden 400 con el campo que falla (`validation_errors.py`), no el 422 de
FastAPI que siguen dando las del analizador.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from incident_analysis import (
    Branch,
    FileEncodingError,
    IncidentCategory,
    IncidentFileError,
    IncidentOrigin,
    IncidentStatus,
)

from ...config import Settings
from ...dependencies import get_settings
from ...schemas import ErrorResponse
from ..auth.dependencies import UNAUTHORIZED, get_current_user
from . import service
from .database import IncidentRepository
from .dependencies import get_incident_repository, get_results_store
from .exceptions import (
    FileTooLargeError,
    IncidentNotFoundError,
    InvalidTransitionError,
    NoAnalysisYetError,
    StatusChangedError,
    UnsupportedFileTypeError,
)
from .schemas import (
    AnalysisResponse,
    Incident,
    IncidentCreate,
    IncidentSummary,
    StatusUpdate,
    ValidationErrorResponse,
)
from .service import ResultsStore
from .validation_errors import IncidentManagerRoute

# El candado, una vez para todo el router: cada ruta de aquí pide token, y
# una ruta nueva nace protegida sin acordarse de nada. Las rutas no usan el
# usuario, así que va en `dependencies` y no como parámetro.
router = APIRouter(
    prefix="/api/incidents",
    tags=["incidents"],
    dependencies=[Depends(get_current_user)],
    responses=UNAUTHORIZED,
)


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analizar un CSV de tickets de soporte",
    responses={
        400: {"model": ErrorResponse, "description": "Vacío, solo cabecera o faltan columnas"},
        413: {"model": ErrorResponse, "description": "Supera el tamaño máximo"},
        415: {"model": ErrorResponse, "description": "No es un .csv o no está en UTF-8"},
    },
)
def analyze(
    file: Annotated[UploadFile, File(description="Exportación CSV del helpdesk")],
    settings: Annotated[Settings, Depends(get_settings)],
    store: Annotated[ResultsStore, Depends(get_results_store)],
) -> dict[str, Any]:
    # `def` y no `async def`: el análisis es cálculo y lectura bloqueante.
    # FastAPI ejecuta las rutas síncronas en un pool de hilos, así que un
    # fichero grande no congela al resto de peticiones.
    try:
        result = service.analyze_upload(
            file.file,
            filename=file.filename,
            size=file.size,
            max_bytes=settings.max_upload_bytes,
            store=store,
        )
    except UnsupportedFileTypeError as error:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(error)) from error
    except FileTooLargeError as error:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(error)) from error
    except FileEncodingError as error:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(error)) from error
    except IncidentFileError as error:
        # Vacío, solo cabecera o columnas que faltan: la petición está bien
        # formada, pero el contenido no se puede analizar.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return result.to_dict()


@router.get(
    "/results/export",
    summary="Descargar el último análisis como CSV",
    response_class=Response,
    responses={
        200: {"content": {"text/csv": {}}, "description": "Una métrica por fila"},
        404: {"model": ErrorResponse, "description": "Aún no se ha analizado nada"},
    },
)
def export_results(store: Annotated[ResultsStore, Depends(get_results_store)]) -> Response:
    try:
        csv_text = service.export_last(store)
    except NoAnalysisYetError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            # attachment: el navegador lo descarga en vez de mostrarlo.
            "Content-Disposition": f'attachment; filename="{service.EXPORT_FILENAME}"',
            # "El último" cambia con cada análisis: que nadie lo guarde en caché.
            "Cache-Control": "no-store",
        },
    )


# --- Gestor de incidencias ----------------------------------------------------

# Un router aparte, con el mismo prefijo y el mismo candado, por
# `route_class`: solo sus rutas cambian el 422 por el 400. `main.py` lo
# incluye después de `router`.
manager = APIRouter(
    prefix="/api/incidents",
    tags=["incidents"],
    dependencies=[Depends(get_current_user)],
    route_class=IncidentManagerRoute,
    responses={
        **UNAUTHORIZED,
        400: {"model": ValidationErrorResponse, "description": "Algún campo no es válido"},
    },
)

Repository = Annotated[IncidentRepository, Depends(get_incident_repository)]

NOT_FOUND = {404: {"model": ErrorResponse, "description": "No existe ninguna incidencia con ese ID"}}


@manager.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Incident,
    summary="Registrar una incidencia",
)
def create_incident(data: IncidentCreate, repo: Repository, response: Response) -> Incident:
    incident = service.create_incident(repo, data)
    # 201 + Location: la respuesta dice dónde vive el recurso recién creado.
    response.headers["Location"] = f"{manager.prefix}/{incident.id}"
    return incident


@manager.get("", response_model=list[Incident], summary="Listar incidencias, con filtros opcionales")
def list_incidents(
    repo: Repository,
    # alias: en la URL es `?status=`, pero aquí `status` taparía el módulo de FastAPI.
    status_filter: Annotated[
        IncidentStatus | None, Query(alias="status", description="Solo las de este estado")
    ] = None,
    origin: Annotated[IncidentOrigin | None, Query(description="Solo las de este origen")] = None,
    branch: Annotated[Branch | None, Query(description="Solo las de esta sede")] = None,
    category: Annotated[
        IncidentCategory | None,
        Query(description="Solo las de esta categoría; `sla_breach` para las críticas"),
    ] = None,
) -> list[Incident]:
    return service.list_incidents(
        repo, status=status_filter, origin=origin, branch=branch, category=category
    )


# Antes de `/{incident_id}`: FastAPI prueba las rutas en orden y, si no,
# "summary" llegaría como un ID (y daría 400 por no ser un UUID).
@manager.get(
    "/summary", response_model=IncidentSummary, summary="Totales por estado, categoría, origen y sede"
)
def summary(repo: Repository) -> IncidentSummary:
    return service.summarize(repo)


@manager.get(
    "/{incident_id}", response_model=Incident, summary="Consultar una incidencia", responses=NOT_FOUND
)
def get_incident(incident_id: UUID, repo: Repository) -> Incident:
    try:
        return service.get_incident(repo, incident_id)
    except IncidentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@manager.patch(
    "/{incident_id}/status",
    response_model=Incident,
    summary="Cambiar el estado de una incidencia",
    responses={
        **NOT_FOUND,
        409: {
            "model": ErrorResponse,
            "description": "El ciclo de vida no permite el cambio, o alguien se adelantó",
        },
    },
)
def change_status(incident_id: UUID, data: StatusUpdate, repo: Repository) -> Incident:
    try:
        return service.change_status(repo, incident_id, data.status)
    except IncidentNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except (InvalidTransitionError, StatusChangedError) as error:
        # 409 y no 400: la petición está bien formada; lo que choca es el
        # estado actual de la incidencia. Lo mismo que hace proveedores.
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

