"""Validación de un registro (una fila del CSV) contra las reglas del briefing.

Función pura: recibe una fila, devuelve los códigos de las reglas que rompe.
No imprime nada ni guarda la fila. Es lo que garantiza que el email del
cliente entra aquí para comprobar que tiene "@" y no sale por ningún sitio.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime

from .schema import (
    AGENT_ID_PATTERN,
    CATEGORIES,
    CLOSED_STATUS,
    DATE_FORMAT,
    DESCRIPTION_MIN_LENGTH,
    SCORE_MAX,
    SCORE_MIN,
    STATUSES,
    TICKET_ID_PATTERN,
)

_TICKET_ID_RE = re.compile(TICKET_ID_PATTERN)
_AGENT_ID_RE = re.compile(AGENT_ID_PATTERN)
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def field(row: Mapping[str, str | None], name: str) -> str:
    """Valor de un campo sin espacios alrededor.

    `csv.DictReader` rellena con None las columnas que faltan en una fila
    corta; aquí None y "" significan lo mismo: el campo está vacío.
    """
    value = row.get(name)
    return value.strip() if value else ""


def parse_score(raw: str) -> int | None:
    """Convierte la puntuación a entero. None si no es un entero válido.

    "4" -> 4. "4.0", "cuatro" o "" -> None. No se redondea nada: el briefing
    pide un entero y un decimal es un dato mal registrado.
    """
    try:
        return int(raw)
    except ValueError:
        return None


def _is_valid_date(raw: str) -> bool:
    # La expresión regular fuerza YYYY-MM-DD con ceros (strptime acepta
    # "2024-1-5"); strptime rechaza fechas imposibles como 2024-02-30.
    if not _DATE_RE.fullmatch(raw):
        return False
    try:
        datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        return False
    return True


def validate_record(row: Mapping[str, str | None]) -> list[str]:
    """Códigos de las reglas que rompe la fila. Lista vacía = registro válido."""
    errors: list[str] = []

    if not _TICKET_ID_RE.fullmatch(field(row, "ticket_id")):
        errors.append("invalid_ticket_id")

    if not _is_valid_date(field(row, "date")):
        errors.append("invalid_date")

    if not field(row, "client_company"):
        errors.append("missing_client_company")

    # Comparación exacta: "technical" en minúsculas no es una categoría válida.
    if field(row, "category") not in CATEGORIES:
        errors.append("invalid_category")

    if len(field(row, "description")) < DESCRIPTION_MIN_LENGTH:
        errors.append("invalid_description")

    if not _AGENT_ID_RE.fullmatch(field(row, "agent_id")):
        errors.append("invalid_agent_id")

    status = field(row, "status")
    if status not in STATUSES:
        errors.append("invalid_status")

    # Regla literal del briefing: vacío o sin "@". No se valida más a fondo a
    # propósito: el criterio lo fija el negocio, no el desarrollador.
    if "@" not in field(row, "customer_email"):
        errors.append("invalid_email")

    raw_score = field(row, "satisfaction_score")
    if raw_score:
        score = parse_score(raw_score)
        if score is None or not SCORE_MIN <= score <= SCORE_MAX:
            errors.append("score_out_of_range")
    elif status == CLOSED_STATUS:
        errors.append("closed_without_score")

    return errors
