"""Transformación del CSV del analizador al modelo `Incident` del gestor.

Es la sección "Datos históricos — seed desde CSV" de
docs/contexts/proyectos/centralized-incident-manager.es.md, literal. Funciones
puras: reciben filas y devuelven borradores listos para insertar, sin tocar
ninguna base de datos. Quien inserta es scripts/seed_incidents.py.

Una fila pasa dos filtros, en este orden:
1. La validación del analizador (`validate_record`), la misma que usan
   scripts/analyze.py y la API. Así el seed carga exactamente los 96 registros
   válidos del proyecto anterior, ni uno más.
2. Los mapeos de estado y categoría y el título. Lo que no se puede mapear
   también se rechaza, con su propio código.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .analysis import InvalidRecord, iter_rows, safe_ticket_id
from .catalog import TITLE_MAX_LENGTH, Branch, IncidentCategory, IncidentOrigin, IncidentStatus
from .schema import DATE_FORMAT, RULES, Rule
from .validation import field, validate_record

# Estado del CSV -> estado del modelo.
STATUS_MAP: dict[str, IncidentStatus] = {
    "OPEN": IncidentStatus.OPEN,
    "CLOSED": IncidentStatus.RESOLVED,
    "DISCARDED": IncidentStatus.DISCARDED,
}

# Categoría del CSV -> categoría del modelo (mapeo de Nexova).
CATEGORY_MAP: dict[str, IncidentCategory] = {
    "TECHNICAL": IncidentCategory.TECHNICAL_FAILURE,
    "BILLING": IncidentCategory.PROCESS_ERROR,
    "ACCESS": IncidentCategory.TECHNICAL_FAILURE,
    "HR_QUERY": IncidentCategory.PROCESS_ERROR,
    "COMPLAINT": IncidentCategory.CLIENT_COMPLAINT,
}

# Todo el histórico son quejas de clientes, y el CSV no trae oficina.
SEED_ORIGIN = IncidentOrigin.CUSTOMER
SEED_BRANCH = Branch.CENTRAL

# Rechazos propios del seed, además de las reglas del analizador. Con el CSV
# actual nunca saltan (todo valor válido tiene mapeo y la descripción mínima
# es de 5 caracteres), pero el briefing pide descartar lo que no se pueda
# mapear, y un CSV futuro podría traer un estado o una categoría nuevos.
SEED_RULES: tuple[Rule, ...] = (
    Rule("unmapped_status", "Status without a mapping in the incident manager"),
    Rule("unmapped_category", "Category without a mapping in the incident manager"),
    Rule("empty_title", "Empty title after trimming the description"),
)

# Etiqueta de cualquier código de rechazo, del analizador o del seed.
REJECTION_LABELS: dict[str, str] = {rule.code: rule.label for rule in (*RULES, *SEED_RULES)}


@dataclass(frozen=True)
class IncidentDraft:
    """Una incidencia lista para insertar.

    `source_id` es el `ticket_id` del CSV. No es un campo del modelo: el
    briefing dice que no se almacena en la incidencia. El seed lo usa solo
    para no insertar dos veces la misma fila.
    """

    source_id: str
    title: str
    description: str
    category: IncidentCategory
    status: IncidentStatus
    origin: IncidentOrigin
    branch: Branch
    created_at: datetime

    @property
    def updated_at(self) -> datetime:
        # Al insertar, la última modificación es la creación.
        return self.created_at


@dataclass(frozen=True)
class SeedPlan:
    """Qué se insertaría a partir de un CSV. Sin ningún dato personal."""

    total_records: int
    drafts: tuple[IncidentDraft, ...]
    rejected: tuple[InvalidRecord, ...]


def make_title(description: str) -> str:
    """Primeros 120 caracteres de la descripción, sin espacios en los bordes."""
    return description.strip()[:TITLE_MAX_LENGTH].strip()


def transform_record(
    row: Mapping[str, str | None],
) -> tuple[IncidentDraft | None, tuple[str, ...]]:
    """Una fila del CSV -> (borrador, ()) o (None, códigos de rechazo)."""
    errors = validate_record(row)
    if errors:
        return None, tuple(errors)

    status = STATUS_MAP.get(field(row, "status"))
    category = CATEGORY_MAP.get(field(row, "category"))
    # La descripción se copia literalmente; el título sale de ella.
    description = row.get("description") or ""
    title = make_title(description)

    errors = []
    if status is None:
        errors.append("unmapped_status")
    if category is None:
        errors.append("unmapped_category")
    if not title:
        errors.append("empty_title")
    if errors:
        return None, tuple(errors)

    # validate_record ya garantiza YYYY-MM-DD real. Medianoche UTC.
    created_at = datetime.strptime(field(row, "date"), DATE_FORMAT).replace(tzinfo=UTC)

    return (
        IncidentDraft(
            source_id=field(row, "ticket_id"),
            title=title,
            description=description,
            category=category,
            status=status,
            origin=SEED_ORIGIN,
            branch=SEED_BRANCH,
            created_at=created_at,
        ),
        (),
    )


def plan_seed(lines: Iterable[str]) -> SeedPlan:
    """Transforma un CSV entero. Lanza IncidentFileError si el fichero no sirve.

    Devuelve todos los rechazos, no una muestra: el seed los muestra todos en
    consola para que se corrijan en el origen.
    """
    total = 0
    drafts: list[IncidentDraft] = []
    rejected: list[InvalidRecord] = []

    for line, row in iter_rows(lines):
        total += 1
        draft, errors = transform_record(row)
        if draft is None:
            rejected.append(InvalidRecord(line=line, ticket_id=safe_ticket_id(row), rules=errors))
        else:
            drafts.append(draft)

    return SeedPlan(total_records=total, drafts=tuple(drafts), rejected=tuple(rejected))


def plan_seed_file(path: str | Path) -> SeedPlan:
    """Abre el fichero y lo transforma. `utf-8-sig` acepta UTF-8 con o sin BOM."""
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return plan_seed(handle)
