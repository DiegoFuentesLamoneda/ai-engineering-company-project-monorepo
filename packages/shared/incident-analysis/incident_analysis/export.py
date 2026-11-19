"""Exportación del análisis a CSV: una métrica por fila.

Roberto pega este fichero en la plantilla del informe para clientes, así que
el formato es estable: tres columnas (`section`, `metric`, `value`) y siempre
las mismas filas en el mismo orden, también las que valen 0. Lo usan el script
(results.csv) y la API (GET /api/incidents/results/export): el mismo análisis
produce byte a byte el mismo fichero en los dos sitios.
"""

from __future__ import annotations

import csv
import io
from typing import TextIO

from .analysis import AnalysisResult

EXPORT_COLUMNS = ("section", "metric", "value")

MetricRow = tuple[str, str, int | float | str]


def metric_rows(result: AnalysisResult) -> list[MetricRow]:
    """Las métricas del análisis, aplanadas en filas (sección, métrica, valor)."""
    data = result.to_dict()
    rows: list[MetricRow] = [
        ("summary", "total_records", data["total_records"]),
        ("summary", "valid_records", data["valid_records"]),
        ("summary", "invalid_records", data["invalid_records"]),
    ]
    rows += [("invalid_by_rule", r["rule"], r["count"]) for r in data["invalid_by_rule"]]
    rows += [("category_count", c["category"], c["count"]) for c in data["by_category"]]
    rows += [("category_pct", c["category"], c["percentage"]) for c in data["by_category"]]
    rows += [("status_count", s["status"], s["count"]) for s in data["by_status"]]
    rows += [("status_pct", s["status"], s["percentage"]) for s in data["by_status"]]

    satisfaction = data["satisfaction"]
    average = satisfaction["average_score"]
    rows += [
        ("satisfaction", "closed_records", satisfaction["closed_records"]),
        ("satisfaction", "scored_records", satisfaction["scored_records"]),
        # Vacío y no 0 cuando no hay puntuaciones: 0 sería una media falsa.
        ("satisfaction", "average_score", "" if average is None else f"{average:.2f}"),
    ]
    rows += [
        ("score_distribution", f"score_{d['score']}", d["count"])
        for d in satisfaction["distribution"]
    ]
    return rows


def write_results_csv(result: AnalysisResult, stream: TextIO) -> int:
    """Escribe el CSV de resultados en `stream`. Devuelve cuántas métricas escribió."""
    rows = metric_rows(result)
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(rows)
    return len(rows)


def results_csv_text(result: AnalysisResult) -> str:
    """El mismo CSV como texto, para devolverlo desde la API."""
    buffer = io.StringIO()
    write_results_csv(result, buffer)
    return buffer.getvalue()
