"""Análisis de un fichero de tickets: validación + métricas, en una sola pasada.

El fichero se lee fila a fila (streaming). En memoria solo viven los
contadores y una muestra acotada de filas inválidas, así que el consumo es el
mismo con 100 filas que con el millón de la exportación de producción.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import (
    CATEGORIES,
    CLOSED_STATUS,
    COLUMNS,
    RULES,
    RULES_BY_CODE,
    SCORE_LABELS,
    SCORE_MAX,
    SCORE_MIN,
    STATUSES,
    TICKET_ID_PATTERN,
)
from .validation import field, parse_score, validate_record

# Cuántas filas inválidas se devuelven con su número de línea. Con un millón
# de registros podrían ser miles: la muestra sirve para ir a corregir el origen,
# los totales por regla son los que cuentan.
MAX_INVALID_SAMPLES = 50

_TICKET_ID_RE = re.compile(TICKET_ID_PATTERN)
_BOM = "﻿"


class IncidentFileError(ValueError):
    """El fichero entero no se puede analizar (no una fila suelta)."""


class EmptyFileError(IncidentFileError):
    pass


class MissingColumnsError(IncidentFileError):
    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(
            "Al fichero le faltan columnas obligatorias: " + ", ".join(missing) + "."
        )


class FileEncodingError(IncidentFileError):
    pass


@dataclass(frozen=True)
class InvalidRecord:
    """Una fila inválida, sin ningún dato personal.

    `line` es la línea física del fichero (la cabecera es la 1), para que
    quien corrija el origen la encuentre a la primera.
    """

    line: int
    ticket_id: str
    rules: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisResult:
    """Resultado del análisis. Solo números y códigos: ningún dato personal."""

    total_records: int
    valid_records: int
    invalid_records: int
    invalid_by_rule: dict[str, int]
    by_category: dict[str, int]
    by_status: dict[str, int]
    closed_records: int
    scored_closed_records: int
    average_score: float | None
    score_distribution: dict[int, int]
    invalid_samples: tuple[InvalidRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        """Versión serializable a JSON. Es la que devuelve la API."""
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "invalid_by_rule": [
                {"rule": code, "label": RULES_BY_CODE[code].label, "count": count}
                for code, count in self.invalid_by_rule.items()
            ],
            "by_category": [
                {
                    "category": category,
                    "count": count,
                    "percentage": percentage(count, self.valid_records),
                }
                for category, count in self.by_category.items()
            ],
            "by_status": [
                {
                    "status": status,
                    "count": count,
                    "percentage": percentage(count, self.valid_records),
                }
                for status, count in self.by_status.items()
            ],
            "satisfaction": {
                "closed_records": self.closed_records,
                "scored_records": self.scored_closed_records,
                "average_score": (
                    round(self.average_score, 2) if self.average_score is not None else None
                ),
                "distribution": [
                    {"score": score, "label": SCORE_LABELS[score], "count": count}
                    for score, count in self.score_distribution.items()
                ],
            },
            "invalid_samples": [
                {"line": s.line, "ticket_id": s.ticket_id, "rules": list(s.rules)}
                for s in self.invalid_samples
            ],
        }


def percentage(count: int, total: int) -> float:
    """Porcentaje con un decimal. 0.0 si no hay total (nunca divide por cero)."""
    return round(count * 100 / total, 1) if total else 0.0


def analyze_csv(lines: Iterable[str]) -> AnalysisResult:
    """Analiza un CSV ya abierto como texto (fichero, upload de la API, lista de líneas).

    Lanza IncidentFileError (o una subclase) si el fichero entero es
    inutilizable: vacío, sin las columnas obligatorias o con otra codificación.
    Las filas sueltas mal formadas no lanzan nada: se cuentan como inválidas.
    """
    reader = csv.DictReader(lines)

    try:
        header = reader.fieldnames
    except UnicodeDecodeError as exc:
        raise FileEncodingError(
            "El fichero no está en UTF-8. Expórtalo de nuevo como CSV UTF-8."
        ) from exc
    except csv.Error as exc:
        raise IncidentFileError(f"El fichero no tiene un formato CSV válido: {exc}.") from exc

    if not header:
        raise EmptyFileError("El fichero está vacío.")

    # Excel guarda el CSV con BOM y a veces con espacios en la cabecera: se
    # normalizan los nombres para no rechazar un fichero correcto por eso.
    reader.fieldnames = [name.lstrip(_BOM).strip() for name in header]
    missing = [column for column in COLUMNS if column not in reader.fieldnames]
    if missing:
        raise MissingColumnsError(missing)

    total = 0
    invalid = 0
    invalid_by_rule: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    scores: Counter[int] = Counter()
    closed = 0
    samples: list[InvalidRecord] = []

    try:
        for row in reader:
            total += 1
            errors = validate_record(row)

            if errors:
                invalid += 1
                invalid_by_rule.update(errors)
                if len(samples) < MAX_INVALID_SAMPLES:
                    ticket_id = field(row, "ticket_id")
                    samples.append(
                        InvalidRecord(
                            line=reader.line_num,
                            # Solo se devuelve el ID si tiene el formato esperado:
                            # un campo mal rellenado podría contener cualquier cosa.
                            ticket_id=ticket_id if _TICKET_ID_RE.fullmatch(ticket_id) else "",
                            rules=tuple(errors),
                        )
                    )
                continue

            # A partir de aquí la fila es válida: los valores ya están comprobados.
            by_category[field(row, "category")] += 1
            status = field(row, "status")
            by_status[status] += 1

            if status == CLOSED_STATUS:
                closed += 1
                score = parse_score(field(row, "satisfaction_score"))
                if score is not None:
                    scores[score] += 1
    except UnicodeDecodeError as exc:
        raise FileEncodingError(
            "El fichero no está en UTF-8. Expórtalo de nuevo como CSV UTF-8."
        ) from exc
    except csv.Error as exc:
        raise IncidentFileError(
            f"Formato CSV incorrecto cerca de la línea {reader.line_num}: {exc}."
        ) from exc

    if total == 0:
        raise EmptyFileError("El fichero solo tiene la cabecera: no hay registros que analizar.")

    scored = sum(scores.values())
    average = sum(score * count for score, count in scores.items()) / scored if scored else None

    return AnalysisResult(
        total_records=total,
        valid_records=total - invalid,
        invalid_records=invalid,
        # Todas las claves siempre presentes y en el orden del briefing, también
        # las que valen 0: un cero también es información.
        invalid_by_rule={rule.code: invalid_by_rule[rule.code] for rule in RULES},
        by_category={category: by_category[category] for category in CATEGORIES},
        by_status={status: by_status[status] for status in STATUSES},
        closed_records=closed,
        scored_closed_records=scored,
        average_score=average,
        score_distribution={s: scores[s] for s in range(SCORE_MIN, SCORE_MAX + 1)},
        invalid_samples=tuple(samples),
    )


def analyze_file(path: str | Path) -> AnalysisResult:
    """Abre el fichero y lo analiza. `utf-8-sig` acepta UTF-8 con o sin BOM."""
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return analyze_csv(handle)
