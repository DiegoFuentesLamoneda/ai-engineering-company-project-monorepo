"""Vocabulario del gestor de incidencias centralizado de Nexova.

Todo lo que aparece aquí está copiado literalmente de
docs/contexts/proyectos/centralized-incident-manager.es.md. Es la única
definición de estados, categorías, orígenes, sedes y transiciones: el seed
(scripts/seed_incidents.py) y la API (services/api) la importan. Si el
briefing cambia, se cambia aquí y los dos se enteran a la vez.

Son `StrEnum`: cada miembro es también un `str` ("open" == IncidentStatus.OPEN),
así que se guardan en la base de datos y viajan en el JSON como texto plano,
y Pydantic los usa directamente para rechazar cualquier otro valor.
"""

from __future__ import annotations

from enum import StrEnum

# Longitud máxima del título. Es la que fija el briefing para el título que el
# seed saca de la descripción; el formulario usa el mismo límite para que una
# incidencia del histórico y una nueva no se distingan por el título.
TITLE_MAX_LENGTH = 120


class IncidentStatus(StrEnum):
    """Ciclo de vida. El orden es el del briefing y el que se muestra."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISCARDED = "discarded"


class IncidentCategory(StrEnum):
    TECHNICAL_FAILURE = "technical_failure"
    PROCESS_ERROR = "process_error"
    CLIENT_COMPLAINT = "client_complaint"
    CANDIDATE_ISSUE = "candidate_issue"
    STAFF_ISSUE = "staff_issue"
    # Crítica para Roberto Díaz y Laura Mendoza. Es un valor más de la
    # categoría, así que la futura alerta es un filtro `category=sla_breach`.
    SLA_BREACH = "sla_breach"
    DATA_QUALITY = "data_quality"
    OTHER = "other"


class IncidentOrigin(StrEnum):
    CUSTOMER = "customer"
    BRANCH = "branch"
    INTERNAL = "internal"


class Branch(StrEnum):
    CENTRAL = "central"
    VALENCIA_OPERATIONS = "valencia_operations"
    MIAMI_OFFICE = "miami_office"
    REMOTE = "remote"


# Nombre para mostrar de cada sede, tal cual lo da el briefing.
BRANCH_LABELS: dict[Branch, str] = {
    Branch.CENTRAL: "Central — Sede Valencia",
    Branch.VALENCIA_OPERATIONS: "Valencia — Operaciones",
    Branch.MIAMI_OFFICE: "Miami Office",
    Branch.REMOTE: "Remoto (empleado sin sede fija)",
}

# Sede por defecto cuando la incidencia no corresponde a una oficina concreta.
DEFAULT_BRANCH = Branch.CENTRAL

# Transiciones válidas: a qué estados se puede pasar desde cada uno. Los
# estados finales tienen el conjunto vacío.
ALLOWED_TRANSITIONS: dict[IncidentStatus, frozenset[IncidentStatus]] = {
    IncidentStatus.OPEN: frozenset({IncidentStatus.IN_PROGRESS, IncidentStatus.DISCARDED}),
    IncidentStatus.IN_PROGRESS: frozenset({IncidentStatus.RESOLVED, IncidentStatus.DISCARDED}),
    IncidentStatus.RESOLVED: frozenset(),
    IncidentStatus.DISCARDED: frozenset(),
}

FINAL_STATUSES: frozenset[IncidentStatus] = frozenset(
    status for status, targets in ALLOWED_TRANSITIONS.items() if not targets
)


def can_transition(current: IncidentStatus | str, target: IncidentStatus | str) -> bool:
    """True si el ciclo de vida permite pasar de `current` a `target`.

    Quedarse en el mismo estado no es una transición: devuelve False. Un valor
    que no es un estado tampoco lanza nada: devuelve False.
    """
    try:
        return IncidentStatus(target) in ALLOWED_TRANSITIONS[IncidentStatus(current)]
    except ValueError:
        return False
