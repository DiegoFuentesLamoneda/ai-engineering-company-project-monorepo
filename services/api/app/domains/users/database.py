"""Persistencia de los usuarios sobre TinyDB.

Los usuarios viven solo en TinyDB, también cuando el resto de módulos pase a
Postgres: allí solo se guardará su `id` como `user_uuid`. Este módulo es el
único que conoce TinyDB; el resto del dominio trabaja con modelos `User`.

El `id` es un UUID guardado dentro del documento. El `doc_id` numérico de
TinyDB es interno y no sale de aquí (ver `schemas.User`).
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any
from uuid import UUID

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.table import Document

from .exceptions import EmailAlreadyRegisteredError
from .schemas import User

TABLE = "users"


class UserRepository:
    """Lectura y escritura de usuarios en un fichero de TinyDB.

    Un cerrojo hace que las operaciones vayan de una en una: FastAPI ejecuta
    las rutas síncronas en varios hilos y TinyDB no está pensado para eso.
    Además garantiza que el email sea único: la comprobación y la escritura
    ocurren dentro del mismo cerrojo, así que dos altas simultáneas con el
    mismo email no pueden pasar las dos.
    """

    def __init__(self, path: Path) -> None:
        self._db = TinyDB(
            path,
            storage=JSONStorage,
            create_dirs=True,
            encoding="utf-8",
            ensure_ascii=False,
            indent=2,
        )
        self._table = self._db.table(TABLE)
        self._lock = threading.Lock()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> UserRepository:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # --- Lectura -----------------------------------------------------------

    def list(self) -> list[User]:
        with self._lock:
            documents = self._table.all()
        return sorted((_to_user(doc) for doc in documents), key=lambda user: user.created_at)

    def get(self, user_id: UUID) -> User | None:
        with self._lock:
            document = self._table.get(Query().id == str(user_id))
        return _to_user(document) if document is not None else None

    def get_by_email(self, email: str) -> User | None:
        """`email` ya normalizado (minúsculas), como lo deja `schemas.Email`."""
        with self._lock:
            document = self._table.get(Query().email == email)
        return _to_user(document) if document is not None else None

    # --- Escritura ---------------------------------------------------------

    def insert(self, user: User) -> User:
        with self._lock:
            if self._table.contains(Query().email == user.email):
                raise EmailAlreadyRegisteredError()
            self._table.insert(user.model_dump(mode="json"))
        return user

    def update(self, user_id: UUID, changes: dict[str, Any]) -> User | None:
        """Aplica `changes` (valores ya serializables a JSON) y devuelve el resultado."""
        user = Query()
        with self._lock:
            if not self._table.contains(user.id == str(user_id)):
                return None
            new_email = changes.get("email")
            if new_email is not None and self._table.contains(
                (user.email == new_email) & (user.id != str(user_id))
            ):
                raise EmailAlreadyRegisteredError()
            self._table.update(changes, user.id == str(user_id))
            document = self._table.get(user.id == str(user_id))
        return _to_user(document)

    def delete(self, user_id: UUID) -> bool:
        with self._lock:
            removed = self._table.remove(Query().id == str(user_id))
        return bool(removed)


def _to_user(document: Document) -> User:
    return User.model_validate(dict(document))
