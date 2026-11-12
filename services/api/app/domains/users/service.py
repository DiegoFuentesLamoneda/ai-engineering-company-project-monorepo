"""Reglas de los usuarios: alta, consulta, edición, borrado y contraseñas.

No importa fastapi ni TinyDB. Recibe modelos, habla con los repositorios y
lanza errores del dominio; el router los traduce a códigos HTTP.

Quién puede hacer qué también se decide aquí, porque es una regla de negocio
y no un detalle de HTTP. Las operaciones sobre un usuario concreto reciben a
quien llama (`caller`):

- Un usuario puede ver, editar y borrar **su propia** cuenta.
- Un `admin` puede hacerlo con cualquiera, y es el único que cambia roles.
- `manager` aún no tiene permisos propios: de momento es como `user`.

`now` es un parámetro para que las pruebas fijen la hora; en la API se queda
sin pasar y vale la hora actual en UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from passlib.hash import bcrypt

from ..profiles import service as profiles_service
from ..profiles.schemas import Profile, ProfileFields
from .database import UserRepository
from .exceptions import NotAllowedError, UserNotFoundError
from .schemas import Role, User, UserCreate, UserUpdate

if TYPE_CHECKING:
    # Solo para la anotación de tipos: el repositorio de perfiles se pasa
    # tal cual al service de perfiles, que es el único que lo usa.
    from ..profiles.database import ProfileRepository

# Hash de una contraseña cualquiera. Cuando el email no existe, el login
# verifica contra él igualmente: así tarda lo mismo que con un email real y
# nadie puede averiguar qué emails tienen cuenta midiendo el tiempo.
_DUMMY_HASH = "$2b$12$/NmFZcV8r8W1Qrtead.GAOkDlhP8N3scpGuZVIl2d4Gnqx33ZDwk2"

_PROFILE_FIELDS = set(ProfileFields.model_fields)


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _normalize_email(email: str) -> str:
    # El mismo criterio que `schemas.Email`, para quien llega con un texto
    # sin validar (el formulario de login).
    return email.strip().lower()


# --- Contraseñas -----------------------------------------------------------


def hash_password(password: str) -> str:
    """bcrypt con sal aleatoria: la misma contraseña da un hash distinto cada vez."""
    return bcrypt.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.verify(password, hashed_password)
    except ValueError:
        # Más de 72 bytes o un hash corrupto: no coincide, sin un 500.
        return False


def authenticate(repo: UserRepository, email: str, password: str) -> User | None:
    """El usuario si el email y la contraseña coinciden y la cuenta está activa.

    Devuelve `None` en cualquier otro caso, sin decir cuál: un mensaje de
    "ese email no existe" le diría a un atacante qué cuentas probar.
    """
    user = repo.get_by_email(_normalize_email(email))
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password) or not user.is_active:
        return None
    return user


# --- Permisos --------------------------------------------------------------


def _ensure_self_or_admin(caller: User, user_id: UUID) -> None:
    if caller.role is not Role.ADMIN and caller.id != user_id:
        raise NotAllowedError()


def ensure_admin(caller: User) -> None:
    if caller.role is not Role.ADMIN:
        raise NotAllowedError()


# --- Operaciones -----------------------------------------------------------


def create_user(
    users: UserRepository,
    profiles: ProfileRepository,
    data: UserCreate,
    role: Role = Role.USER,
    now: datetime | None = None,
) -> tuple[User, Profile]:
    """Da de alta la cuenta y su perfil en la misma operación.

    `role` no llega de la petición (`UserCreate` no lo admite); solo lo cambia
    `uv run create-admin`. TinyDB no tiene transacciones y son dos ficheros:
    si el perfil falla, se borra el usuario recién creado para no dejar una
    cuenta a medias.
    """
    user = User(
        id=uuid4(),
        email=data.email,
        hashed_password=hash_password(data.password),
        role=role,
        is_active=True,
        created_at=_now(now),
    )
    users.insert(user)
    try:
        profile = profiles_service.create_profile(
            profiles, user.id, ProfileFields(**data.model_dump(include=_PROFILE_FIELDS))
        )
    except Exception:
        users.delete(user.id)
        raise
    return user, profile


def list_users(repo: UserRepository, caller: User) -> list[User]:
    ensure_admin(caller)
    return repo.list()


def get_user(repo: UserRepository, user_id: UUID) -> User:
    """Sin comprobar permisos: lo usa la autenticación para cargar al usuario del token."""
    user = repo.get(user_id)
    if user is None:
        raise UserNotFoundError()
    return user


def get_user_for(repo: UserRepository, user_id: UUID, caller: User) -> User:
    """`GET /users/{id}`: tu propia cuenta, o cualquiera si eres admin."""
    _ensure_self_or_admin(caller, user_id)
    return get_user(repo, user_id)


def get_user_by_email(repo: UserRepository, email: str) -> User:
    user = repo.get_by_email(_normalize_email(email))
    if user is None:
        raise UserNotFoundError()
    return user


def update_user(repo: UserRepository, user_id: UUID, data: UserUpdate, caller: User) -> User:
    """Cambia los campos enviados. Ausente o `null`: se queda como estaba."""
    _ensure_self_or_admin(caller, user_id)
    changes = data.model_dump(exclude_none=True, mode="json")
    if "role" in changes:
        ensure_admin(caller)
    if "password" in changes:
        changes["hashed_password"] = hash_password(changes.pop("password"))
    if not changes:
        return get_user(repo, user_id)
    user = repo.update(user_id, changes)
    if user is None:
        raise UserNotFoundError()
    return user


def set_role(repo: UserRepository, user_id: UUID, role: Role) -> User:
    """Cambio de rol sin `caller`, para `uv run create-admin` (quien tiene la terminal)."""
    user = repo.update(user_id, {"role": role.value})
    if user is None:
        raise UserNotFoundError()
    return user


def delete_user(
    users: UserRepository, profiles: ProfileRepository, user_id: UUID, caller: User
) -> None:
    """Borra la cuenta y su perfil.

    Primero la cuenta: en cuanto desaparece nadie puede entrar con ella. Si
    después fallase el perfil, quedaría un perfil huérfano, que no da acceso
    a nada.
    """
    _ensure_self_or_admin(caller, user_id)
    if not users.delete(user_id):
        raise UserNotFoundError()
    profiles_service.delete_profile(profiles, user_id)
