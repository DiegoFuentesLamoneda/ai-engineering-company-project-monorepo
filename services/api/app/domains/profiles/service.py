"""Reglas de los perfiles.

Un perfil siempre se busca por su usuario: no hay "el perfil 7", hay "el
perfil de Ana". El alta y el borrado los dispara el dominio de usuarios
(`POST /users` y `DELETE /users/{id}`); la edición, la propia persona
(`PUT /profiles/me`). No importa fastapi ni TinyDB.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from .database import ProfileRepository
from .exceptions import ProfileNotFoundError
from .schemas import Profile, ProfileFields, ProfileUpdate


def create_profile(repo: ProfileRepository, user_id: UUID, data: ProfileFields) -> Profile:
    profile = Profile(id=uuid4(), user_id=user_id, **data.model_dump())
    return repo.insert(profile)


def get_profile(repo: ProfileRepository, user_id: UUID) -> Profile:
    profile = repo.get_by_user(user_id)
    if profile is None:
        raise ProfileNotFoundError()
    return profile


def update_profile(repo: ProfileRepository, user_id: UUID, data: ProfileUpdate) -> Profile:
    """Cambia solo los campos enviados. Uno a `null` se borra."""
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        return get_profile(repo, user_id)
    profile = repo.update_by_user(user_id, changes)
    if profile is None:
        raise ProfileNotFoundError()
    return profile


def delete_profile(repo: ProfileRepository, user_id: UUID) -> bool:
    """Borra el perfil del usuario. `False` si no tenía, que no es un error."""
    return repo.delete_by_user(user_id)
