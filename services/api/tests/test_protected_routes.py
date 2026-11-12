"""Pruebas HTTP del candado en las rutas que ya existían: incidencias y proveedores.

Cada ruta, sin token, responde 401 y no toca nada. Con un token válido se
comporta igual que antes de tener candado. Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pydantic import SecretStr

from app.config import Settings
from app.domains.auth.security import create_access_token
from app.domains.profiles.database import ProfileRepository
from app.domains.suppliers.database import SupplierRepository
from app.domains.users import service as users_service
from app.domains.users.database import UserRepository
from app.domains.users.schemas import UserCreate
from app.main import create_app
from app.seed import seed_suppliers
from http_client import request

SECRET = SecretStr("s" * 40)
SEEDED_AT = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
MISSING_ID = 999

# Las 8 rutas que existían antes de la autenticación, con un cuerpo válido.
PROTECTED = [
    ("POST", "/api/incidents/analyze", None),
    ("GET", "/api/incidents/results/export", None),
    ("POST", "/suppliers", {"name": "x"}),
    ("GET", "/suppliers", None),
    ("GET", "/suppliers/1", None),
    ("PATCH", "/suppliers/1/rate", {"monthly_rate": 1200}),
    ("PATCH", "/suppliers/1/status", {"status": "suspended"}),
    ("DELETE", "/suppliers/1", None),
]


class ProtectedRoutesTestCase(unittest.TestCase):
    """Una app con los 15 proveedores de la semilla y una cuenta `user`."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name)
        self.suppliers = SupplierRepository(directory / "suppliers.json")
        self.addCleanup(self.suppliers.close)
        seed_suppliers(self.suppliers, now=SEEDED_AT)
        self.users = UserRepository(directory / "users.json")
        self.addCleanup(self.users.close)
        self.profiles = ProfileRepository(directory / "profiles.json")
        self.addCleanup(self.profiles.close)

        settings = Settings(
            cors_origins=["http://localhost:3000"],
            max_upload_mb=10,
            jwt_secret_key=SECRET,
            access_token_expire_minutes=30,
        )
        self.app = create_app(settings)
        self.app.state.suppliers = self.suppliers
        self.app.state.users = self.users
        self.app.state.profiles = self.profiles

        data = UserCreate(email="ana@nexova.es", password="contraseña-segura")
        self.ana, _ = users_service.create_user(self.users, self.profiles, data)
        self.token = create_access_token(self.ana.id, SECRET, 30)

    def call(self, method, path, **kwargs):
        return request(self.app, method, path, **kwargs)


class WithoutTokenTests(ProtectedRoutesTestCase):
    def test_every_route_answers_401(self):
        for method, path, body in PROTECTED:
            with self.subTest(route=f"{method} {path}"):
                response = self.call(method, path, json_body=body)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_a_malformed_token_is_401_too(self):
        for method, path, body in PROTECTED:
            with self.subTest(route=f"{method} {path}"):
                response = self.call(method, path, json_body=body, token="no-es-un-token")
                self.assertEqual(response.status_code, 401)

    def test_nothing_changes_without_token(self):
        before = self.suppliers.get(1)
        self.call("PATCH", "/suppliers/1/rate", json_body={"monthly_rate": 1})
        self.call("DELETE", "/suppliers/1")
        self.assertEqual(self.suppliers.get(1), before)

    def test_a_deleted_account_loses_access(self):
        # El token sigue firmado y sin caducar, pero la cuenta ya no existe.
        self.users.delete(self.ana.id)
        response = self.call("GET", "/suppliers", token=self.token)
        self.assertEqual(response.status_code, 401)


class WithTokenTests(ProtectedRoutesTestCase):
    """Con token, cada ruta responde lo mismo que antes del candado."""

    def test_list_suppliers(self):
        response = self.call("GET", "/suppliers", token=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 15)

    def test_get_and_change_a_supplier(self):
        self.assertEqual(self.call("GET", "/suppliers/1", token=self.token).status_code, 200)
        response = self.call("PATCH", "/suppliers/1/rate", json_body={"monthly_rate": 1200}, token=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["monthly_rate"], 1200)

    def test_domain_errors_are_unchanged(self):
        self.assertEqual(self.call("GET", f"/suppliers/{MISSING_ID}", token=self.token).status_code, 404)
        self.assertEqual(self.call("POST", "/suppliers", json_body={"name": "x"}, token=self.token).status_code, 422)

    def test_incidents_reach_the_route(self):
        # Sin análisis previo, la exportación da su 404 de siempre.
        self.assertEqual(self.call("GET", "/api/incidents/results/export", token=self.token).status_code, 404)
        # Sin fichero, la subida da su 422: el candado la ha dejado pasar.
        self.assertEqual(self.call("POST", "/api/incidents/analyze", token=self.token).status_code, 422)


class OpenApiTests(unittest.TestCase):
    def test_every_route_shows_the_padlock_and_the_401(self):
        paths = create_app().openapi()["paths"]
        for method, path, _ in PROTECTED:
            template = path.replace("/1", "/{supplier_id}")
            with self.subTest(route=f"{method} {template}"):
                operation = paths[template][method.lower()]
                self.assertIn("security", operation)
                self.assertIn("401", operation["responses"])


if __name__ == "__main__":
    unittest.main()
