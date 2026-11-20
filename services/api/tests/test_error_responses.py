"""Pruebas de las respuestas de error de la API (auditoría de gestión de errores).

- B1: el 422 de validación no repite lo que envió el usuario.
- B6: un fichero de TinyDB ilegible es un 503 con mensaje propio, no un 500.

Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from pydantic import SecretStr
from tinydb.storages import JSONStorage

from app.config import Settings
from app.domains.auth.security import create_access_token
from app.domains.incidents.database import IncidentRepository
from app.domains.password_resets.database import PasswordResetRepository
from app.domains.profiles.database import ProfileRepository
from app.domains.suppliers.database import SupplierRepository
from app.domains.users import service as users_service
from app.domains.users.database import UserRepository
from app.domains.users.schemas import UserCreate
from app.errors import STORAGE_UNAVAILABLE, StorageUnavailableError
from app.mailer import LogMailer
from app.main import create_app
from app.seed import seed_suppliers
from http_client import request

SECRET = SecretStr("s" * 40)
ORIGIN = "http://localhost:3000"
SEEDED_AT = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)


class ErrorResponsesTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name)
        self.suppliers_path = directory / "suppliers.json"
        self.suppliers = SupplierRepository(self.suppliers_path)
        self.addCleanup(self.suppliers.close)
        seed_suppliers(self.suppliers, now=SEEDED_AT)
        self.users = UserRepository(directory / "users.json")
        self.addCleanup(self.users.close)
        self.profiles = ProfileRepository(directory / "profiles.json")
        self.addCleanup(self.profiles.close)
        self.resets = PasswordResetRepository(directory / "password_resets.json")
        self.addCleanup(self.resets.close)
        self.incidents = IncidentRepository(directory / "incidents.json")
        self.addCleanup(self.incidents.close)

        settings = Settings(cors_origins=[ORIGIN], max_upload_mb=10, jwt_secret_key=SECRET)
        self.app = create_app(settings)
        self.app.state.suppliers = self.suppliers
        self.app.state.users = self.users
        self.app.state.profiles = self.profiles
        self.app.state.password_resets = self.resets
        self.app.state.incidents = self.incidents
        self.app.state.mailer = LogMailer()

        ana, _ = users_service.create_user(
            self.users, self.profiles, UserCreate(email="ana@nexova.es", password="contraseña-segura")
        )
        self.token = create_access_token(ana.id, SECRET, 30)

    def call(self, method, path, **kwargs):
        return request(self.app, method, path, **kwargs)


class ValidationErrorTests(ErrorResponsesTestCase):
    """B1: el 422 de siempre, sin el campo `input`."""

    TOKEN = "token-de-restablecimiento-que-no-debe-volver"
    PASSWORD = "corta"

    def reset_with_short_password(self):
        return self.call(
            "POST",
            "/auth/reset-password",
            json_body={"token": self.TOKEN, "new_password": self.PASSWORD},
        )

    def test_is_still_a_422_with_a_list_in_detail(self):
        response = self.reset_with_short_password()
        self.assertEqual(response.status_code, 422)
        errors = response.json()["detail"]
        self.assertIsInstance(errors, list)
        self.assertEqual(errors[0]["loc"], ["body", "new_password"])
        self.assertIn("msg", errors[0])
        self.assertIn("type", errors[0])

    def test_never_echoes_what_was_sent(self):
        response = self.reset_with_short_password()
        body = response.body.decode("utf-8")
        self.assertNotIn(self.TOKEN, body)
        self.assertNotIn(self.PASSWORD, body)
        for error in response.json()["detail"]:
            self.assertEqual(set(error), {"loc", "msg", "type"})

    def test_broken_json_is_a_422_too(self):
        response = request(
            self.app, "POST", "/auth/reset-password", headers={"content-type": "application/json"}
        )
        self.assertEqual(response.status_code, 422)

    def test_incident_manager_keeps_its_own_400(self):
        response = self.call("POST", "/api/incidents", json_body={}, token=self.token)
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())


class StorageUnavailableTests(ErrorResponsesTestCase):
    """B6: un fichero corrupto o que no se puede escribir es un 503."""

    def corrupt_suppliers_file(self):
        self.suppliers_path.write_text("{ esto no es JSON", encoding="utf-8")

    def test_corrupt_file_is_a_503_with_a_clean_message(self):
        self.corrupt_suppliers_file()
        with self.assertLogs("nexova.errors", level="ERROR") as logs:
            response = self.call("GET", "/suppliers", token=self.token)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": STORAGE_UNAVAILABLE})
        # El detalle va al log del servidor, no a la respuesta.
        self.assertIn("JSONDecodeError", "\n".join(logs.output))
        self.assertNotIn("suppliers.json", response.body.decode("utf-8"))

    def test_the_503_carries_cors_headers(self):
        self.corrupt_suppliers_file()
        with self.assertLogs("nexova.errors", level="ERROR"):
            response = self.call("GET", "/suppliers", token=self.token, headers={"origin": ORIGIN})
        self.assertEqual(response.headers.get("access-control-allow-origin"), ORIGIN)

    def test_a_failed_write_is_a_503_too(self):
        with (
            mock.patch.object(JSONStorage, "write", side_effect=PermissionError("sin permisos")),
            self.assertLogs("nexova.errors", level="ERROR"),
        ):
            response = self.call("DELETE", "/suppliers/1", token=self.token)
        self.assertEqual(response.status_code, 503)

    def test_the_repository_raises_its_own_error(self):
        self.corrupt_suppliers_file()
        with self.assertRaises(StorageUnavailableError):
            self.suppliers.get(1)


if __name__ == "__main__":
    unittest.main()
