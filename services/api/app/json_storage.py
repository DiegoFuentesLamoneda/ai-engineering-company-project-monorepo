"""El almacenamiento JSON de TinyDB, con los fallos de disco traducidos.

Los cinco repositorios guardan en un fichero JSON. Si ese fichero se corrompe
(una escritura cortada a medias) o el sistema niega el acceso, `JSONStorage`
lanza `json.JSONDecodeError` u `OSError` desde dentro de TinyDB, y la API
acabaría en un 500 genérico que no distingue "el servidor tiene un bug" de
"la base de datos no se puede leer".

Se capturan aquí, en la única operación que toca el disco, y no con un
`try` alrededor de cada método de cada repositorio: así el ámbito es exacto
y ningún otro error queda tapado por error.
"""

from __future__ import annotations

import json
from typing import Any

from tinydb.storages import JSONStorage

from .errors import StorageUnavailableError


class SafeJSONStorage(JSONStorage):
    """`JSONStorage` que convierte los fallos de lectura y escritura en `StorageUnavailableError`."""

    def read(self) -> dict[str, dict[str, Any]] | None:
        try:
            return super().read()
        except (OSError, json.JSONDecodeError) as error:
            raise StorageUnavailableError(f"No se pudo leer {self._handle.name}") from error

    def write(self, data: dict[str, dict[str, Any]]) -> None:
        try:
            super().write(data)
        except OSError as error:
            raise StorageUnavailableError(f"No se pudo escribir {self._handle.name}") from error
