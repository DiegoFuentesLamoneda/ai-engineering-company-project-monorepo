"""Rutas HTTP del analizador de incidencias.

El router no calcula nada: recibe la subida, llama al `service` y traduce
cada error a su código HTTP. Todos los errores salen con la misma forma,
`{"detail": "..."}`, la que ya usa FastAPI para sus 422.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from incident_analysis import FileEncodingError, IncidentFileError

from ...config import Settings
from ...dependencies import get_settings
from . import service
from .dependencies import get_results_store
from .exceptions import FileTooLargeError, NoAnalysisYetError, UnsupportedFileTypeError
from .schemas import AnalysisResponse, ErrorResponse
from .service import ResultsStore

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


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
