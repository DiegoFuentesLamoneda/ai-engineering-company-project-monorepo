"""Rutas HTTP del directorio de proveedores.

El router no decide reglas: valida la entrada con los modelos, llama al
`service` y traduce cada error del dominio a su código HTTP.

| Código | Cuándo |
| --- | --- |
| 200 | Lectura, cambio o borrado correcto (el borrado devuelve el proveedor) |
| 201 | Proveedor creado |
| 404 | El ID no existe |
| 409 | Borrar un proveedor suspendido |
| 422 | El cuerpo o los filtros no cumplen el BRIEFING (lo responde FastAPI) |

Las rutas son `def` y no `async def`: TinyDB lee y escribe en disco de forma
bloqueante, y FastAPI ejecuta las rutas síncronas en un pool de hilos.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from ...schemas import ErrorResponse
from . import service
from .database import SupplierRepository
from .dependencies import get_supplier_repository
from .exceptions import SupplierNotFoundError, SuspendedSupplierDeletionError
from .schemas import Category, Country, RateUpdate, StatusUpdate, Supplier, SupplierCreate

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

Repo = Annotated[SupplierRepository, Depends(get_supplier_repository)]

NOT_FOUND = {404: {"model": ErrorResponse, "description": "No existe ningún proveedor con ese ID"}}


def _not_found(error: SupplierNotFoundError) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, str(error))


@router.post(
    "",
    response_model=Supplier,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un proveedor",
)
def create_supplier(data: SupplierCreate, repo: Repo, response: Response) -> Supplier:
    supplier = service.create_supplier(repo, data)
    # Convención REST: dónde se puede consultar lo que se acaba de crear.
    response.headers["Location"] = f"{router.prefix}/{supplier.id}"
    return supplier


@router.get("", response_model=list[Supplier], summary="Listar proveedores, con filtros opcionales")
def list_suppliers(
    repo: Repo,
    country: Annotated[Country | None, Query(description="Spain o USA")] = None,
    category: Annotated[Category | None, Query(description="Una de las categorías del BRIEFING")] = None,
) -> list[Supplier]:
    # Un valor fuera del BRIEFING (country=Mexico) es un 422, no una lista
    # vacía: así un error de escritura en el filtro no parece "no hay nada".
    return service.list_suppliers(repo, country=country, category=category)


@router.get("/{supplier_id}", response_model=Supplier, summary="Consultar un proveedor", responses=NOT_FOUND)
def get_supplier(supplier_id: int, repo: Repo) -> Supplier:
    try:
        return service.get_supplier(repo, supplier_id)
    except SupplierNotFoundError as error:
        raise _not_found(error) from error


@router.patch(
    "/{supplier_id}/rate",
    response_model=Supplier,
    summary="Actualizar la tarifa mensual (renueva updated_at)",
    responses=NOT_FOUND,
)
def update_rate(supplier_id: int, data: RateUpdate, repo: Repo) -> Supplier:
    try:
        return service.update_rate(repo, supplier_id, data)
    except SupplierNotFoundError as error:
        raise _not_found(error) from error


@router.patch(
    "/{supplier_id}/status",
    response_model=Supplier,
    summary="Activar o suspender un proveedor",
    responses=NOT_FOUND,
)
def update_status(supplier_id: int, data: StatusUpdate, repo: Repo) -> Supplier:
    try:
        return service.update_status(repo, supplier_id, data)
    except SupplierNotFoundError as error:
        raise _not_found(error) from error


@router.delete(
    "/{supplier_id}",
    response_model=Supplier,
    summary="Eliminar un proveedor activo (devuelve el proveedor borrado)",
    responses={
        **NOT_FOUND,
        409: {"model": ErrorResponse, "description": "Está suspendido: se conserva para el historial"},
    },
)
def delete_supplier(supplier_id: int, repo: Repo) -> Supplier:
    try:
        return service.delete_supplier(repo, supplier_id)
    except SupplierNotFoundError as error:
        raise _not_found(error) from error
    except SuspendedSupplierDeletionError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
