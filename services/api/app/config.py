"""Configuración de la API, leída del entorno una sola vez y validada al arrancar.

Ningún otro módulo lee `os.environ`. Si una variable trae un valor imposible,
el servicio no arranca: es mejor que falle el despliegue que la primera
petición de un usuario.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, Field, SecretStr, field_validator

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

# Fichero de TinyDB de usuarios y perfiles, junto al de proveedores. Los
# usuarios viven solo en TinyDB, también cuando llegue Postgres.
DEFAULT_USERS_DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "users.json"

# Ventana de validez del token. Corta a propósito: un JWT no se puede revocar,
# así que un token robado sirve hasta que caduca.
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HS256 firma con una clave de 256 bits. Un secreto más corto se puede
# adivinar por fuerza bruta a partir de un token cualquiera.
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseModel):
    cors_origins: list[str] = Field(min_length=1)
    max_upload_mb: int = Field(gt=0)
    suppliers_db_path: Path = DEFAULT_SUPPLIERS_DB_PATH
    users_db_path: Path = DEFAULT_USERS_DB_PATH
    # Opcional aquí porque el seeder también carga la configuración y no firma
    # tokens. La API no arranca sin él: ver `require_jwt_secret`.
    # SecretStr: si la configuración sale en un log o un traceback, se ve
    # '**********' y no el secreto.
    jwt_secret_key: SecretStr | None = None
    # Un día como máximo: más allá, un token robado da demasiado margen.
    access_token_expire_minutes: int = Field(default=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES, gt=0, le=1440)

    @field_validator("jwt_secret_key")
    @classmethod
    def long_enough(cls, secret: SecretStr | None) -> SecretStr | None:
        if secret is not None and len(secret.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(f"El secreto del JWT necesita al menos {MIN_JWT_SECRET_LENGTH} caracteres")
        return secret

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

    def require_jwt_secret(self) -> SecretStr:
        """El secreto de firma. Sin él, la API se niega a arrancar."""
        if self.jwt_secret_key is None:
            raise MissingJwtSecretError(
                "Falta NEXOVA_API_JWT_SECRET_KEY. Copia .env.example a .env, "
                "genera un secreto y arranca con `uv run --env-file .env uvicorn app.main:app`."
            )
        return self.jwt_secret_key


class MissingJwtSecretError(RuntimeError):
    """La API no puede firmar tokens: no hay secreto configurado."""


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    """Construye la configuración a partir de las variables de entorno.

    - `NEXOVA_API_CORS_ORIGINS`: orígenes permitidos, separados por comas.
    - `NEXOVA_API_MAX_UPLOAD_MB`: tamaño máximo del CSV subido, en MB.
    - `NEXOVA_API_SUPPLIERS_DB_PATH`: fichero JSON de TinyDB de proveedores.
    - `NEXOVA_API_USERS_DB_PATH`: fichero JSON de TinyDB de usuarios y perfiles.
    - `NEXOVA_API_JWT_SECRET_KEY`: secreto con el que se firman los tokens.
      Va en `.env`, nunca en el código.
    - `NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES`: minutos de validez del token.
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
        users_db_path=env.get("NEXOVA_API_USERS_DB_PATH") or DEFAULT_USERS_DB_PATH,
        # Vacía cuenta como ausente: es como viene en .env.example.
        jwt_secret_key=env.get("NEXOVA_API_JWT_SECRET_KEY") or None,
        access_token_expire_minutes=env.get(
            "NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES", DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )
