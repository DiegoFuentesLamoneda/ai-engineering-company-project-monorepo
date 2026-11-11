"""Utilidades de los tests: filas y ficheros CSV sintéticos.

Los emails de prueba usan example.com, el dominio reservado para ejemplos:
nunca un dato real en un test.
"""

from __future__ import annotations

import csv
import io

from incident_analysis.schema import COLUMNS

VALID_ROW: dict[str, str] = {
    "ticket_id": "NXV-000001",
    "date": "2024-01-18",
    "client_company": "FinServ Group",
    "category": "ACCESS",
    "description": "Role permissions not updated",
    "agent_id": "AGT-08",
    "status": "CLOSED",
    "customer_email": "persona@example.com",
    "satisfaction_score": "5",
}


def row(**changes: str) -> dict[str, str]:
    """Una fila válida con los cambios indicados."""
    return {**VALID_ROW, **changes}


def csv_lines(*rows: dict[str, str], columns: tuple[str, ...] = COLUMNS) -> list[str]:
    """Un CSV completo (cabecera + filas) como lista de líneas, igual que un fichero abierto."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for item in rows:
        writer.writerow({key: item.get(key, "") for key in columns})
    return buffer.getvalue().splitlines(keepends=True)
