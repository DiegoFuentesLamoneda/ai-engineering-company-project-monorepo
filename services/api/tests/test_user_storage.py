"""Pruebas de la persistencia de usuarios y perfiles en TinyDB.

Cada prueba trabaja sobre ficheros temporales, nunca sobre storage/.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.domains.profiles.database import ProfileRepository
from app.domains.profiles.exceptions import ProfileAlreadyExistsError
from app.domains.profiles.schemas import Profile
from app.domains.users.database import UserRepository
from app.domains.users.exceptions import EmailAlreadyRegisteredError
from app.domains.users.schemas import Role, User

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)


def make_user(email: str = "ana@nexova.es", minutes: int = 0) -> User:
    return User(
        id=uuid4(),
        email=email,
        role=Role.USER,
        is_active=True,
        created_at=NOW + timedelta(minutes=minutes),
        hashed_password="$2b$12$hash",
    )


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # Una subcarpeta que no existe: el repositorio tiene que crearla.
        self.dir = Path(tmp.name) / "storage"

    def open_users(self) -> UserRepository:
        repo = UserRepository(self.dir / "users.json")
        self.addCleanup(repo.close)
        return repo

    def open_profiles(self) -> ProfileRepository:
        repo = ProfileRepository(self.dir / "profiles.json")
        self.addCleanup(repo.close)
        return repo


class UserRepositoryTests(TempDirTestCase):
    def test_insert_and_get_by_id(self):
        repo = self.open_users()
        user = repo.insert(make_user())
        self.assertEqual(repo.get(user.id), user)

    def test_get_unknown_id_returns_none(self):
        self.assertIsNone(self.open_users().get(uuid4()))

    def test_get_by_email(self):
        repo = self.open_users()
        user = repo.insert(make_user())
        self.assertEqual(repo.get_by_email("ana@nexova.es"), user)
        self.assertIsNone(repo.get_by_email("otra@nexova.es"))

    def test_duplicate_email_is_rejected(self):
        repo = self.open_users()
        repo.insert(make_user())
        with self.assertRaises(EmailAlreadyRegisteredError):
            repo.insert(make_user())
        self.assertEqual(len(repo.list()), 1)

    def test_list_is_sorted_by_creation(self):
        repo = self.open_users()
        later = repo.insert(make_user("luis@nexova.es", minutes=5))
        first = repo.insert(make_user("ana@nexova.es"))
        self.assertEqual([u.id for u in repo.list()], [first.id, later.id])

    def test_update_changes_only_given_fields(self):
        repo = self.open_users()
        user = repo.insert(make_user())
        updated = repo.update(user.id, {"role": "manager"})
        self.assertEqual(updated.role, Role.MANAGER)
        self.assertEqual(updated.email, user.email)

    def test_update_to_taken_email_is_rejected(self):
        repo = self.open_users()
        repo.insert(make_user("ana@nexova.es"))
        luis = repo.insert(make_user("luis@nexova.es"))
        with self.assertRaises(EmailAlreadyRegisteredError):
            repo.update(luis.id, {"email": "ana@nexova.es"})
        self.assertEqual(repo.get(luis.id).email, "luis@nexova.es")

    def test_update_keeping_own_email_is_allowed(self):
        repo = self.open_users()
        user = repo.insert(make_user())
        self.assertIsNotNone(repo.update(user.id, {"email": user.email}))

    def test_update_unknown_returns_none(self):
        self.assertIsNone(self.open_users().update(uuid4(), {"role": "admin"}))

    def test_delete(self):
        repo = self.open_users()
        user = repo.insert(make_user())
        self.assertTrue(repo.delete(user.id))
        self.assertIsNone(repo.get(user.id))
        self.assertFalse(repo.delete(user.id))

    def test_data_survives_reopening(self):
        repo = self.open_users()
        user = repo.insert(make_user())
        repo.close()
        self.assertEqual(self.open_users().get(user.id), user)

    def test_ids_are_not_reused_after_delete(self):
        # El motivo del UUID: con el número de TinyDB, el siguiente usuario
        # heredaría el ID del borrado y su token seguiría valiendo.
        repo = self.open_users()
        deleted = repo.insert(make_user("ana@nexova.es"))
        repo.delete(deleted.id)
        new = repo.insert(make_user("luis@nexova.es"))
        self.assertNotEqual(new.id, deleted.id)
        self.assertIsNone(repo.get(deleted.id))


class ProfileRepositoryTests(TempDirTestCase):
    def make_profile(self, user_id=None, **fields) -> Profile:
        return Profile(id=uuid4(), user_id=user_id or uuid4(), **fields)

    def test_insert_and_get_by_user(self):
        repo = self.open_profiles()
        profile = repo.insert(self.make_profile(name="Ana Pérez"))
        self.assertEqual(repo.get_by_user(profile.user_id), profile)

    def test_one_profile_per_user(self):
        repo = self.open_profiles()
        profile = repo.insert(self.make_profile())
        with self.assertRaises(ProfileAlreadyExistsError):
            repo.insert(self.make_profile(user_id=profile.user_id))

    def test_update_by_user(self):
        repo = self.open_profiles()
        profile = repo.insert(self.make_profile(name="Ana", phone="+34 600 123 456"))
        updated = repo.update_by_user(profile.user_id, {"phone": None, "address": "Valencia"})
        self.assertEqual(updated.name, "Ana")
        self.assertIsNone(updated.phone)
        self.assertEqual(updated.address, "Valencia")

    def test_update_unknown_user_returns_none(self):
        self.assertIsNone(self.open_profiles().update_by_user(uuid4(), {"name": "X"}))

    def test_delete_by_user(self):
        repo = self.open_profiles()
        profile = repo.insert(self.make_profile())
        self.assertTrue(repo.delete_by_user(profile.user_id))
        self.assertIsNone(repo.get_by_user(profile.user_id))
        self.assertFalse(repo.delete_by_user(profile.user_id))

    def test_accents_are_stored_readable(self):
        repo = self.open_profiles()
        repo.insert(self.make_profile(name="Begoña Martínez"))
        repo.close()
        text = (self.dir / "profiles.json").read_text(encoding="utf-8")
        self.assertIn("Begoña Martínez", text)


if __name__ == "__main__":
    unittest.main()
