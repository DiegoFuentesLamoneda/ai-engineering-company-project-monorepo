"""Reglas del análisis de ficheros subidos. No importa `fastapi`.

La validación y las métricas no se calculan aquí: son las del paquete
`incident_analysis`, las mismas que usa `scripts/analyze.py`. Este módulo solo
añade lo que es propio de recibir el fichero por la red (extensión, tamaño,
bytes → texto) y el recuerdo del último análisis para poder exportarlo.
"""

from __future__ import annotations

import io
import threading
from typing import BinaryIO

from incident_analysis import AnalysisResult, analyze_csv, results_csv_text

from .exceptions import FileTooLargeError, NoAnalysisYetError, UnsupportedFileTypeError

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
