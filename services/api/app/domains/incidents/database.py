"""Persistencia del gestor de incidencias sobre TinyDB.

Un fichero, dos tablas:

- `incidents`: las incidencias. El `id` es un UUID guardado dentro del
  documento; el `doc_id` numérico de TinyDB es interno y no sale de aquí.
  Un UUID no se puede adivinar ni se reutiliza al borrar, y funcionará igual
  el día que se migre a Postgres.
- `seed_imports`: qué `ticket_id` del CSV histórico se ha cargado ya y con qué
  incidencia. Es la clave de idempotencia del seed. Va aparte porque el
  briefing dice que el `ticket_id` no se almacena en la incidencia.

Este módulo es el único que conoce TinyDB. El resto del dominio trabaja con
modelos `Incident`: el día que se migre a Postgres, solo cambia este fichero.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from uuid import UUID

from incident_analysis import Branch, IncidentCategory, IncidentOrigin, IncidentStatus
from tinydb import Query, TinyDB
from tinydb.table import Document

from ...json_storage import SafeJSONStorage
from .schemas import Incident

TABLE = "incidents"
SEED_IMPORTS_TABLE = "seed_imports"


class IncidentRepository:
    """Lectura y escritura de incidencias en un fichero de TinyDB.

    Un cerrojo hace que las operaciones vayan de una en una: FastAPI ejecuta
    las rutas síncronas en varios hilos y TinyDB no está pensado para eso.
    """

    def __init__(self, path: Path) -> None:
        self._db = TinyDB(
            path,
            storage=SafeJSONStorage,
            create_dirs=True,
            encoding="utf-8",
            # Fichero legible a simple vista, con tildes y sangría.
            ensure_ascii=False,
            indent=2,
        )
        self._table = self._db.table(TABLE)
        self._seed_imports = self._db.table(SEED_IMPORTS_TABLE)
        self._lock = threading.Lock()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> IncidentRepository:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # --- Lectura -----------------------------------------------------------

    def list(
        self,
        *,
        status: IncidentStatus | None = None,
        origin: IncidentOrigin | None = None,
        branch: Branch | None = None,
        category: IncidentCategory | None = None,
    ) -> list[Incident]:
        """Las incidencias que cumplen los filtros que lleguen, de la más reciente a la más antigua.

        Sin incidencias devuelve una lista vacía, nunca un error.
        """
        incident = Query()
        filters = {"status": status, "origin": origin, "branch": branch, "category": category}
        conditions = [incident[field] == value.value for field, value in filters.items() if value is not None]

        with self._lock:
            if not conditions:
                documents = self._table.all()
            else:
                condition = conditions[0]
                for extra in conditions[1:]:
                    condition &= extra
                documents = self._table.search(condition)
        incidents = [_to_incident(doc) for doc in documents]
        # Se ordena ya convertido a datetime, no comparando el texto del JSON.
        return sorted(incidents, key=lambda i: i.created_at, reverse=True)

    def get(self, incident_id: UUID) -> Incident | None:
        with self._lock:
            document = self._table.get(Query().id == str(incident_id))
        return _to_incident(document) if document is not None else None

    def count(self) -> int:
        with self._lock:
            return len(self._table)

    # --- Escritura ---------------------------------------------------------

    def insert(self, incident: Incident) -> Incident:
        with self._lock:
            self._table.insert(incident.model_dump(mode="json"))
        return incident

    def update_status(
        self,
        incident_id: UUID,
        *,
        expected: IncidentStatus,
        target: IncidentStatus,
        updated_at: datetime,
    ) -> Incident | None:
        """Cambia el estado solo si sigue siendo `expected`.

        El service lee la incidencia, decide si la transición es válida y
        después llama aquí. Entre la lectura y la escritura otra petición
        podría haberla cambiado: si dos personas la pasan a la vez de
        `in_progress` a `resolved` y a `discarded`, ganaría la última sin
        saber que la otra existía. Por eso la comprobación se repite dentro
        del cerrojo. Devuelve `None` si la incidencia no existe o ya no está
        en `expected`; el service vuelve a leerla para saber cuál de las dos.
        """
        match = (Query().id == str(incident_id)) & (Query().status == expected.value)
        with self._lock:
            document = self._table.get(match)
            if document is None:
                return None
            # Se valida el documento entero antes de escribirlo: así se
            # comprueba que updated_at no queda antes de created_at, y la
            # fecha se guarda con el mismo formato que en el alta.
            updated = Incident.model_validate(dict(document) | {"status": target, "updated_at": updated_at})
            self._table.update(updated.model_dump(mode="json"), match)
        return updated

    # --- Seed --------------------------------------------------------------

    def insert_seeded(self, incident: Incident, source_id: str) -> bool:
        """Inserta una incidencia del CSV histórico si su `ticket_id` no se cargó ya.

        Devuelve `True` si la ha insertado y `False` si ya estaba. Comprobar y
        escribir ocurren dentro del mismo cerrojo: dos seeds a la vez no
        pueden insertar la misma fila dos veces.
        """
        with self._lock:
            if self._seed_imports.contains(Query().ticket_id == source_id):
                return False
            self._table.insert(incident.model_dump(mode="json"))
            self._seed_imports.insert({"ticket_id": source_id, "incident_id": str(incident.id)})
        return True

    def seeded_count(self) -> int:
        with self._lock:
            return len(self._seed_imports)


def _to_incident(document: Document) -> Incident:
    return Incident.model_validate(dict(document))
