"""Reglas del dominio de incidencias. No importa `fastapi`. Dos partes:

1. **El análisis de ficheros subidos.** La validación y las métricas no se
   calculan aquí: son las del paquete `incident_analysis`, las mismas que usa
   `scripts/analyze.py`. Este módulo solo añade lo que es propio de recibir el
   fichero por la red (extensión, tamaño, bytes → texto) y el recuerdo del
   último análisis para poder exportarlo.
2. **El gestor de incidencias**: alta, consulta, cambio de estado y resumen.
   El ciclo de vida (`can_transition`) también viene del paquete compartido.
"""

from __future__ import annotations

import io
import threading
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from typing import BinaryIO
from uuid import UUID, uuid4

from incident_analysis import (
    ALLOWED_TRANSITIONS,
    AnalysisResult,
    Branch,
    IncidentCategory,
    IncidentOrigin,
    IncidentStatus,
    analyze_csv,
    can_transition,
    results_csv_text,
)

from .database import IncidentRepository
from .exceptions import (
    FileTooLargeError,
    IncidentNotFoundError,
    InvalidTransitionError,
    NoAnalysisYetError,
    StatusChangedError,
    UnsupportedFileTypeError,
)
from .schemas import Incident, IncidentCreate, IncidentSummary

# --- Análisis de ficheros -----------------------------------------------------

ALLOWED_EXTENSION = ".csv"
EXPORT_FILENAME = "results.csv"


class ResultsStore:
    """El último análisis, en la memoria del proceso.

    Lo exige el contrato: `GET /results/export` no recibe qué análisis
    exportar. Consecuencias asumidas, documentadas en el README del servicio:
    se pierde al reiniciar, es común a todos los usuarios y no se comparte
    entre procesos. Solo guarda números agregados, nunca datos de las filas.
    """

    def __init__(self) -> None:
        # Las rutas síncronas de FastAPI corren en un pool de hilos: dos
        # análisis simultáneos podrían escribir a la vez.
        self._lock = threading.Lock()
        self._last: AnalysisResult | None = None

    def save(self, result: AnalysisResult) -> None:
        with self._lock:
            self._last = result

    def last(self) -> AnalysisResult | None:
        with self._lock:
            return self._last


def check_upload(filename: str | None, size: int | None, max_bytes: int) -> None:
    """Rechaza lo que no merece la pena leer: otra extensión o demasiado grande.

    Se decide por la extensión y no por el Content-Type, porque el navegador
    lo deduce del sistema operativo: en un Windows con Excel, un .csv viaja
    como `application/vnd.ms-excel`. La prueba de verdad es el contenido, que
    `analyze_csv` valida después (UTF-8 y columnas obligatorias).
    """
    if not filename or not filename.lower().endswith(ALLOWED_EXTENSION):
        raise UnsupportedFileTypeError()
    if size is not None and size > max_bytes:
        raise FileTooLargeError(max_bytes // (1024 * 1024))


def analyze_upload(
    stream: BinaryIO,
    *,
    filename: str | None,
    size: int | None,
    max_bytes: int,
    store: ResultsStore,
) -> AnalysisResult:
    """Analiza el CSV subido y lo recuerda como último análisis.

    Lanza `IncidentUploadError` si la subida no es aceptable e
    `IncidentFileError` (del paquete) si el contenido no lo es.
    """
    check_upload(filename, size, max_bytes)

    # La subida llega en bytes; el análisis lee texto línea a línea, sin cargar
    # el fichero entero. utf-8-sig acepta el BOM que añade Excel.
    text = io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")
    try:
        result = analyze_csv(text)
    finally:
        # Suelta el fichero sin cerrarlo: lo cierra FastAPI al acabar la petición.
        text.detach()

    store.save(result)
    return result


def export_last(store: ResultsStore) -> str:
    """El CSV de resultados del último análisis, idéntico al del script."""
    result = store.last()
    if result is None:
        raise NoAnalysisYetError()
    return results_csv_text(result)


# --- Gestor de incidencias ----------------------------------------------------


def _now() -> datetime:
    return datetime.now(UTC)


def create_incident(
    repo: IncidentRepository,
    data: IncidentCreate,
    *,
    now: Callable[[], datetime] = _now,
    new_id: Callable[[], UUID] = uuid4,
) -> Incident:
    """Registra una incidencia nueva. Nace `open` y con las dos fechas iguales.

    `now` y `new_id` se pueden sustituir en las pruebas para fijar el reloj y el ID.
    """
    created_at = now()
    incident = Incident(
        id=new_id(),
        status=IncidentStatus.OPEN,
        created_at=created_at,
        updated_at=created_at,
        **data.model_dump(),
    )
    return repo.insert(incident)


def list_incidents(
    repo: IncidentRepository,
    *,
    status: IncidentStatus | None = None,
    origin: IncidentOrigin | None = None,
    branch: Branch | None = None,
    category: IncidentCategory | None = None,
) -> list[Incident]:
    """Las incidencias que cumplen los filtros, la más reciente primero. Vacía si no hay."""
    return repo.list(status=status, origin=origin, branch=branch, category=category)


def get_incident(repo: IncidentRepository, incident_id: UUID) -> Incident:
    incident = repo.get(incident_id)
    if incident is None:
        raise IncidentNotFoundError(incident_id)
    return incident


def change_status(
    repo: IncidentRepository,
    incident_id: UUID,
    target: IncidentStatus,
    *,
    now: Callable[[], datetime] = _now,
) -> Incident:
    """Mueve la incidencia por su ciclo de vida.

    Lanza `IncidentNotFoundError` si no existe, `InvalidTransitionError` si
    el ciclo no permite el cambio y `StatusChangedError` si otra petición la
    cambió entre la lectura y la escritura (ver `IncidentRepository.update_status`).
    """
    current = get_incident(repo, incident_id)
    if not can_transition(current.status, target):
        allowed = [status.value for status in IncidentStatus if status in ALLOWED_TRANSITIONS[current.status]]
        raise InvalidTransitionError(current.status.value, target.value, allowed)

    updated = repo.update_status(incident_id, expected=current.status, target=target, updated_at=now())
    if updated is not None:
        return updated
    # None: o la han borrado o ya no está en el estado que leímos.
    if repo.get(incident_id) is None:
        raise IncidentNotFoundError(incident_id)
    raise StatusChangedError()


def summarize(repo: IncidentRepository) -> IncidentSummary:
    """Totales por estado, categoría, origen y sede. Con la base vacía, todo a 0."""
    incidents = repo.list()

    def breakdown(values: type[StrEnum], field: str) -> dict:
        counts = Counter(getattr(incident, field) for incident in incidents)
        # Todos los valores del enum, en su orden, aunque no aparezcan.
        return {value: counts[value] for value in values}

    return IncidentSummary(
        total=len(incidents),
        by_status=breakdown(IncidentStatus, "status"),
        by_category=breakdown(IncidentCategory, "category"),
        by_origin=breakdown(IncidentOrigin, "origin"),
        by_branch=breakdown(Branch, "branch"),
    )
