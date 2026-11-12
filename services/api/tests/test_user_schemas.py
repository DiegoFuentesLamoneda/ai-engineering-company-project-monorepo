"""Pruebas de los modelos de usuarios y perfiles.

Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.domains.profiles.schemas import ProfileUpdate
from app.domains.users.schemas import (
    MAX_PASSWORD_BYTES,
    Role,
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
)

VALID = {"email": "ana@nexova.es", "password": "contraseña-segura"}


class RoleTests(unittest.TestCase):
    def test_only_three_roles(self):
        self.assertEqual({role.value for role in Role}, {"admin", "manager", "user"})

    def test_unknown_role_is_rejected(self):
        with self.assertRaises(ValidationError):
            UserUpdate(role="superadmin")


class UserCreateTests(unittest.TestCase):
    def test_minimal_signup(self):
        user = UserCreate(**VALID)
        self.assertEqual(user.email, "ana@nexova.es")
        self.assertIsNone(user.name)

    def test_signup_with_profile_fields(self):
        user = UserCreate(**VALID, name="Ana Pérez", phone="+34 600 123 456", address="Valencia")
        self.assertEqual(user.name, "Ana Pérez")

    def test_role_in_signup_is_rejected(self):
        # Nadie se registra como admin: el campo ni siquiera existe en el alta.
        with self.assertRaises(ValidationError):
            UserCreate(**VALID, role="admin")

    def test_email_is_normalized(self):
        user = UserCreate(email="  Ana@Nexova.ES ", password=VALID["password"])
        self.assertEqual(user.email, "ana@nexova.es")

    def test_malformed_email_is_rejected(self):
        for email in ("ana", "ana@nexova", "ana @nexova.es", "@nexova.es"):
            with self.subTest(email=email), self.assertRaises(ValidationError):
                UserCreate(email=email, password=VALID["password"])

    def test_short_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            UserCreate(email=VALID["email"], password="corta")

    def test_password_limit_is_in_bytes(self):
        UserCreate(email=VALID["email"], password="a" * MAX_PASSWORD_BYTES)
        with self.assertRaises(ValidationError):
            UserCreate(email=VALID["email"], password="a" * (MAX_PASSWORD_BYTES + 1))
        # 40 eñes son 40 caracteres pero 80 bytes: bcrypt no las admite.
        with self.assertRaises(ValidationError):
            UserCreate(email=VALID["email"], password="ñ" * 40)

    def test_malformed_phone_is_rejected(self):
        with self.assertRaises(ValidationError):
            UserCreate(**VALID, phone="llámame")


class UserOutputTests(unittest.TestCase):
    def test_public_model_has_no_hash(self):
        self.assertNotIn("hashed_password", UserPublic.model_fields)

    def test_stored_user_filtered_through_public_model(self):
        stored = User(
            id=uuid4(),
            email="ana@nexova.es",
            role=Role.USER,
            is_active=True,
            created_at=datetime(2026, 11, 12, tzinfo=timezone.utc),
            hashed_password="$2b$12$hash",
        )
        public = UserPublic.model_validate(stored.model_dump())
        self.assertNotIn("hashed_password", public.model_dump())


class ProfileUpdateTests(unittest.TestCase):
    def test_only_sent_fields_are_set(self):
        update = ProfileUpdate(phone=None)
        self.assertEqual(update.model_dump(exclude_unset=True), {"phone": None})

    def test_unknown_field_is_rejected(self):
        with self.assertRaises(ValidationError):
            ProfileUpdate(user_id=str(uuid4()))

    def test_blank_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            ProfileUpdate(name="   ")


if __name__ == "__main__":
    unittest.main()
