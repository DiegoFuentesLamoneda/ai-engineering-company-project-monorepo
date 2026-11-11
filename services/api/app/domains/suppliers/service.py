"""Reglas del directorio de proveedores.

Aquí se decide qué pasa en cada operación: quién pone `updated_at`, qué se
puede borrar y qué ocurre si el proveedor no existe. No importa fastapi ni
TinyDB: recibe modelos, habla con el repositorio y lanza errores del dominio.

`now` es un parámetro para que las pruebas fijen la hora; en la API se queda
sin pasar y vale la hora actual en UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .database import SupplierRepository
from .exceptions import SupplierNotFoundError, SuspendedSupplierDeletionError
from .schemas import (
    Category,
    Country,
    RateUpdate,
    StatusUpdate,
    Supplier,
    SupplierCreate,
    SupplierStatus,
)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def list_suppliers(
    repo: SupplierRepository,
    country: Country | None = None,
    category: Category | None = None,
) -> list[Supplier]:
    """El directorio, ordenado por nombre para que el listado no baile."""
    suppliers = repo.list(country=country, category=category)
    return sorted(suppliers, key=lambda s: s.name.casefold())


def get_supplier(repo: SupplierRepository, supplier_id: int) -> Supplier:
    supplier = repo.get(supplier_id)
    if supplier is None:
        raise SupplierNotFoundError(supplier_id)
    return supplier


def create_supplier(repo: SupplierRepository, data: SupplierCreate, now: datetime | None = None) -> Supplier:
    # El alta cuenta como la primera tarifa: `updated_at` nace con ella.
    return repo.insert(data, updated_at=_now(now))


def update_rate(
    repo: SupplierRepository, supplier_id: int, data: RateUpdate, now: datetime | None = None
) -> Supplier:
    """Cambia la tarifa y deja constancia de cuándo (trazabilidad del BRIEFING).

    `updated_at` se renueva aunque la tarifa sea la misma: Patricia ha
    confirmado ese precio en esa fecha, y eso también es un dato.
    """
    changes = {"monthly_rate": data.monthly_rate, "updated_at": _now(now).isoformat()}
    supplier = repo.update(supplier_id, changes)
    if supplier is None:
        raise SupplierNotFoundError(supplier_id)
    return supplier


def update_status(repo: SupplierRepository, supplier_id: int, data: StatusUpdate) -> Supplier:
    # Solo la tarifa mueve `updated_at`: el BRIEFING lo usa para justificar
    # variaciones de presupuesto, y suspender no cambia el precio.
    supplier = repo.update(supplier_id, {"status": data.status.value})
    if supplier is None:
        raise SupplierNotFoundError(supplier_id)
    return supplier


def delete_supplier(repo: SupplierRepository, supplier_id: int) -> Supplier:
    """Borra un proveedor activo y lo devuelve. Un suspendido se conserva (BRIEFING)."""
    supplier = get_supplier(repo, supplier_id)
    if supplier.status == SupplierStatus.SUSPENDED:
        raise SuspendedSupplierDeletionError(supplier.name)
    if not repo.delete(supplier_id):
        # Otra petición lo ha borrado entre la lectura y el borrado.
        raise SupplierNotFoundError(supplier_id)
    return supplier
