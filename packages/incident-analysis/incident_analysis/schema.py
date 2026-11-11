"""Contrato de datos del CSV de tickets de soporte de Nexova.

Todo lo que aparece aquí está copiado literalmente de
docs/contexts/proyectos/incidents-file-analysis.es.md. Si el briefing cambia,
este es el único archivo que se toca: la validación, las métricas, el script,
la API y la exportación lo importan desde aquí.
"""

from __future__ import annotations

from dataclasses import dataclass

# Columnas que el fichero debe traer en la cabecera, en el orden del briefing.
COLUMNS: tuple[str, ...] = (
    "ticket_id",
    "date",
    "client_company",
    "category",
    "description",
    "agent_id",
    "status",
    "customer_email",
    "satisfaction_score",
)

# Campo con datos personales. Nunca se imprime, se registra ni se exporta.
SENSITIVE_COLUMNS: frozenset[str] = frozenset({"customer_email"})

# Tuplas y no conjuntos: el orden es el del briefing y es el que se muestra.
CATEGORIES: tuple[str, ...] = ("TECHNICAL", "BILLING", "ACCESS", "HR_QUERY", "COMPLAINT")
STATUSES: tuple[str, ...] = ("OPEN", "CLOSED", "DISCARDED")
CLOSED_STATUS = "CLOSED"

SCORE_MIN = 1
SCORE_MAX = 5
SCORE_LABELS: dict[int, str] = {
    1: "Very dissatisfied",
    2: "Dissatisfied",
    3: "Neutral",
    4: "Satisfied",
    5: "Very satisfied",
}

TICKET_ID_PATTERN = r"NXV-\d{6}"
AGENT_ID_PATTERN = r"AGT-\d{2}"
DATE_FORMAT = "%Y-%m-%d"
DESCRIPTION_MIN_LENGTH = 5


@dataclass(frozen=True)
class Rule:
    """Una regla de invalidez: código estable para máquinas, etiqueta para personas."""

    code: str
    label: str


# Las siete primeras son la tabla "Reglas de registros inválidos" del briefing.
# Las tres últimas cubren campos que el briefing marca como obligatorios en la
# tabla de estructura pero que su tabla de reglas no menciona (ticket_id, date,
# status). El enunciado del proyecto exige invalidar cualquier registro al que
# le falte un campo obligatorio o que traiga un estado fuera de los permitidos.
RULES: tuple[Rule, ...] = (
    Rule("missing_client_company", "Missing client_company"),
    Rule("invalid_category", "Invalid or missing category"),
    Rule("invalid_description", "Invalid or missing description"),
    Rule("invalid_agent_id", "Invalid or missing agent_id"),
    Rule("invalid_email", "Invalid or missing email"),
    Rule("closed_without_score", "Closed ticket, no score"),
    Rule("score_out_of_range", "Score out of range (1-5)"),
    Rule("invalid_ticket_id", "Invalid or missing ticket_id"),
    Rule("invalid_date", "Invalid or missing date"),
    Rule("invalid_status", "Invalid or missing status"),
)

RULES_BY_CODE: dict[str, Rule] = {rule.code: rule for rule in RULES}
