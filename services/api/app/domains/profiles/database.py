"""Persistencia de los perfiles sobre TinyDB.

Como los usuarios, los perfiles viven solo en TinyDB. Cada perfil apunta a su
usuario por `user_id` y solo puede haber uno por usuario: el vínculo es uno a
uno. Este módulo es el único que conoce TinyDB.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any
from uuid import UUID

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.table import Document

from .exceptions import ProfileAlreadyExistsError
from .schemas import Profile

TABLE = "profiles"


class ProfileRepository:
    """Lectura y escritura de perfiles en un fichero de TinyDB.

    Se busca siempre por `user_id`: nadie pide un perfil por su propio ID,
    sino el perfil de un usuario. El cerrojo garantiza el uno a uno: la
    comprobación y la escritura van juntas.
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

    def __enter__(self) -> ProfileRepository:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def get_by_user(self, user_id: UUID) -> Profile | None:
        with self._lock:
            document = self._table.get(Query().user_id == str(user_id))
        return _to_profile(document) if document is not None else None

    def insert(self, profile: Profile) -> Profile:
        with self._lock:
            if self._table.contains(Query().user_id == str(profile.user_id)):
                raise ProfileAlreadyExistsError()
            self._table.insert(profile.model_dump(mode="json"))
        return profile

    def update_by_user(self, user_id: UUID, changes: dict[str, Any]) -> Profile | None:
        """Aplica `changes` (valores ya serializables a JSON) y devuelve el resultado."""
        condition = Query().user_id == str(user_id)
        with self._lock:
            if not self._table.contains(condition):
                return None
            self._table.update(changes, condition)
            document = self._table.get(condition)
        return _to_profile(document)

    def delete_by_user(self, user_id: UUID) -> bool:
        with self._lock:
            removed = self._table.remove(Query().user_id == str(user_id))
        return bool(removed)


def _to_profile(document: Document) -> Profile:
    return Profile.model_validate(dict(document))
