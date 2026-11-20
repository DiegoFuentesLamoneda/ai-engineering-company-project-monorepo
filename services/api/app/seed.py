"""Carga los proveedores del BRIEFING en la base de datos de TinyDB.

Desde services/api:
    uv run seed

Se puede lanzar las veces que haga falta: un proveedor cuyo nombre ya está en
la base de datos se salta, así que nunca se duplica. Cada entrada pasa por el
mismo modelo que `POST /suppliers` (`SupplierCreate`): si el BRIEFING trajera
un dato que la API rechazaría, el seeder también lo rechaza.

Consecuencia a tener en cuenta: si se borra por la API un proveedor del
BRIEFING, la siguiente ejecución del seeder lo vuelve a crear.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NoReturn

from pydantic import ValidationError

from app.config import load_settings
from app.domains.suppliers.database import SupplierRepository
from app.domains.suppliers.schemas import SupplierCreate
from app.domains.suppliers.seed_data import SUPPLIERS_SEED
from app.errors import StorageUnavailableError


@dataclass(frozen=True)
class SeedResult:
    inserted: int
    skipped: int
    total: int


def seed_suppliers(
    repo: SupplierRepository,
    seed: list[dict] = SUPPLIERS_SEED,
    now: datetime | None = None,
) -> SeedResult:
    """Inserta los proveedores de `seed` que aún no están en `repo`."""
    # Se valida todo antes de escribir nada: o entra el BRIEFING entero o
    # no entra nada, en vez de dejar la base de datos a medias.
    suppliers = [SupplierCreate.model_validate(entry) for entry in seed]
    now = now or datetime.now(timezone.utc)

    existing = repo.names()
    inserted = 0
    for supplier in suppliers:
        if supplier.name in existing:
            continue
        repo.insert(supplier, updated_at=now)
        existing.add(supplier.name)
        inserted += 1

    return SeedResult(inserted=inserted, skipped=len(suppliers) - inserted, total=repo.count())


def _reasons(error: ValidationError) -> str:
    """Campo y motivo de cada error, sin el valor recibido."""
    return "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors())


def _fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    # En Windows, la salida redirigida usa la codificación antigua del sistema
    # y las tildes salen rotas. UTF-8 se lee bien en cualquier terminal.
    # stderr también: ahí van los errores.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        settings = load_settings()
    except ValidationError as error:
        _fail(f"Configuración no válida ({_reasons(error)}). Revisa las variables NEXOVA_API_* del .env.")
    try:
        with SupplierRepository(settings.suppliers_db_path) as repo:
            result = seed_suppliers(repo)
    except ValidationError as error:
        # seed_suppliers valida todo antes de escribir: no ha entrado nada.
        _fail(f"El BRIEFING trae un proveedor no válido ({_reasons(error)}). No se ha insertado nada.")
    except StorageUnavailableError as error:
        # El motivo concreto (JSON roto, sin permisos) es la causa.
        _fail(f"{error} ({error.__cause__}). Revisa el fichero y vuelve a lanzarlo.")
    except OSError as error:
        # Al abrir: la carpeta no se puede crear o el fichero no se puede abrir.
        _fail(f"No se pudo abrir la base de datos: {error}")
    print(f"Base de datos: {settings.suppliers_db_path}")
    print(f"Proveedores insertados: {result.inserted}")
    print(f"Ya existían (saltados): {result.skipped}")
    print(f"Total en el directorio: {result.total}")


if __name__ == "__main__":
    main()
