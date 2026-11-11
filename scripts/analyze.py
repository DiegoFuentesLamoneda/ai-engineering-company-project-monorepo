"""Analizador de tickets de soporte de Nexova — fase 1 del proyecto.

Uso (desde scripts/):
    python analyze.py incidents-nexova.csv

Valida el fichero, imprime el resumen y ofrece exportarlo a results.csv (en
la carpeta desde la que se ejecuta). Toda la lógica vive en el paquete
packages/incident-analysis, que es el mismo que usa la API: este archivo solo
lee argumentos, imprime y pregunta.

Ningún email de cliente aparece en la salida, ni en los errores.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# El paquete compartido no hace falta instalarlo para usar el script: se añade
# su carpeta a la ruta de importación. Si está instalado con `pip install -e`,
# esta línea no cambia nada.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "incident-analysis"))

from incident_analysis import (  # noqa: E402  (va después de ajustar sys.path)
    IncidentFileError,
    analyze_file,
    render_report,
    write_results_csv,
)

RESULTS_FILE = "results.csv"
EXPORT_PROMPT = "Export results to CSV? [y / n]: "
# La salida del briefing pregunta [y / n]; se acepta también la respuesta en español.
YES_ANSWERS = {"y", "yes", "s", "si", "sí"}


def ask_to_export() -> bool:
    try:
        answer = input(EXPORT_PROMPT)
    except EOFError:
        # Sin terminal interactiva (por ejemplo, en una tarea programada): no exporta.
        print()
        return False
    return answer.strip().lower() in YES_ANSWERS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valida y resume un CSV de tickets de soporte de Nexova."
    )
    parser.add_argument("csv_path", type=Path, help="ruta al fichero CSV de tickets")
    args = parser.parse_args(argv)

    if not args.csv_path.is_file():
        print(f"Error: no existe el fichero '{args.csv_path}'.", file=sys.stderr)
        return 1

    try:
        result = analyze_file(args.csv_path)
    except IncidentFileError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(render_report(result, args.csv_path.name))

    if ask_to_export():
        output = Path(RESULTS_FILE)
        with output.open("w", encoding="utf-8", newline="") as handle:
            count = write_results_csv(result, handle)
        print(f"Saved {count} metrics to {output.resolve()}")
    else:
        print("Export skipped.")
    return 0


if __name__ == "__main__":
    # La consola de Windows redirigida a un fichero usa cp1252, que no tiene
    # los caracteres de caja (├─) y estropea los acentos de los errores. Se fuerza
    # UTF-8 en las dos salidas para que nunca falle ni se corrompa al imprimir.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
