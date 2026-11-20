"""Carga en el gestor las incidencias históricas del CSV del analizador.

La transformación (qué filas valen y cómo se mapean) es del paquete
compartido: `incident_analysis.plan_seed_file`. Aquí solo se convierte cada
borrador en un `Incident` y se inserta. Quien lo lanza es
scripts/seed_incidents.py.

Idempotente: cada `ticket_id` se apunta en la tabla `seed_imports` al
insertarlo, y un ticket ya apuntado se salta. Lanzarlo dos veces no duplica.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from incident_analysis import IncidentDraft, SeedPlan
from pydantic import ValidationError

from .database import IncidentRepository
from .schemas import Incident


@dataclass(frozen=True)
class ModelRejection:
    """Un borrador que el paquete aceptó pero el modelo no (p. ej., descripción > 2000)."""

    ticket_id: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class SeedResult:
    inserted: int
    skipped: int
    model_rejected: tuple[ModelRejection, ...]
    total: int


def to_incident(draft: IncidentDraft, new_id: UUID) -> Incident:
    """Borrador -> incidencia. Pasa por el mismo modelo que guarda la API."""
    return Incident(
        id=new_id,
        title=draft.title,
        description=draft.description,
        category=draft.category,
        status=draft.status,
        origin=draft.origin,
        branch=draft.branch,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
    )


def seed_incidents(
    repo: IncidentRepository,
    plan: SeedPlan,
    new_id: Callable[[], UUID] = uuid4,
) -> SeedResult:
    """Inserta los borradores de `plan` cuyo ticket aún no se cargó."""
    # Se valida todo antes de escribir: un borrador que el modelo rechaza se
    # informa y se salta, sin dejar la carga a medias por un error a mitad.
    ready: list[tuple[Incident, str]] = []
    model_rejected: list[ModelRejection] = []
    for draft in plan.drafts:
        try:
            ready.append((to_incident(draft, new_id()), draft.source_id))
        except ValidationError as exc:
            fields = tuple(sorted({str(e["loc"][0]) for e in exc.errors() if e["loc"]}))
            model_rejected.append(ModelRejection(ticket_id=draft.source_id, fields=fields))

    inserted = sum(repo.insert_seeded(incident, source_id) for incident, source_id in ready)

    return SeedResult(
        inserted=inserted,
        skipped=len(ready) - inserted,
        model_rejected=tuple(model_rejected),
        total=repo.count(),
    )
