"""Informe de consola con el formato de la salida esperada del briefing.

Solo da formato: no calcula nada que no venga ya en el AnalysisResult. Los
textos están en inglés porque el briefing fija la salida literalmente así.
"""

from __future__ import annotations

from .analysis import AnalysisResult, percentage
from .schema import RULES_BY_CODE, SCORE_LABELS

WIDTH = 60
RULE = "=" * WIDTH
# Columna en la que termina la línea de puntos; los números se alinean después.
LEADER_END = 38
NUMBER_WIDTH = 5

BRANCH = "├─"
LAST_BRANCH = "└─"


def _leader(text: str, value: object, suffix: str = "") -> str:
    """`text ......... value suffix`, con el valor alineado a la derecha."""
    dots = "." * max(LEADER_END - len(text) - 1, 3)
    return f"{text} {dots}{str(value).rjust(NUMBER_WIDTH)}{suffix}"


def _tree(items: list[tuple[str, object, str]]) -> list[str]:
    """Rama de árbol: └─ en el último elemento y ├─ en el resto."""
    lines = []
    for index, (label, value, suffix) in enumerate(items):
        branch = LAST_BRANCH if index == len(items) - 1 else BRANCH
        lines.append(_leader(f"  {branch} {label}", value, suffix))
    return lines


def _pct(count: int, total: int) -> str:
    return f"  ({percentage(count, total):4.1f}%)"


def render_report(result: AnalysisResult, source_name: str) -> str:
    valid = result.valid_records
    lines = [
        RULE,
        "  NEXOVA — SUPPORT TICKET ANALYSIS",
        f"  Source file: {source_name}",
        RULE,
        "",
        _leader("TOTAL RECORDS IN FILE", result.total_records),
        *_tree(
            [
                ("Valid records", valid, ""),
                ("Invalid / incomplete", result.invalid_records, ""),
            ]
        ),
        "",
        "INVALID RECORDS BREAKDOWN",
    ]

    # Solo las reglas que se han activado, como en la salida del briefing.
    broken = [
        (RULES_BY_CODE[code].label, count, "")
        for code, count in result.invalid_by_rule.items()
        if count
    ]
    lines += _tree(broken) if broken else ["  (no invalid records)"]

    lines += ["", "BREAKDOWN BY CATEGORY (valid records)"]
    lines += _tree(
        [(category, count, _pct(count, valid)) for category, count in result.by_category.items()]
    )

    lines += ["", "BREAKDOWN BY STATUS (valid records)"]
    lines += _tree(
        [(status, count, _pct(count, valid)) for status, count in result.by_status.items()]
    )

    average = (
        f"{result.average_score:.2f} / 5.00" if result.average_score is not None else "n/a"
    )
    lines += [
        "",
        "SATISFACTION INDEX (closed tickets)",
        f"  Scored tickets: {result.scored_closed_records} of {result.closed_records}",
        f"  Average score: {average}",
    ]
    lines += _tree(
        [
            (f"Score {score} ({SCORE_LABELS[score]})", count, "")
            for score, count in result.score_distribution.items()
        ]
    )

    lines += ["", RULE]
    return "\n".join(lines)
