"""Configuración de la API, leída del entorno una sola vez y validada al arrancar.

Ningún otro módulo lee `os.environ`. Si una variable trae un valor imposible,
el servicio no arranca: es mejor que falle el despliegue que la primera
petición de un usuario.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# Desarrollo: el backoffice en :3000. localhost y 127.0.0.1 son orígenes
# distintos para el navegador aunque apunten a la misma máquina, así que van
# los dos (ver memory-bank/techContext.md, "Restricciones técnicas").
DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")

# La exportación de producción puede llegar al millón de filas (~150 MB).
DEFAULT_MAX_UPLOAD_MB = 200

# Fichero de TinyDB del directorio de proveedores. Relativo a services/api y
# no a la carpeta desde la que se lanza el comando: la API y el seeder
# tienen que abrir siempre el mismo fichero.
DEFAULT_SUPPLIERS_DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "suppliers.json"


class Settings(BaseModel):
    cors_origins: list[str] = Field(min_length=1)
    max_upload_mb: int = Field(gt=0)
    suppliers_db_path: Path = DEFAULT_SUPPLIERS_DB_PATH

    @field_validator("cors_origins")
    @classmethod
    def no_wildcard(cls, origins: list[str]) -> list[str]:
        # Un comodín abriría la API a cualquier web, y además es incompatible
        # con allow_credentials, que llegará con la autenticación.
        if "*" in origins:
            raise ValueError("CORS necesita una lista explícita de orígenes, no '*'")
        return origins

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    """Construye la configuración a partir de las variables de entorno.

    - `NEXOVA_API_CORS_ORIGINS`: orígenes permitidos, separados por comas.
    - `NEXOVA_API_MAX_UPLOAD_MB`: tamaño máximo del CSV subido, en MB.
    - `NEXOVA_API_SUPPLIERS_DB_PATH`: fichero JSON de TinyDB de proveedores.
    """
    raw_origins = env.get("NEXOVA_API_CORS_ORIGINS")
    origins = (
        [o.strip() for o in raw_origins.split(",") if o.strip()]
        if raw_origins
        else list(DEFAULT_CORS_ORIGINS)
    )
    return Settings(
        cors_origins=origins,
        max_upload_mb=env.get("NEXOVA_API_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB),
        suppliers_db_path=env.get("NEXOVA_API_SUPPLIERS_DB_PATH") or DEFAULT_SUPPLIERS_DB_PATH,
    )
