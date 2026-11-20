"""Configuración de la API, leída del entorno una sola vez y validada al arrancar.

Ningún otro módulo lee `os.environ`. Si una variable trae un valor imposible,
el servicio no arranca: es mejor que falle el despliegue que la primera
petición de un usuario.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

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

# Ficheros de TinyDB de usuarios y de perfiles, junto al de proveedores. Viven
# solo en TinyDB, también cuando llegue Postgres. Uno por dominio: cada
# repositorio tiene su fichero y su cerrojo, sin estado compartido.
DEFAULT_USERS_DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "users.json"
DEFAULT_PROFILES_DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "profiles.json"

# Fichero de TinyDB del gestor de incidencias: las incidencias y la tabla de
# idempotencia del seed. Relativo a services/api, como los demás: la API y
# scripts/seed_incidents.py tienen que abrir siempre el mismo fichero.
DEFAULT_INCIDENTS_DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "incidents.json"

# Ventana de validez del token. Corta a propósito: un JWT no se puede revocar,
# así que un token robado sirve hasta que caduca.
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# HS256 firma con una clave de 256 bits. Un secreto más corto se puede
# adivinar por fuerza bruta a partir de un token cualquiera.
MIN_JWT_SECRET_LENGTH = 32

# Fichero de TinyDB del restablecimiento de contraseña (AUTH-03): los tokens
# emitidos y el registro de auditoría, en dos tablas del mismo fichero.
DEFAULT_PASSWORD_RESETS_DB_PATH = Path(__file__).resolve().parents[1] / "storage" / "password_resets.json"

# Validez del enlace del email. El ticket pide entre 15 y 60 minutos: lo
# bastante para abrir el correo, lo bastante corto para que un enlace
# olvidado en una bandeja de entrada deje de servir pronto.
DEFAULT_RESET_TOKEN_EXPIRE_MINUTES = 30
MIN_RESET_TOKEN_EXPIRE_MINUTES = 15
MAX_RESET_TOKEN_EXPIRE_MINUTES = 60

# Enlaces de restablecimiento por cuenta y hora. Por encima, la API sigue
# respondiendo 200 pero no envía nada: así nadie usa el formulario para
# inundar el buzón de otra persona ni gastar la cuota del servicio de correo.
DEFAULT_RESET_REQUESTS_PER_HOUR = 3

# Adónde apunta el enlace del email: la página /reset-password del backoffice.
DEFAULT_FRONTEND_URL = "http://localhost:3000"

# Remitente de pruebas de Resend: funciona sin verificar un dominio propio,
# pero solo entrega al email con el que se creó la cuenta de Resend.
DEFAULT_EMAIL_FROM = "Nexova Solutions <onboarding@resend.dev>"


class Settings(BaseModel):
    # Si un valor no valida, el error dice qué variable falla pero no repite
    # el valor: un secreto del JWT demasiado corto no acaba en la consola ni
    # en el log del despliegue.
    model_config = ConfigDict(hide_input_in_errors=True)

    cors_origins: list[str] = Field(min_length=1)
    max_upload_mb: int = Field(gt=0)
    suppliers_db_path: Path = DEFAULT_SUPPLIERS_DB_PATH
    users_db_path: Path = DEFAULT_USERS_DB_PATH
    profiles_db_path: Path = DEFAULT_PROFILES_DB_PATH
    incidents_db_path: Path = DEFAULT_INCIDENTS_DB_PATH
    # Opcional aquí porque el seeder también carga la configuración y no firma
    # tokens. La API no arranca sin él: ver `require_jwt_secret`.
    # SecretStr: si la configuración sale en un log o un traceback, se ve
    # '**********' y no el secreto.
    jwt_secret_key: SecretStr | None = None
    # Un día como máximo: más allá, un token robado da demasiado margen.
    access_token_expire_minutes: int = Field(default=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES, gt=0, le=1440)
    password_resets_db_path: Path = DEFAULT_PASSWORD_RESETS_DB_PATH
    reset_token_expire_minutes: int = Field(
        default=DEFAULT_RESET_TOKEN_EXPIRE_MINUTES,
        ge=MIN_RESET_TOKEN_EXPIRE_MINUTES,
        le=MAX_RESET_TOKEN_EXPIRE_MINUTES,
    )
    reset_requests_per_hour: int = Field(default=DEFAULT_RESET_REQUESTS_PER_HOUR, gt=0, le=20)
    frontend_url: str = DEFAULT_FRONTEND_URL
    # Opcional: sin clave, el email no sale y el enlace se escribe en el log
    # de la API, para poder desarrollar y probar sin cuenta de Resend.
    resend_api_key: SecretStr | None = None
    email_from: str = Field(default=DEFAULT_EMAIL_FROM, min_length=3)

    @field_validator("frontend_url")
    @classmethod
    def http_url_without_trailing_slash(cls, url: str) -> str:
        # El enlace se construye como f"{frontend_url}/reset-password?token=…":
        # una barra final daría "//reset-password".
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise ValueError("La URL del frontend tiene que empezar por http:// o https://")
        return url

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
    - `NEXOVA_API_USERS_DB_PATH`: fichero JSON de TinyDB de usuarios.
    - `NEXOVA_API_PROFILES_DB_PATH`: fichero JSON de TinyDB de perfiles.
    - `NEXOVA_API_INCIDENTS_DB_PATH`: fichero JSON de TinyDB del gestor de
      incidencias.
    - `NEXOVA_API_JWT_SECRET_KEY`: secreto con el que se firman los tokens.
      Va en `.env`, nunca en el código.
    - `NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES`: minutos de validez del token.
    - `NEXOVA_API_PASSWORD_RESETS_DB_PATH`: fichero JSON de TinyDB de los
      restablecimientos de contraseña y su auditoría.
    - `NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES`: minutos de validez del enlace
      de restablecimiento (de 15 a 60).
    - `NEXOVA_API_RESET_REQUESTS_PER_HOUR`: enlaces por cuenta y hora.
    - `NEXOVA_API_FRONTEND_URL`: URL del backoffice, para el enlace del email.
    - `NEXOVA_API_RESEND_API_KEY`: API key de Resend. Va en `.env`, nunca en
      el código.
    - `NEXOVA_API_EMAIL_FROM`: remitente de los emails.
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
        profiles_db_path=env.get("NEXOVA_API_PROFILES_DB_PATH") or DEFAULT_PROFILES_DB_PATH,
        incidents_db_path=env.get("NEXOVA_API_INCIDENTS_DB_PATH") or DEFAULT_INCIDENTS_DB_PATH,
        # Vacía cuenta como ausente: es como viene en .env.example.
        jwt_secret_key=env.get("NEXOVA_API_JWT_SECRET_KEY") or None,
        access_token_expire_minutes=env.get(
            "NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES", DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        password_resets_db_path=env.get("NEXOVA_API_PASSWORD_RESETS_DB_PATH")
        or DEFAULT_PASSWORD_RESETS_DB_PATH,
        reset_token_expire_minutes=env.get(
            "NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES", DEFAULT_RESET_TOKEN_EXPIRE_MINUTES
        ),
        reset_requests_per_hour=env.get(
            "NEXOVA_API_RESET_REQUESTS_PER_HOUR", DEFAULT_RESET_REQUESTS_PER_HOUR
        ),
        frontend_url=env.get("NEXOVA_API_FRONTEND_URL") or DEFAULT_FRONTEND_URL,
        # Vacía cuenta como ausente, igual que el secreto del JWT.
        resend_api_key=env.get("NEXOVA_API_RESEND_API_KEY") or None,
        email_from=env.get("NEXOVA_API_EMAIL_FROM") or DEFAULT_EMAIL_FROM,
    )
