"""Pruebas HTTP de `/users`, `/profiles/me` y el candado de las rutas.

Las peticiones recorren la app entera con el cliente de `http_client.py`:
lo que se comprueba es el código HTTP que vería el backoffice. Se ejecutan
desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from pydantic import SecretStr

from app.config import Settings
from app.domains.auth.security import create_access_token
from app.domains.profiles.database import ProfileRepository
from app.domains.users import service as users_service
from app.domains.users.database import UserRepository
from app.domains.users.schemas import Role, UserCreate
from app.main import create_app
from http_client import request

SECRET = SecretStr("s" * 40)
PASSWORD = "contraseña-segura"


class RoutesTestCase(unittest.TestCase):
    """Una app con dos cuentas: Ana (`user`) y Marta (`admin`)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name) / "storage"
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
        self.app.state.users = self.users
        self.app.state.profiles = self.profiles

        self.ana = self._create("ana@nexova.es", Role.USER, name="Ana Pérez")
        self.marta = self._create("marta@nexova.es", Role.ADMIN)
        self.ana_token = create_access_token(self.ana.id, SECRET, 30)
        self.marta_token = create_access_token(self.marta.id, SECRET, 30)

    def _create(self, email, role, **profile):
        data = UserCreate(email=email, password=PASSWORD, **profile)
        user, _ = users_service.create_user(self.users, self.profiles, data, role=role)
        return user

    def call(self, method, path, **kwargs):
        return request(self.app, method, path, **kwargs)


class RegisterTests(RoutesTestCase):
    def test_register_is_public_and_creates_the_profile(self):
        response = self.call(
            "POST", "/users",
            json_body={"email": "Luis@Nexova.es", "password": PASSWORD, "name": "Luis", "phone": "+34 600 000 000"},
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(response.headers["location"], f"/users/{body['id']}")
        self.assertEqual(body["email"], "luis@nexova.es")
        self.assertEqual(body["role"], "user")
        self.assertEqual(body["profile"]["name"], "Luis")
        self.assertEqual(body["profile"]["user_id"], body["id"])
        self.assertNotIn("hashed_password", body)
        self.assertNotIn("password", body)

    def test_full_flow_register_login_me(self):
        self.call("POST", "/users", json_body={"email": "luis@nexova.es", "password": PASSWORD, "name": "Luis"})
        login = self.call("POST", "/auth/login", form={"username": "luis@nexova.es", "password": PASSWORD})
        self.assertEqual(login.status_code, 200)
        me = self.call("GET", "/auth/me", token=login.json()["access_token"])
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["profile"]["name"], "Luis")

    def test_nobody_registers_as_admin(self):
        response = self.call("POST", "/users", json_body={"email": "x@nexova.es", "password": PASSWORD, "role": "admin"})
        self.assertEqual(response.status_code, 422)

    def test_email_already_registered(self):
        response = self.call("POST", "/users", json_body={"email": "ANA@nexova.es", "password": PASSWORD})
        self.assertEqual(response.status_code, 409)


class LockTests(RoutesTestCase):
    """El candado: toda ruta de usuarios salvo el alta pide un token válido."""

    def protected_routes(self):
        user = f"/users/{self.ana.id}"
        return [
            ("GET", "/auth/me", None),
            ("GET", "/users", None),
            ("GET", user, None),
            ("PUT", user, {"email": "otra@nexova.es"}),
            ("DELETE", user, None),
            ("GET", "/profiles/me", None),
            ("PUT", "/profiles/me", {"name": "Otra"}),
        ]

    def test_without_token_401(self):
        for method, path, body in self.protected_routes():
            with self.subTest(route=f"{method} {path}"):
                response = self.call(method, path, json_body=body)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_with_malformed_token_401(self):
        for method, path, body in self.protected_routes():
            with self.subTest(route=f"{method} {path}"):
                response = self.call(method, path, json_body=body, token="no-es-un-token")
                self.assertEqual(response.status_code, 401)

    def test_401_comes_before_validating_the_request(self):
        # Sin token no se dice nada más, ni siquiera que el ID está mal escrito.
        self.assertEqual(self.call("GET", "/users/no-es-un-uuid").status_code, 401)

    def test_nothing_changed_without_token(self):
        self.call("DELETE", f"/users/{self.ana.id}")
        self.assertIsNotNone(self.users.get(self.ana.id))


class ListAndGetTests(RoutesTestCase):
    def test_admin_lists_users_without_hashes(self):
        response = self.call("GET", "/users", token=self.marta_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({u["email"] for u in response.json()}, {"ana@nexova.es", "marta@nexova.es"})
        self.assertNotIn(b"hashed_password", response.body)

    def test_user_cannot_list(self):
        self.assertEqual(self.call("GET", "/users", token=self.ana_token).status_code, 403)

    def test_get_own_account(self):
        response = self.call("GET", f"/users/{self.ana.id}", token=self.ana_token)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("hashed_password", response.json())

    def test_get_someone_else_403(self):
        response = self.call("GET", f"/users/{self.marta.id}", token=self.ana_token)
        self.assertEqual(response.status_code, 403)

    def test_admin_gets_anyone(self):
        response = self.call("GET", f"/users/{self.ana.id}", token=self.marta_token)
        self.assertEqual(response.status_code, 200)

    def test_unknown_id_404_for_admin_but_403_for_others(self):
        unknown = f"/users/{uuid4()}"
        self.assertEqual(self.call("GET", unknown, token=self.marta_token).status_code, 404)
        self.assertEqual(self.call("GET", unknown, token=self.ana_token).status_code, 403)


class UpdateTests(RoutesTestCase):
    def test_change_own_email(self):
        response = self.call("PUT", f"/users/{self.ana.id}", json_body={"email": "ana.perez@nexova.es"}, token=self.ana_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "ana.perez@nexova.es")

    def test_user_cannot_change_own_role(self):
        response = self.call("PUT", f"/users/{self.ana.id}", json_body={"role": "admin"}, token=self.ana_token)
        self.assertEqual(response.status_code, 403)
        self.assertIs(self.users.get(self.ana.id).role, Role.USER)

    def test_admin_changes_a_role(self):
        response = self.call("PUT", f"/users/{self.ana.id}", json_body={"role": "manager"}, token=self.marta_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "manager")

    def test_edit_someone_else_403(self):
        response = self.call("PUT", f"/users/{self.marta.id}", json_body={"email": "x@nexova.es"}, token=self.ana_token)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.users.get(self.marta.id).email, "marta@nexova.es")

    def test_email_taken_409(self):
        response = self.call("PUT", f"/users/{self.ana.id}", json_body={"email": "marta@nexova.es"}, token=self.ana_token)
        self.assertEqual(response.status_code, 409)

    def test_unknown_field_422(self):
        response = self.call("PUT", f"/users/{self.ana.id}", json_body={"is_active": False}, token=self.ana_token)
        self.assertEqual(response.status_code, 422)


class DeleteTests(RoutesTestCase):
    def test_delete_someone_else_403(self):
        response = self.call("DELETE", f"/users/{self.marta.id}", token=self.ana_token)
        self.assertEqual(response.status_code, 403)
        self.assertIsNotNone(self.users.get(self.marta.id))

    def test_delete_own_account_with_profile(self):
        response = self.call("DELETE", f"/users/{self.ana.id}", token=self.ana_token)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.body, b"")
        self.assertIsNone(self.users.get(self.ana.id))
        self.assertIsNone(self.profiles.get_by_user(self.ana.id))
        # Su token deja de valer en el acto.
        self.assertEqual(self.call("GET", "/auth/me", token=self.ana_token).status_code, 401)

    def test_admin_deletes_anyone_then_404(self):
        path = f"/users/{self.ana.id}"
        self.assertEqual(self.call("DELETE", path, token=self.marta_token).status_code, 204)
        self.assertEqual(self.call("DELETE", path, token=self.marta_token).status_code, 404)


class ProfileTests(RoutesTestCase):
    def test_get_my_profile(self):
        response = self.call("GET", "/profiles/me", token=self.ana_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Ana Pérez")
        self.assertEqual(response.json()["user_id"], str(self.ana.id))

    def test_update_only_what_is_sent(self):
        response = self.call("PUT", "/profiles/me", json_body={"phone": "+1 305 555 0100"}, token=self.ana_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["phone"], "+1 305 555 0100")
        self.assertEqual(response.json()["name"], "Ana Pérez")

    def test_null_clears_a_field(self):
        response = self.call("PUT", "/profiles/me", json_body={"name": None}, token=self.ana_token)
        self.assertIsNone(response.json()["name"])

    def test_cannot_move_the_profile_to_another_user(self):
        response = self.call("PUT", "/profiles/me", json_body={"user_id": str(self.marta.id)}, token=self.ana_token)
        self.assertEqual(response.status_code, 422)

    def test_each_one_sees_their_own(self):
        response = self.call("GET", "/profiles/me", token=self.marta_token)
        self.assertEqual(response.json()["user_id"], str(self.marta.id))


class OpenApiTests(unittest.TestCase):
    def test_only_register_is_public(self):
        paths = create_app().openapi()["paths"]
        self.assertNotIn("security", paths["/users"]["post"])
        for path, method in [
            ("/users", "get"),
            ("/users/{user_id}", "get"),
            ("/users/{user_id}", "put"),
            ("/users/{user_id}", "delete"),
            ("/profiles/me", "get"),
            ("/profiles/me", "put"),
        ]:
            with self.subTest(route=f"{method} {path}"):
                self.assertIn("security", paths[path][method])


if __name__ == "__main__":
    unittest.main()
