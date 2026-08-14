#!/usr/bin/env python3
"""Sincroniza los contextos de empresa del syllabus de 4Geeks con este repo.

El syllabus publica los contextos en
https://github.com/4GeeksAcademy/ai-engineering-syllabus/tree/main/content/contexts
con una estructura pensada para servir a las cuatro empresas a la vez. Este
script la reorganiza en la estructura de este repo, que separa la empresa
activa (Nexova) del archivo de referencia:

    docs/contexts/                  <- empresa activa, plano y navegable
    docs/contexts-archive/<empresa> <- las otras tres, misma convencion

Normalizaciones que aplica sobre el origen:

  * El ingles se llama unas veces `CONTEXT-x.en.md` y otras `CONTEXT-x.md`.
    Aqui siempre es `.en.md`.
  * El nombre del archivo pasa a ser el hito (`01-web-fundamentals.es.md`) en
    lugar de repetir el nombre de la empresa en cada carpeta.
  * Los hitos 06, 08 y 10 traen dos contextos cada uno en subcarpetas; se
    aplanan a `06-telemetry`, `06-data-pipelines`, `08-agent-harnessing`, etc.
  * `07-trainning-rag` esta mal escrito en origen; aqui es `07-training-rag`.
  * Las carpetas sin numerar van a `proyectos/`, los CSV y PDF a `assets/` y
    los documentos de dominio de `00-general-contexts/<empresa>/` a
    `knowledge-base/`.

Uso:
    python scripts/sync_contexts.py --dry-run     # muestra el plan, no escribe
    python scripts/sync_contexts.py               # descarga y coloca
    python scripts/sync_contexts.py --only nexova # solo la empresa activa

No borra nada: los archivos que ya no existan en origen se quedan como estan.
Tampoco toca los README.md que escribimos a mano.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = "4GeeksAcademy/ai-engineering-syllabus"
BRANCH = "main"
SOURCE_ROOT = "content/contexts"

TREE_URL = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{{path}}"

ACTIVE_COMPANY = "nexova"
COMPANIES = ("nexova", "brasaland", "healthcore", "trackflow")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACTIVE_DIR = PROJECT_ROOT / "docs" / "contexts"
ARCHIVE_DIR = PROJECT_ROOT / "docs" / "contexts-archive"

# Carpeta de origen -> nombre de hito en destino. Las claves con "/" son
# subcarpetas de un hito que trae mas de un contexto.
MILESTONE_MAP = {
    "01-web-fundamentals": "01-web-fundamentals",
    "02-coding-fundamentals": "02-coding-fundamentals",
    "03-frontend-development": "03-frontend-development",
    "05-backend-development": "05-backend-development",
    # Los hitos 06, 08 y 10 traen dos contextos. El sufijo a/b conserva el orden
    # en que se cursan, que no coincide con el alfabetico: en el 08 la memoria es
    # la Parte 1 y el harness la Parte 2, y en el 10 las notificaciones van antes
    # que la comunicacion.
    "06-telemetry-data-pipelines/telemetry": "06a-telemetry",
    "06-telemetry-data-pipelines/data-pipelines": "06b-data-pipelines",
    "07-trainning-rag": "07-training-rag",  # typo en origen
    "08-agent-engineering/memory": "08a-agent-memory",
    "08-agent-engineering/harnessing": "08b-agent-harnessing",
    "09-agentic-workflows": "09-agentic-workflows",
    "10-realtime/notification": "10a-realtime-notification",
    "10-realtime/communication": "10b-realtime-communication",
}


def http_get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "sync-contexts"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def company_root(company: str) -> Path:
    if company == ACTIVE_COMPANY:
        return ACTIVE_DIR
    return ARCHIVE_DIR / company


def language_suffix(filename: str) -> str:
    """Devuelve `.es.md` o `.en.md`. En origen el ingles a veces es solo `.md`."""
    if filename.endswith(".es.md"):
        return ".es.md"
    return ".en.md"


def company_in(path: str) -> str | None:
    for company in COMPANIES:
        if company in path.lower():
            return company
    return None


def destination_for(path: str) -> tuple[str, Path] | None:
    """Mapea una ruta del syllabus a (empresa, ruta local). None si se ignora."""
    relative = path[len(SOURCE_ROOT) + 1 :]
    company = company_in(relative)

    # READMEs propios del syllabus: se guardan como referencia en el archivo.
    if "/" not in relative and relative.startswith("README"):
        suffix = language_suffix(relative)
        return ACTIVE_COMPANY, ARCHIVE_DIR / f"_upstream-README{suffix}"

    if company is None:
        return None

    root = company_root(company)
    parts = relative.split("/")
    filename = parts[-1]
    suffix = language_suffix(filename)

    # 00-general-contexts/CONTEXT-<empresa>-briefing.<lang>.md
    if parts[0] == "00-general-contexts":
        if len(parts) == 2:
            return company, root / f"00-briefing{suffix}"
        # 00-general-contexts/<empresa>/<empresa>-<tema>.<lang>.md
        topic = re.sub(rf"^{company}-", "", filename)
        topic = re.sub(r"\.(es|en)?\.?md$", "", topic)
        return company, root / "knowledge-base" / f"{topic}{suffix}"

    # PDFs de RFP: 09-agentic-workflows/rfp-requests/<empresa>/...-request-N.pdf
    if filename.endswith(".pdf"):
        match = re.search(r"request-(\d+)", filename)
        number = match.group(1) if match else filename
        return company, root / "assets" / f"rfp-request-{number}.pdf"

    # CSVs: incidents-<empresa>.csv y <empresa>_sales.csv
    if filename.endswith(".csv"):
        kind = "incidents" if "incident" in filename else "sales"
        return company, root / "assets" / f"{kind}.csv"

    # Hitos numerados, con o sin subcarpeta.
    for depth in (2, 1):
        key = "/".join(parts[:depth])
        if key in MILESTONE_MAP:
            return company, root / f"{MILESTONE_MAP[key]}{suffix}"

    # Carpetas sin numerar -> proyectos/
    if re.match(r"^\d{2}-", parts[0]):
        # Hito numerado que aun no esta en MILESTONE_MAP: avisamos y lo colocamos
        # con el nombre de la carpeta de origen para no perderlo.
        print(f"  ! hito no mapeado, usando nombre de origen: {parts[0]}")
        return company, root / f"{parts[0]}{suffix}"

    return company, root / "proyectos" / f"{parts[0]}{suffix}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="no escribe nada")
    parser.add_argument("--only", choices=COMPANIES, help="sincroniza una sola empresa")
    args = parser.parse_args()

    print(f"Leyendo el arbol de {REPO}@{BRANCH} ...")
    try:
        tree = json.loads(http_get(TREE_URL))["tree"]
    except urllib.error.URLError as error:
        print(f"No se pudo leer el arbol del repositorio: {error}", file=sys.stderr)
        return 1

    plan: list[tuple[str, Path]] = []
    skipped = 0
    for item in tree:
        path = item.get("path", "")
        if item.get("type") != "blob" or not path.startswith(SOURCE_ROOT + "/"):
            continue
        destination = destination_for(path)
        if destination is None:
            skipped += 1
            continue
        company, local_path = destination
        if args.only and company != args.only:
            continue
        plan.append((path, local_path))

    print(f"{len(plan)} archivos a sincronizar ({skipped} ignorados)\n")

    if args.dry_run:
        for source, local_path in sorted(plan, key=lambda pair: str(pair[1])):
            print(f"  {local_path.relative_to(PROJECT_ROOT)}  <-  {source}")
        return 0

    written = 0
    for source, local_path in plan:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            local_path.write_bytes(http_get(RAW_URL.format(path=source)))
        except urllib.error.URLError as error:
            print(f"  ! fallo al descargar {source}: {error}", file=sys.stderr)
            continue
        written += 1
        if written % 25 == 0:
            print(f"  {written}/{len(plan)} ...")

    print(f"\nListo: {written} archivos escritos.")
    print("Los README.md de docs/contexts/ y docs/contexts-archive/ se mantienen a mano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
