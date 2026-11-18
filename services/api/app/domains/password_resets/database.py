"""Persistencia de los tokens de restablecimiento y su auditoría sobre TinyDB.

Único módulo del dominio que conoce TinyDB. El resto trabaja con
`ResetToken` y `AuditEntry`. Dos tablas en el mismo fichero.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from uuid import UUID

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage
from tinydb.table import Document

from .schemas import AuditEntry, AuditEvent, ResetToken

TOKENS_TABLE = "tokens"
AUDIT_TABLE = "audit"


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
        self._audit = self._db.table(AUDIT_TABLE)
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

    # --- Auditoría ---------------------------------------------------------

    def list_audit(self, user_id: UUID | None = None) -> list[AuditEntry]:
        """Las entradas, de la más antigua a la más nueva. Con `user_id`, solo las suyas."""
        with self._lock:
            if user_id is None:
                documents = self._audit.all()
            else:
                documents = self._audit.search(Query().user_id == str(user_id))
        return sorted((_to_entry(doc) for doc in documents), key=lambda entry: entry.created_at)

    def insert_audit(self, entry: AuditEntry, purge_before: datetime) -> None:
        """Anota `entry` y borra las entradas anteriores a `purge_before` (la retención)."""
        with self._lock:
            self._purge_audit(purge_before)
            self._audit.insert(entry.model_dump(mode="json"))

    def insert_audit_if_under_limit(
        self,
        entry: AuditEntry,
        since: datetime,
        limit: int,
        purge_before: datetime,
    ) -> bool:
        """Anota `entry` solo si su cuenta tiene menos de `limit` iguales desde `since`.

        Es el *rate limiting*: el propio registro hace de contador. Contar y
        anotar ocurren dentro del mismo cerrojo; si no, dos peticiones a la
        vez contarían las dos "2 de 3" y pasarían las dos.
        """
        with self._lock:
            self._purge_audit(purge_before)
            if self._count(entry.user_id, [entry.event], since) >= limit:
                return False
            self._audit.insert(entry.model_dump(mode="json"))
            return True

    # Llamar con el cerrojo ya tomado.
    def _count(self, user_id: UUID | None, events: Iterable[AuditEvent], since: datetime) -> int:
        line = Query()
        wanted = {str(event) for event in events}
        return self._audit.count(
            (line.user_id == (str(user_id) if user_id else None))
            & line.event.one_of(list(wanted))
            & line.created_at.test(lambda value: datetime.fromisoformat(value) >= since)
        )

    # Llamar con el cerrojo ya tomado.
    def _purge_audit(self, before: datetime) -> None:
        self._audit.remove(
            Query().created_at.test(lambda value: datetime.fromisoformat(value) < before)
        )


def _to_token(document: Document) -> ResetToken:
    return ResetToken.model_validate(dict(document))


def _to_entry(document: Document) -> AuditEntry:
    return AuditEntry.model_validate(dict(document))
