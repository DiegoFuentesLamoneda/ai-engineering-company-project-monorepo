"""Persistencia del directorio de proveedores sobre TinyDB.

TinyDB guarda los documentos en un fichero JSON en disco. Cada escritura se
vuelca al fichero en el acto, así que los datos sobreviven a un reinicio del
servidor. El ID de cada proveedor es el `doc_id` que asigna TinyDB: no se
guarda dentro del documento, se añade al leerlo.

Limitación conocida: TinyDB calcula el siguiente ID como el mayor existente
más uno. Si se borra el último proveedor y se reinicia el servidor, su ID se
le da al siguiente que se cree. Con borrados poco frecuentes no molesta; una
base de datos con secuencias (Postgres) no tiene este problema.

Este módulo es el único que conoce TinyDB. El resto del dominio trabaja con
modelos `Supplier`: el día que se migre a Postgres, solo cambia este fichero.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.table import Document

from .schemas import Category, Country, Supplier, SupplierCreate

TABLE = "suppliers"


class SupplierRepository:
    """Lectura y escritura de proveedores en un fichero de TinyDB.

    TinyDB no está pensado para varios hilos a la vez, y FastAPI ejecuta las
    rutas síncronas en un pool de hilos. Un cerrojo hace que las operaciones
    se ejecuten de una en una: si dos peticiones escribieran a la vez, una
    podría pisar el fichero de la otra.
    """

    def __init__(self, path: Path) -> None:
        self._db = TinyDB(
            path,
            storage=JSONStorage,
            create_dirs=True,
            encoding="utf-8",
            # Fichero legible a simple vista, con tildes y sangría.
            ensure_ascii=False,
            indent=2,
        )
        self._table = self._db.table(TABLE)
        self._lock = threading.Lock()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> SupplierRepository:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # --- Lectura -----------------------------------------------------------

    def list(self, country: Country | None = None, category: Category | None = None) -> list[Supplier]:
        """Todos los proveedores, o solo los que cumplen los filtros que lleguen."""
        supplier = Query()
        conditions = []
        if country is not None:
            conditions.append(supplier.country == country.value)
        if category is not None:
            # `any`: la lista de categorías del proveedor contiene esta.
            conditions.append(supplier.categories.any([category.value]))

        with self._lock:
            if not conditions:
                documents = self._table.all()
            else:
                condition = conditions[0]
                for extra in conditions[1:]:
                    condition &= extra
                documents = self._table.search(condition)
        return [_to_supplier(doc) for doc in documents]

    def get(self, supplier_id: int) -> Supplier | None:
        with self._lock:
            document = self._table.get(doc_id=supplier_id)
        return _to_supplier(document) if document is not None else None

    def names(self) -> set[str]:
        with self._lock:
            return {doc["name"] for doc in self._table.all()}

    def count(self) -> int:
        with self._lock:
            return len(self._table)

    # --- Escritura ---------------------------------------------------------

    def insert(self, data: SupplierCreate, updated_at: datetime) -> Supplier:
        document = data.model_dump(mode="json") | {"updated_at": updated_at.isoformat()}
        with self._lock:
            supplier_id = self._table.insert(document)
        return Supplier.model_validate(document | {"id": supplier_id})

    def update(self, supplier_id: int, changes: dict[str, Any]) -> Supplier | None:
        """Aplica `changes` (ya serializados a JSON) y devuelve el resultado."""
        with self._lock:
            if not self._table.contains(doc_id=supplier_id):
                return None
            self._table.update(changes, doc_ids=[supplier_id])
            document = self._table.get(doc_id=supplier_id)
        return _to_supplier(document)

    def delete(self, supplier_id: int) -> bool:
        with self._lock:
            removed = self._table.remove(doc_ids=[supplier_id])
        return bool(removed)


def _to_supplier(document: Document) -> Supplier:
    return Supplier.model_validate(dict(document) | {"id": document.doc_id})
