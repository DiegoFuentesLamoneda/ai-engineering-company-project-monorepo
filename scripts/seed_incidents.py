"""Carga en el gestor de incidencias el histórico del CSV del analizador.

Uso, desde la raíz del repositorio:
    uv run --project services/api python scripts/seed_incidents.py

Sin argumento carga scripts/incidents-nexova.csv; se le puede pasar otra ruta.
`--project services/api` hace que corra en el entorno de la API, que es quien
tiene TinyDB y Pydantic, y que escriba en el mismo fichero que lee la API
(storage/incidents.json, o NEXOVA_API_INCIDENTS_DB_PATH si está definida).

Se puede lanzar las veces que haga falta: la primera inserta 96 incidencias y
las siguientes, 0. Las filas inválidas se listan en consola con su línea y su
ticket_id, nunca con el email del cliente.

Este archivo solo lee argumentos e imprime. La transformación es del paquete
packages/shared/incident-analysis y la inserción, de la API
(app/domains/incidents/seed.py).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "scripts" / "incidents-nexova.csv"
# `uv run --project` da el entorno de la API, pero no su carpeta: sin esto,
# `import app` no se encuentra al lanzar el script desde la raíz.
sys.path.insert(0, str(REPO_ROOT / "services" / "api"))

from incident_analysis import REJECTION_LABELS, IncidentFileError, SeedPlan, plan_seed_file  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.config import load_settings  # noqa: E402
from app.domains.incidents.database import IncidentRepository  # noqa: E402
from app.domains.incidents.seed import SeedResult, seed_incidents  # noqa: E402
from app.errors import StorageUnavailableError  # noqa: E402


def render_rejected(plan: SeedPlan) -> list[str]:
    if not plan.rejected:
        return ["Filas rechazadas: ninguna"]
    lines = [f"Filas rechazadas: {len(plan.rejected)}"]
    for record in plan.rejected:
        reasons = "; ".join(REJECTION_LABELS.get(code, code) for code in record.rules)
        lines.append(f"  - línea {record.line} · {record.ticket_id}: {reasons}")
    return lines


def render_breakdown(plan: SeedPlan) -> list[str]:
    """Lo que trae el CSV válido, para cotejarlo con los valores esperados del briefing."""
    by_status = Counter(draft.status.value for draft in plan.drafts)
    by_category = Counter(draft.category.value for draft in plan.drafts)
    return [
        "Válidas por estado:    " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())),
        "Válidas por categoría: " + ", ".join(f"{k} {v}" for k, v in sorted(by_category.items())),
    ]


def render_result(result: SeedResult) -> list[str]:
    lines = [
        f"Insertadas ahora:       {result.inserted}",
        f"Ya cargadas (saltadas): {result.skipped}",
    ]
    for rejection in result.model_rejected:
        lines.append(f"  - {rejection.ticket_id}: el modelo rechaza {', '.join(rejection.fields)}")
    lines.append(f"Total en el gestor:     {result.total}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Carga en el gestor de incidencias el CSV del analizador (idempotente)."
    )
    parser.add_argument(
        "csv_path", nargs="?", type=Path, default=DEFAULT_CSV, help="CSV de tickets (por defecto, el del briefing)"
    )
    args = parser.parse_args(argv)

    if not args.csv_path.is_file():
        print(f"Error: no existe el fichero '{args.csv_path}'.", file=sys.stderr)
        return 1

    try:
        plan = plan_seed_file(args.csv_path)
    except IncidentFileError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        # Existe pero no se puede abrir: sin permisos, o bloqueado por otro programa.
        print(f"Error: no se pudo abrir '{args.csv_path}': {exc.strerror}.", file=sys.stderr)
        return 1

    try:
        settings = load_settings()
    except ValidationError as exc:
        reasons = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        print(f"Error: configuración no válida ({reasons}). Revisa las variables NEXOVA_API_*.", file=sys.stderr)
        return 1

    try:
        with IncidentRepository(settings.incidents_db_path) as repo:
            result = seed_incidents(repo, plan)
    except StorageUnavailableError as exc:
        # El motivo concreto (JSON roto, sin permisos) es la causa.
        print(f"Error: {exc} ({exc.__cause__}). Revisa el fichero y vuelve a lanzarlo.", file=sys.stderr)
        return 1
    except OSError as exc:
        # Al abrir: la carpeta no se puede crear o el fichero no se puede abrir.
        print(f"Error: no se pudo abrir la base de datos: {exc}", file=sys.stderr)
        return 1

    print(f"CSV: {args.csv_path.name} · {plan.total_records} registros, {len(plan.drafts)} válidos")
    print("\n".join(render_rejected(plan)))
    print("\n".join(render_breakdown(plan)))
    print(f"Base de datos: {settings.incidents_db_path}")
    print("\n".join(render_result(result)))
    return 0


if __name__ == "__main__":
    # En Windows, la salida redirigida usa la codificación antigua del sistema
    # y las tildes salen rotas. UTF-8 se lee bien en cualquier terminal.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
