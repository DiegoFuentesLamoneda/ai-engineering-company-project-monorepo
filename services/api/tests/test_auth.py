"""Pruebas de la autenticación: tokens, `get_current_user`, login y `/auth/me`.

Las rutas se prueban llamando a sus funciones directamente, con los
repositorios sobre ficheros temporales: sin `httpx` no hay `TestClient`.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr

from app.config import Settings
from app.domains.auth import router as auth_router
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.exceptions import InvalidTokenError
from app.domains.auth.security import create_access_token, decode_access_token
from app.domains.profiles.database import ProfileRepository
from app.domains.users import service as users_service
from app.domains.users.database import UserRepository
from app.domains.users.schemas import Role, UserCreate
from app.main import create_app

SECRET = SecretStr("s" * 40)
OTHER_SECRET = SecretStr("o" * 40)
PASSWORD = "contraseña-segura"


def _b64(data: dict) -> str:
    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class TokenTests(unittest.TestCase):
    def test_round_trip(self):
        user_id = uuid4()
        token = create_access_token(user_id, SECRET, 30)
        self.assertEqual(decode_access_token(token, SECRET), user_id)

    def test_token_carries_only_id_and_dates(self):
        token = create_access_token(uuid4(), SECRET, 30)
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        self.assertEqual(set(claims), {"sub", "iat", "exp"})
        self.assertEqual(claims["exp"] - claims["iat"], 30 * 60)

    def test_expired_token_is_rejected(self):
        an_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        token = create_access_token(uuid4(), SECRET, 30, now=an_hour_ago)
        with self.assertRaises(InvalidTokenError):
            decode_access_token(token, SECRET)

    def test_token_signed_with_another_secret_is_rejected(self):
        token = create_access_token(uuid4(), OTHER_SECRET, 30)
        with self.assertRaises(InvalidTokenError):
            decode_access_token(token, SECRET)

    def test_tampered_payload_is_rejected(self):
        # Cambiar el `sub` por el de otra persona sin volver a firmar.
        header, _, signature = create_access_token(uuid4(), SECRET, 30).split(".")
        exp = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
        forged = ".".join([header, _b64({"sub": str(uuid4()), "exp": exp}), signature])
        with self.assertRaises(InvalidTokenError):
            decode_access_token(forged, SECRET)

    def test_unsigned_token_is_rejected(self):
        exp = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
        unsigned = f"{_b64({'alg': 'none', 'typ': 'JWT'})}.{_b64({'sub': str(uuid4()), 'exp': exp})}."
        with self.assertRaises(InvalidTokenError):
            decode_access_token(unsigned, SECRET)

    def test_malformed_tokens_are_rejected(self):
        for token in ("", "no-es-un-jwt", "a.b.c", "Bearer x"):
            with self.subTest(token=token), self.assertRaises(InvalidTokenError):
                decode_access_token(token, SECRET)

    def test_token_without_exp_or_with_bad_sub_is_rejected(self):
        from jose import jwt

        no_exp = jwt.encode({"sub": str(uuid4())}, SECRET.get_secret_value(), algorithm="HS256")
        exp = int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp())
        bad_sub = jwt.encode({"sub": "7", "exp": exp}, SECRET.get_secret_value(), algorithm="HS256")
        for token in (no_exp, bad_sub):
            with self.subTest(token=token), self.assertRaises(InvalidTokenError):
                decode_access_token(token, SECRET)


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name) / "storage"
        self.users = UserRepository(directory / "users.json")
        self.addCleanup(self.users.close)
        self.profiles = ProfileRepository(directory / "profiles.json")
        self.addCleanup(self.profiles.close)
        self.settings = Settings(
            cors_origins=["http://localhost:3000"],
            max_upload_mb=10,
            jwt_secret_key=SECRET,
            access_token_expire_minutes=30,
        )
        data = UserCreate(email="ana@nexova.es", password=PASSWORD, name="Ana Pérez")
        self.ana, _ = users_service.create_user(self.users, self.profiles, data)

    def login(self, username="ana@nexova.es", password=PASSWORD):
        form = OAuth2PasswordRequestForm(username=username, password=password)
        return auth_router.login(form, self.users, self.settings)

    def current_user(self, token):
        return get_current_user(token, self.users, self.settings)

    def assert_401(self, call):
        with self.assertRaises(HTTPException) as caught:
            call()
        self.assertEqual(caught.exception.status_code, 401)
        self.assertEqual(caught.exception.headers, {"WWW-Authenticate": "Bearer"})
        return caught.exception


class LoginTests(AuthTestCase):
    def test_login_returns_bearer_token(self):
        token = self.login()
        self.assertEqual(token.token_type, "bearer")
        self.assertEqual(token.expires_in, 30 * 60)
        self.assertEqual(decode_access_token(token.access_token, SECRET), self.ana.id)

    def test_email_is_case_insensitive(self):
        self.assertTrue(self.login(username=" ANA@Nexova.es").access_token)

    def test_wrong_credentials_give_the_same_401(self):
        wrong_password = self.assert_401(lambda: self.login(password="otra-contraseña"))
        unknown_email = self.assert_401(lambda: self.login(username="nadie@nexova.es"))
        self.assertEqual(wrong_password.detail, unknown_email.detail)


class CurrentUserTests(AuthTestCase):
    def test_valid_token_gives_the_user(self):
        token = self.login().access_token
        self.assertEqual(self.current_user(token).id, self.ana.id)

    def test_missing_token(self):
        self.assert_401(lambda: self.current_user(None))

    def test_bad_tokens(self):
        an_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        expired = create_access_token(self.ana.id, SECRET, 30, now=an_hour_ago)
        foreign = create_access_token(self.ana.id, OTHER_SECRET, 30)
        for token in ("basura", expired, foreign):
            with self.subTest(token=token):
                self.assert_401(lambda: self.current_user(token))

    def test_token_of_deleted_account(self):
        token = self.login().access_token
        users_service.delete_user(self.users, self.profiles, self.ana.id, self.ana)
        self.assert_401(lambda: self.current_user(token))

    def test_token_of_deactivated_account(self):
        token = self.login().access_token
        self.users.update(self.ana.id, {"is_active": False})
        self.assert_401(lambda: self.current_user(token))

    def test_role_comes_from_the_database_not_the_token(self):
        token = self.login().access_token
        self.users.update(self.ana.id, {"role": "admin"})
        self.assertEqual(self.current_user(token).role, Role.ADMIN)


class MeTests(AuthTestCase):
    def test_me_returns_email_role_and_profile(self):
        caller = self.current_user(self.login().access_token)
        me = auth_router.me(caller, self.profiles)
        self.assertEqual(me.email, "ana@nexova.es")
        self.assertEqual(me.role, Role.USER)
        self.assertEqual(me.profile.name, "Ana Pérez")
        self.assertNotIn("hashed_password", me.model_dump())


class OpenApiTests(unittest.TestCase):
    def test_docs_know_how_to_log_in(self):
        schema = create_app().openapi()
        scheme = schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]
        self.assertEqual(scheme["flows"]["password"]["tokenUrl"], "/auth/login")
        self.assertIn("security", schema["paths"]["/auth/me"]["get"])
        self.assertNotIn("security", schema["paths"]["/auth/login"]["post"])


if __name__ == "__main__":
    unittest.main()
