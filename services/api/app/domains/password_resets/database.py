"""Persistencia de los tokens de restablecimiento sobre TinyDB.

Único módulo del dominio que conoce TinyDB. El resto trabaja con `ResetToken`.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from uuid import UUID

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.table import Document

from .schemas import ResetToken

TOKENS_TABLE = "tokens"


class PasswordResetRepository:
    """Lectura y escritura de tokens de restablecimiento en un fichero de TinyDB.

    Como en usuarios, un cerrojo pone las operaciones en fila: FastAPI
    ejecuta las rutas síncronas en varios hilos y TinyDB no está pensado
    para eso.
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
        self._tokens = self._db.table(TOKENS_TABLE)
        self._lock = threading.Lock()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> PasswordResetRepository:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # --- Lectura -----------------------------------------------------------

    def get_by_hash(self, token_hash: str) -> ResetToken | None:
        with self._lock:
            document = self._tokens.get(Query().token_hash == token_hash)
        return _to_token(document) if document is not None else None

    def list_for_user(self, user_id: UUID) -> list[ResetToken]:
        with self._lock:
            documents = self._tokens.search(Query().user_id == str(user_id))
        return sorted((_to_token(doc) for doc in documents), key=lambda token: token.created_at)

    # --- Escritura ---------------------------------------------------------

    def insert(self, token: ResetToken) -> ResetToken:
        with self._lock:
            self._tokens.insert(token.model_dump(mode="json"))
        return token

    def mark_used(self, token_id: UUID, used_at: datetime) -> bool:
        """Marca el token como usado **solo si no lo estaba**. `False` si ya lo estaba.

        Comprobar y marcar ocurren dentro del mismo cerrojo. Si dos
        peticiones llegan a la vez con el mismo enlace, solo una gana: la
        otra recibe `False` y no cambia la contraseña.
        """
        token = Query()
        condition = (token.id == str(token_id)) & (token.used_at == None)  # noqa: E711 (sintaxis de TinyDB)
        with self._lock:
            updated = self._tokens.update({"used_at": used_at.isoformat()}, condition)
        return bool(updated)

    def delete_pending_for_user(self, user_id: UUID) -> int:
        """Borra los tokens sin usar de un usuario. Devuelve cuántos."""
        token = Query()
        with self._lock:
            removed = self._tokens.remove((token.user_id == str(user_id)) & (token.used_at == None))  # noqa: E711
        return len(removed)

    def delete_expired(self, now: datetime) -> int:
        """Limpieza: los tokens caducados ya no sirven para nada. Devuelve cuántos."""
        with self._lock:
            removed = self._tokens.remove(
                Query().expires_at.test(lambda value: datetime.fromisoformat(value) <= now)
            )
        return len(removed)


def _to_token(document: Document) -> ResetToken:
    return ResetToken.model_validate(dict(document))
