"""Crea el primer admin, o asciende a admin una cuenta que ya existe.

Desde services/api:
    uv run create-admin

Pide el email y, si la cuenta es nueva, la contraseña dos veces sin mostrarla
en pantalla. Si el email ya tiene cuenta, la asciende a admin y no toca su
contraseña.

Existe porque `POST /users` crea siempre cuentas `user` y solo un admin puede
cambiar roles: sin este comando, el primer admin no podría existir. Quien
tiene acceso a la terminal del servidor ya tiene acceso a todo, así que no
pide más permiso.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from getpass import getpass
from typing import Literal

from pydantic import TypeAdapter, ValidationError

from app.config import load_settings
from app.domains.profiles.database import ProfileRepository
from app.domains.users import service
from app.domains.users.database import UserRepository
from app.domains.users.exceptions import UserNotFoundError
from app.domains.users.schemas import Email, Role, User, UserCreate

Outcome = Literal["created", "promoted", "already_admin"]


def create_or_promote_admin(
    users: UserRepository,
    profiles: ProfileRepository,
    email: str,
    ask_password: Callable[[], str],
) -> tuple[Outcome, User]:
    """`ask_password` solo se llama si hay que crear la cuenta."""
    # El email se valida antes de pedir nada más: no tiene sentido teclear
    # la contraseña dos veces para que luego falle el email.
    email = TypeAdapter(Email).validate_python(email)
    try:
        existing = service.get_user_by_email(users, email)
    except UserNotFoundError:
        # Mismas reglas que `POST /users`: email válido, contraseña de 8
        # caracteres a 72 bytes. Lanza `ValidationError` si no las cumple.
        data = UserCreate(email=email, password=ask_password())
        user, _profile = service.create_user(users, profiles, data, role=Role.ADMIN)
        return "created", user
    if existing.role is Role.ADMIN:
        return "already_admin", existing
    return "promoted", service.set_role(users, existing.id, Role.ADMIN)


def _ask_password() -> str:
    password = getpass("Contraseña (no se muestra): ")
    if getpass("Repítela: ") != password:
        raise SystemExit("Las contraseñas no coinciden. No se ha creado nada.")
    return password


def main() -> None:
    # En Windows, la salida redirigida usa la codificación antigua del sistema.
    # stderr también: ahí van los errores (`SystemExit`), con sus tildes.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    settings = load_settings()
    email = input("Email del admin: ")
    with (
        UserRepository(settings.users_db_path) as users,
        ProfileRepository(settings.profiles_db_path) as profiles,
    ):
        try:
            outcome, user = create_or_promote_admin(users, profiles, email, _ask_password)
        except ValidationError as error:
            # Solo los mensajes: el error completo repetiría la contraseña.
            # Sin `loc` es el email, que se valida suelto, fuera del modelo.
            reasons = "; ".join(
                f"{'.'.join(map(str, e['loc'])) or 'email'}: {e['msg']}" for e in error.errors()
            )
            raise SystemExit(f"Datos no válidos ({reasons}). No se ha creado nada.") from None
    messages = {
        "created": "Cuenta admin creada.",
        "promoted": "La cuenta ya existía: ahora es admin. Su contraseña no cambia.",
        "already_admin": "Esa cuenta ya era admin. No se ha cambiado nada.",
    }
    print(messages[outcome])
    print(f"ID: {user.id}")


if __name__ == "__main__":
    main()
