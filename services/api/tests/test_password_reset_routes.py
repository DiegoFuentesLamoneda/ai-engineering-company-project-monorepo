"""Pruebas HTTP de la recuperación y el cambio de contraseña (AUTH-03).

La app entera, por ASGI (`http_client.py`), con los repositorios sobre
ficheros temporales y un mailer falso que guarda los emails en una lista.
Las tareas en segundo plano de FastAPI terminan antes de que `request`
devuelva la respuesta, así que el email ya está en la lista al comprobarlo.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic import SecretStr

from app.config import Settings
from app.domains.auth.security import create_access_token
from app.domains.password_resets import service as resets_service
from app.domains.password_resets.database import PasswordResetRepository
from app.domains.profiles.database import ProfileRepository
from app.domains.users import service as users_service
from app.domains.users.database import UserRepository
from app.domains.users.schemas import UserCreate
from app.mailer import EmailDeliveryError, EmailMessage
from app.main import create_app
from http_client import request

SECRET = SecretStr("s" * 40)
PASSWORD = "contraseña-segura"
NEW_PASSWORD = "otra-contraseña-segura"
FORGOT_MESSAGE = "Si esa dirección está registrada, recibirás un enlace en breve."


class FakeMailer:
    def __init__(self, fail: bool = False) -> None:
        self.sent: list[EmailMessage] = []
        self.fail = fail

    def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise EmailDeliveryError("Resend respondió 500: caído")
        self.sent.append(message)


class RoutesTestCase(unittest.TestCase):
    """Una app con la cuenta de Ana y un mailer falso."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name)
        self.directory = directory
        self.users = UserRepository(directory / "users.json")
        self.addCleanup(self.users.close)
        self.profiles = ProfileRepository(directory / "profiles.json")
        self.addCleanup(self.profiles.close)
        self.resets = PasswordResetRepository(directory / "password_resets.json")
        self.addCleanup(self.resets.close)
        self.mailer = FakeMailer()

        self.settings = Settings(
            cors_origins=["http://localhost:3000"],
            max_upload_mb=10,
            jwt_secret_key=SECRET,
            frontend_url="http://localhost:3000",
        )
        self.app = create_app(self.settings)
        self.app.state.users = self.users
        self.app.state.profiles = self.profiles
        self.app.state.password_resets = self.resets
        self.app.state.mailer = self.mailer

        data = UserCreate(email="ana@nexova.es", password=PASSWORD)
        self.ana, _ = users_service.create_user(self.users, self.profiles, data)

    def call(self, method, path, **kwargs):
        return request(self.app, method, path, **kwargs)

    def login(self, password: str):
        form = {"username": "ana@nexova.es", "password": password}
        return self.call("POST", "/auth/login", form=form)

    def forgot(self, email: str = "ana@nexova.es"):
        return self.call("POST", "/auth/forgot-password", json_body={"email": email})

    def token_from_last_email(self) -> str:
        return re.search(r"token=([A-Za-z0-9_-]+)", self.mailer.sent[-1].text).group(1)

    def reset(self, token: str, password: str = NEW_PASSWORD):
        return self.call(
            "POST", "/auth/reset-password", json_body={"token": token, "new_password": password}
        )


class ForgotPasswordTests(RoutesTestCase):
    def test_known_email_gets_a_link(self):
        response = self.forgot()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": FORGOT_MESSAGE})
        [email] = self.mailer.sent
        self.assertEqual(email.to, "ana@nexova.es")
        self.assertIn("http://localhost:3000/reset-password?token=", email.text)

    def test_unknown_email_gets_the_same_answer_and_no_email(self):
        known, unknown = self.forgot(), self.forgot("nadie@nexova.es")
        self.assertEqual(unknown.status_code, known.status_code)
        self.assertEqual(unknown.body, known.body)
        self.assertEqual(len(self.mailer.sent), 1)

    def test_email_is_matched_without_case_or_spaces(self):
        self.forgot("  ANA@Nexova.es ")
        self.assertEqual(len(self.mailer.sent), 1)

    def test_deactivated_account_gets_no_email(self):
        self.users.update(self.ana.id, {"is_active": False})
        self.assertEqual(self.forgot().status_code, 200)
        self.assertEqual(self.mailer.sent, [])

    def test_email_service_down_still_answers_200(self):
        self.app.state.mailer = FakeMailer(fail=True)
        with self.assertLogs("nexova.password_resets", level="ERROR") as logs:
            response = self.forgot()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("ana@nexova.es", "\n".join(logs.output))

    def test_malformed_email_is_422(self):
        for body in ({"email": "no-es-un-email"}, {}, {"email": "ana@nexova.es", "extra": 1}):
            with self.subTest(body=body):
                response = self.call("POST", "/auth/forgot-password", json_body=body)
                self.assertEqual(response.status_code, 422)

    def test_no_token_is_needed(self):
        self.assertEqual(self.forgot().status_code, 200)


class ResetPasswordTests(RoutesTestCase):
    def test_link_changes_the_password(self):
        self.forgot()
        response = self.reset(self.token_from_last_email())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.login(NEW_PASSWORD).status_code, 200)
        self.assertEqual(self.login(PASSWORD).status_code, 401)

    def test_link_works_only_once(self):
        self.forgot()
        token = self.token_from_last_email()
        self.reset(token)
        response = self.reset(token, "tercera-contraseña")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Pide uno nuevo", response.json()["detail"])
        self.assertEqual(self.login(NEW_PASSWORD).status_code, 200)

    def test_invented_or_expired_links_get_the_same_400(self):
        expired = resets_service.issue_token(
            self.resets, self.ana.id, 30, now=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        details = set()
        for token in ("inventado", expired):
            with self.subTest(token=token):
                response = self.reset(token)
                self.assertEqual(response.status_code, 400)
                details.add(response.json()["detail"])
        self.assertEqual(len(details), 1)
        self.assertEqual(self.login(PASSWORD).status_code, 200)

    def test_an_older_link_stops_working_when_a_new_one_is_sent(self):
        self.forgot()
        old = self.token_from_last_email()
        self.forgot()
        self.assertEqual(self.reset(old).status_code, 400)
        self.assertEqual(self.reset(self.token_from_last_email()).status_code, 200)

    def test_weak_new_password_is_422_and_does_not_spend_the_link(self):
        self.forgot()
        token = self.token_from_last_email()
        self.assertEqual(self.reset(token, "corta").status_code, 422)
        self.assertEqual(self.reset(token).status_code, 200)

    def test_account_deleted_after_asking_gets_400(self):
        self.forgot()
        self.users.delete(self.ana.id)
        self.assertEqual(self.reset(self.token_from_last_email()).status_code, 400)

    def test_sessions_opened_before_the_reset_are_closed(self):
        # La sesión vieja tiene que ser al menos un segundo anterior al cambio
        # (`iat` va en segundos): se emite con una hora de antigüedad.
        an_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        old_session = create_access_token(self.ana.id, SECRET, 120, now=an_hour_ago)
        self.forgot()
        self.reset(self.token_from_last_email())
        self.assertEqual(self.call("GET", "/auth/me", token=old_session).status_code, 401)
        new_session = self.login(NEW_PASSWORD).json()["access_token"]
        self.assertEqual(self.call("GET", "/auth/me", token=new_session).status_code, 200)

    def test_oversized_token_is_422(self):
        self.assertEqual(self.reset("x" * 500).status_code, 422)


class ChangePasswordTests(RoutesTestCase):
    def setUp(self):
        super().setUp()
        an_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        self.session = create_access_token(self.ana.id, SECRET, 120, now=an_hour_ago)

    def change(self, current: str, new: str = NEW_PASSWORD, token: str | None = None):
        return self.call(
            "POST",
            "/auth/change-password",
            json_body={"current_password": current, "new_password": new},
            token=token or self.session,
        )

    def test_changes_the_password_and_returns_a_new_session(self):
        response = self.change(PASSWORD)
        self.assertEqual(response.status_code, 200)
        new_session = response.json()["access_token"]
        self.assertEqual(self.call("GET", "/auth/me", token=new_session).status_code, 200)
        self.assertEqual(self.login(NEW_PASSWORD).status_code, 200)
        self.assertEqual(self.login(PASSWORD).status_code, 401)

    def test_other_sessions_are_closed(self):
        self.change(PASSWORD)
        self.assertEqual(self.call("GET", "/auth/me", token=self.session).status_code, 401)

    def test_wrong_current_password_is_400(self):
        response = self.change("no-es-la-mia")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "La contraseña actual no es correcta.")
        self.assertEqual(self.login(PASSWORD).status_code, 200)

    def test_same_password_is_400(self):
        response = self.change(PASSWORD, PASSWORD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("distinta", response.json()["detail"])

    def test_without_session_is_401(self):
        response = self.call(
            "POST",
            "/auth/change-password",
            json_body={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.login(PASSWORD).status_code, 200)

    def test_weak_new_password_is_422(self):
        self.assertEqual(self.change(PASSWORD, "corta").status_code, 422)

    def test_cancels_a_pending_reset_link(self):
        self.forgot()
        link_token = self.token_from_last_email()
        self.change(PASSWORD)
        self.assertEqual(self.reset(link_token, "tercera-contraseña").status_code, 400)


class SessionAfterPasswordChangeTests(RoutesTestCase):
    """El borde del segundo: `iat` va en segundos enteros."""

    def test_token_issued_in_the_same_second_as_the_change_is_valid(self):
        # El cambio, a las X,9 s; los tokens, a las X,0 s y a las X-1 s. Relativo
        # a ahora, porque un token con fecha fija acabaría caducando.
        now = datetime.now(timezone.utc).replace(microsecond=900_000)
        users_service.set_password(self.users, self.ana.id, NEW_PASSWORD, now=now)
        same_second = create_access_token(self.ana.id, SECRET, 30, now=now.replace(microsecond=0))
        second_before = create_access_token(self.ana.id, SECRET, 30, now=now - timedelta(seconds=1))
        self.assertEqual(self.call("GET", "/auth/me", token=same_second).status_code, 200)
        self.assertEqual(self.call("GET", "/auth/me", token=second_before).status_code, 401)

    def test_accounts_that_never_changed_their_password_keep_working(self):
        token = create_access_token(self.ana.id, SECRET, 30)
        self.assertIsNone(self.users.get(self.ana.id).password_changed_at)
        self.assertEqual(self.call("GET", "/auth/me", token=token).status_code, 200)

    def test_put_users_with_a_password_also_closes_old_sessions(self):
        old = create_access_token(
            self.ana.id, SECRET, 120, now=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        response = self.call(
            "PUT", f"/users/{self.ana.id}", json_body={"password": NEW_PASSWORD}, token=old
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.call("GET", "/auth/me", token=old).status_code, 401)


class FullFlowTests(RoutesTestCase):
    def test_forgot_reset_login(self):
        self.assertEqual(self.forgot().status_code, 200)
        self.assertEqual(self.reset(self.token_from_last_email()).status_code, 200)
        login = self.login(NEW_PASSWORD)
        self.assertEqual(login.status_code, 200)
        me = self.call("GET", "/auth/me", token=login.json()["access_token"])
        self.assertEqual(me.json()["email"], "ana@nexova.es")


if __name__ == "__main__":
    unittest.main()
