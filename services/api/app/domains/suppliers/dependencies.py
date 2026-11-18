"""Dependencias del dominio de proveedores."""

from fastapi import Request

from .database import SupplierRepository


def get_supplier_repository(request: Request) -> SupplierRepository:
    """El repositorio que abrió la app al arrancar (ver `main.lifespan`)."""
    return request.app.state.suppliers
