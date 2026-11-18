"""Contrato de salida de la API de incidencias.

Reproduce la forma de `AnalysisResult.to_dict()`. Declararlo con Pydantic
tiene dos efectos: FastAPI comprueba que la respuesta cumple el contrato, y
lo publica en el OpenAPI (/docs), que es lo que lee el backoffice para saber
qué recibe. Los valores son códigos (`TECHNICAL`, `CLOSED`…): la traducción a
texto de interfaz la hace cada aplicación, no la API.
"""

from __future__ import annotations

from pydantic import BaseModel


class RuleCount(BaseModel):
    rule: str
    label: str
    count: int


class CategoryCount(BaseModel):
    category: str
    count: int
    percentage: float


class StatusCount(BaseModel):
    status: str
    count: int
    percentage: float


class ScoreCount(BaseModel):
    score: int
    label: str
    count: int


class Satisfaction(BaseModel):
    closed_records: int
    scored_records: int
    average_score: float | None
    distribution: list[ScoreCount]


class InvalidSample(BaseModel):
    line: int
    # Vacío si el ID del fichero no tenía el formato NXV-XXXXXX.
    ticket_id: str
    rules: list[str]


class AnalysisResponse(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    invalid_by_rule: list[RuleCount]
    by_category: list[CategoryCount]
    by_status: list[StatusCount]
    satisfaction: Satisfaction
    # Como mucho 50 filas: suficiente para localizar el problema en el origen.
    invalid_samples: list[InvalidSample]


class ErrorResponse(BaseModel):
    detail: str
