"""Modelos Pydantic del dominio de incidencias. Dos partes:

1. **El gestor de incidencias** (`Incident` y sus modelos de entrada). Es la
   puerta de entrada: todo lo que llega por la API pasa por aquí antes de
   tocar la base de datos. Los valores válidos no se escriben aquí: son los
   `StrEnum` del paquete compartido `incident_analysis`, los mismos que usa
   el seed (docs/contexts/proyectos/centralized-incident-manager.es.md).
2. **El análisis del CSV** (`AnalysisResponse`): reproduce la forma de
   `AnalysisResult.to_dict()`.

Declararlo con Pydantic tiene dos efectos: FastAPI comprueba que entrada y
salida cumplen el contrato, y lo publica en el OpenAPI (/docs), que es lo que
lee el backoffice para saber qué envía y qué recibe. Los valores son códigos
(`technical_failure`, `in_progress`…): la traducción a texto de interfaz la
hace cada aplicación, no la API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from incident_analysis import (
    TITLE_MAX_LENGTH,
    Branch,
    IncidentCategory,
    IncidentOrigin,
    IncidentStatus,
)
from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints, model_validator

# --- Gestor de incidencias --------------------------------------------------

# Límite técnico, no del briefing: que nadie pegue un log de 5 MB en el
# formulario. Las descripciones del CSV histórico no pasan de 60 caracteres.
DESCRIPTION_MAX_LENGTH = 2000

# Lo que escribe una persona: sin espacios sobrantes y no vacío ("   " no es un título).
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_MAX_LENGTH)]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=DESCRIPTION_MAX_LENGTH)
]

# Lo que se guarda: las mismas longitudes, pero sin recortar. El seed copia
# la descripción del CSV literalmente, como pide el briefing.
StoredTitle = Annotated[str, StringConstraints(min_length=1, max_length=TITLE_MAX_LENGTH)]
StoredDescription = Annotated[str, StringConstraints(min_length=1, max_length=DESCRIPTION_MAX_LENGTH)]


class IncidentCreate(BaseModel):
    """Cuerpo de `POST /api/incidents`.

    Sin `status`: toda incidencia nace `open` ("registrada, sin responsable
    asignado aún"). Sin `id` ni fechas: los pone el sistema. `branch` es
    obligatorio aunque exista `central` por defecto en el seed: quien
    registra sabe desde dónde, y el formulario lo pide siempre.
    """

    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Description
    category: IncidentCategory
    origin: IncidentOrigin
    branch: Branch


class StatusUpdate(BaseModel):
    """Cuerpo de `PATCH /api/incidents/{id}/status`.

    Aquí solo se comprueba que el estado exista. Si la transición está
    permitida depende del estado actual, que solo conoce la base de datos:
    lo decide el service.
    """

    model_config = ConfigDict(extra="forbid")

    status: IncidentStatus


class Incident(BaseModel):
    """Una incidencia tal y como se guarda y como la devuelve la API.

    No lleva el `ticket_id` del CSV: el briefing dice que no se almacena en
    la incidencia. El seed lo apunta en una tabla aparte (ver `database.py`).
    """

    id: UUID
    title: StoredTitle
    description: StoredDescription
    category: IncidentCategory
    status: IncidentStatus
    origin: IncidentOrigin
    branch: Branch
    # AwareDatetime: una fecha sin zona horaria es un error, no "hora local".
    # Comparar una con zona y otra sin ella lanza TypeError en Python.
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def updated_after_created(self) -> Self:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at no puede ser anterior a created_at.")
        return self


# --- Análisis del CSV --------------------------------------------------------


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
