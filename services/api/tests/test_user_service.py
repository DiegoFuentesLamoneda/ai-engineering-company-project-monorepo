"""Pruebas del service de usuarios, del de perfiles y de `create-admin`.

Cada prueba trabaja sobre ficheros temporales, nunca sobre storage/.
bcrypt es lento a propósito (~0,2 s por hash), así que estas pruebas tardan
unos segundos. Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

from pydantic import ValidationError

from app.create_admin import create_or_promote_admin
from app.domains.profiles import service as profiles_service
from app.domains.profiles.database import ProfileRepository
from app.domains.profiles.exceptions import ProfileNotFoundError
from app.domains.profiles.schemas import ProfileUpdate
from app.domains.users import service
from app.domains.users.database import UserRepository
from app.domains.users.exceptions import (
    EmailAlreadyRegisteredError,
    NotAllowedError,
    UserNotFoundError,
)
from app.domains.users.schemas import Role, UserCreate, UserUpdate

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
PASSWORD = "contraseña-segura"


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name) / "storage"
        self.users = UserRepository(directory / "users.json")
        self.addCleanup(self.users.close)
        self.profiles = ProfileRepository(directory / "profiles.json")
        self.addCleanup(self.profiles.close)

    def signup(self, email="ana@nexova.es", role=Role.USER, **profile):
        data = UserCreate(email=email, password=PASSWORD, **profile)
        user, _ = service.create_user(self.users, self.profiles, data, role=role, now=NOW)
        return user


class PasswordTests(unittest.TestCase):
    def test_hash_is_not_the_password_and_verifies(self):
        hashed = service.hash_password(PASSWORD)
        self.assertNotIn(PASSWORD, hashed)
        self.assertTrue(service.verify_password(PASSWORD, hashed))
        self.assertFalse(service.verify_password("otra-contraseña", hashed))

    def test_same_password_gives_different_hashes(self):
        # La sal: dos personas con la misma contraseña no tienen el mismo hash.
        self.assertNotEqual(service.hash_password(PASSWORD), service.hash_password(PASSWORD))

    def test_broken_hash_does_not_crash(self):
        self.assertFalse(service.verify_password(PASSWORD, "no-es-un-hash"))


class CreateUserTests(ServiceTestCase):
    def test_signup_creates_user_and_profile(self):
        data = UserCreate(email="Ana@Nexova.es", password=PASSWORD, name="Ana Pérez")
        user, profile = service.create_user(self.users, self.profiles, data, now=NOW)
        self.assertEqual(user.email, "ana@nexova.es")
        self.assertEqual(user.role, Role.USER)
        self.assertTrue(user.is_active)
        self.assertEqual(user.created_at, NOW)
        self.assertEqual(profile.user_id, user.id)
        self.assertEqual(profile.name, "Ana Pérez")
        self.assertIsNone(profile.phone)

    def test_password_is_stored_hashed(self):
        user = self.signup()
        stored = self.users.get(user.id)
        self.assertNotEqual(stored.hashed_password, PASSWORD)
        self.assertTrue(service.verify_password(PASSWORD, stored.hashed_password))

    def test_signup_without_profile_fields_still_creates_profile(self):
        user = self.signup()
        self.assertIsNotNone(self.profiles.get_by_user(user.id))

    def test_duplicate_email_is_rejected(self):
        self.signup()
        with self.assertRaises(EmailAlreadyRegisteredError):
            self.signup(email="ANA@nexova.es")

    def test_failed_profile_rolls_back_the_user(self):
        # Sin transacciones en TinyDB: si el perfil falla, la cuenta no se queda.
        with mock.patch.object(self.profiles, "insert", side_effect=OSError("disco lleno")):
            with self.assertRaises(OSError):
                self.signup()
        self.assertEqual(self.users.list(), [])


class AuthenticateTests(ServiceTestCase):
    def test_right_credentials(self):
        user = self.signup()
        self.assertEqual(service.authenticate(self.users, " ANA@nexova.es", PASSWORD), user)

    def test_wrong_password_or_unknown_email(self):
        self.signup()
        self.assertIsNone(service.authenticate(self.users, "ana@nexova.es", "otra-contraseña"))
        self.assertIsNone(service.authenticate(self.users, "nadie@nexova.es", PASSWORD))

    def test_inactive_account_cannot_log_in(self):
        user = self.signup()
        self.users.update(user.id, {"is_active": False})
        self.assertIsNone(service.authenticate(self.users, "ana@nexova.es", PASSWORD))


class PermissionTests(ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.ana = self.signup("ana@nexova.es")
        self.luis = self.signup("luis@nexova.es")
        self.admin = self.signup("admin@nexova.es", role=Role.ADMIN)

    def test_only_admin_lists_users(self):
        self.assertEqual(len(service.list_users(self.users, self.admin)), 3)
        with self.assertRaises(NotAllowedError):
            service.list_users(self.users, self.ana)

    def test_get_own_or_as_admin(self):
        self.assertEqual(service.get_user_for(self.users, self.ana.id, self.ana).id, self.ana.id)
        self.assertEqual(service.get_user_for(self.users, self.ana.id, self.admin).id, self.ana.id)
        with self.assertRaises(NotAllowedError):
            service.get_user_for(self.users, self.ana.id, self.luis)

    def test_forbidden_comes_before_not_found(self):
        # Un 404 a quien no es admin le confirmaría qué IDs existen.
        with self.assertRaises(NotAllowedError):
            service.get_user_for(self.users, uuid4(), self.ana)
        with self.assertRaises(UserNotFoundError):
            service.get_user_for(self.users, uuid4(), self.admin)

    def test_user_updates_own_email_and_password(self):
        data = UserUpdate(email="ana.perez@nexova.es", password="nueva-contraseña")
        updated = service.update_user(self.users, self.ana.id, data, self.ana)
        self.assertEqual(updated.email, "ana.perez@nexova.es")
        self.assertIsNotNone(service.authenticate(self.users, "ana.perez@nexova.es", "nueva-contraseña"))

    def test_user_cannot_update_someone_else(self):
        with self.assertRaises(NotAllowedError):
            service.update_user(self.users, self.luis.id, UserUpdate(email="x@nexova.es"), self.ana)

    def test_only_admin_changes_roles(self):
        with self.assertRaises(NotAllowedError):
            service.update_user(self.users, self.ana.id, UserUpdate(role=Role.ADMIN), self.ana)
        self.assertEqual(self.users.get(self.ana.id).role, Role.USER)
        updated = service.update_user(self.users, self.ana.id, UserUpdate(role=Role.MANAGER), self.admin)
        self.assertEqual(updated.role, Role.MANAGER)

    def test_null_fields_are_ignored(self):
        updated = service.update_user(self.users, self.ana.id, UserUpdate(email=None), self.ana)
        self.assertEqual(updated.email, "ana@nexova.es")

    def test_delete_removes_user_and_profile(self):
        service.delete_user(self.users, self.profiles, self.ana.id, self.ana)
        self.assertIsNone(self.users.get(self.ana.id))
        self.assertIsNone(self.profiles.get_by_user(self.ana.id))

    def test_user_cannot_delete_someone_else(self):
        with self.assertRaises(NotAllowedError):
            service.delete_user(self.users, self.profiles, self.luis.id, self.ana)
        self.assertIsNotNone(self.users.get(self.luis.id))

    def test_admin_deletes_anyone_and_unknown_is_not_found(self):
        service.delete_user(self.users, self.profiles, self.luis.id, self.admin)
        with self.assertRaises(UserNotFoundError):
            service.delete_user(self.users, self.profiles, self.luis.id, self.admin)


class ProfileServiceTests(ServiceTestCase):
    def test_update_only_sent_fields(self):
        user = self.signup(name="Ana", phone="+34 600 123 456")
        profile = profiles_service.update_profile(
            self.profiles, user.id, ProfileUpdate(address="Calle Colón 1, Valencia")
        )
        self.assertEqual(profile.name, "Ana")
        self.assertEqual(profile.phone, "+34 600 123 456")
        self.assertEqual(profile.address, "Calle Colón 1, Valencia")

    def test_null_clears_a_field(self):
        user = self.signup(phone="+34 600 123 456")
        profile = profiles_service.update_profile(self.profiles, user.id, ProfileUpdate(phone=None))
        self.assertIsNone(profile.phone)

    def test_missing_profile(self):
        with self.assertRaises(ProfileNotFoundError):
            profiles_service.get_profile(self.profiles, uuid4())


class CreateAdminTests(ServiceTestCase):
    def test_creates_admin_when_email_is_new(self):
        outcome, user = create_or_promote_admin(self.users, self.profiles, "Jefa@Nexova.es", lambda: PASSWORD)
        self.assertEqual(outcome, "created")
        self.assertEqual(user.role, Role.ADMIN)
        self.assertEqual(user.email, "jefa@nexova.es")
        self.assertIsNotNone(self.profiles.get_by_user(user.id))

    def test_promotes_existing_account_without_asking_password(self):
        ana = self.signup()
        ask = mock.Mock(return_value="no-se-usa")
        outcome, user = create_or_promote_admin(self.users, self.profiles, "ana@nexova.es", ask)
        self.assertEqual(outcome, "promoted")
        self.assertEqual(user.id, ana.id)
        self.assertEqual(user.role, Role.ADMIN)
        ask.assert_not_called()
        # La contraseña de siempre sigue valiendo.
        self.assertIsNotNone(service.authenticate(self.users, "ana@nexova.es", PASSWORD))

    def test_existing_admin_is_left_alone(self):
        self.signup(role=Role.ADMIN)
        outcome, _ = create_or_promote_admin(self.users, self.profiles, "ana@nexova.es", lambda: PASSWORD)
        self.assertEqual(outcome, "already_admin")

    def test_bad_email_fails_before_asking_password(self):
        ask = mock.Mock(return_value=PASSWORD)
        with self.assertRaises(ValidationError):
            create_or_promote_admin(self.users, self.profiles, "jefa", ask)
        ask.assert_not_called()

    def test_weak_password_creates_nothing(self):
        with self.assertRaises(ValidationError):
            create_or_promote_admin(self.users, self.profiles, "jefa@nexova.es", lambda: "corta")
        self.assertEqual(self.users.list(), [])


if __name__ == "__main__":
    unittest.main()
