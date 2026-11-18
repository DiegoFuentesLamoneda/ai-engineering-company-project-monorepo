"""Pruebas del límite por hora y el registro de auditoría (AUTH-03, fase 5).

Por HTTP, con la base de `test_password_reset_routes` (la app entera, los
repositorios en ficheros temporales y un mailer falso). Lo que depende de la
hora (la ventana del límite, los 90 días) se prueba llamando al `service`
con `now`, porque por HTTP la hora es siempre la de ahora.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.domains.auth.security import create_access_token
from app.domains.password_resets import service as resets_service
from app.domains.password_resets.database import PasswordResetRepository
from app.domains.password_resets.exceptions import InvalidResetTokenError
from app.domains.password_resets.schemas import AuditEntry, AuditEvent
from app.domains.users import service as users_service
from app.domains.users.schemas import UserCreate
from test_password_reset_routes import (
    FORGOT_MESSAGE,
    NEW_PASSWORD,
    PASSWORD,
    SECRET,
    FakeMailer,
    RoutesTestCase,
)

# La IP que pone `http_client.request` en cada petición.
TEST_IP = "testclient"
NOW = datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)


class AuditTestCase(RoutesTestCase):
    def audit(self, user_id=None) -> list[AuditEntry]:
        return self.resets.list_audit(user_id)

    def last(self) -> AuditEntry:
        return self.audit()[-1]

    def request_reset_at(self, when: datetime, email: str = "ana@nexova.es") -> None:
        resets_service.request_reset(
            self.users, self.resets, self.mailer, self.settings, email, ip=TEST_IP, now=when
        )

    def change(self, current: str, new: str = NEW_PASSWORD):
        session = create_access_token(
            self.ana.id, SECRET, 120, now=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        return self.call(
            "POST",
            "/auth/change-password",
            json_body={"current_password": current, "new_password": new},
            token=session,
        )


# --- Límite por hora --------------------------------------------------------


class RateLimitTests(AuditTestCase):
    def setUp(self):
        super().setUp()
        # Cada prueba pasa el límite: el aviso se recoge aquí en vez de ensuciar la salida.
        self.logs = self.enterContext(self.assertLogs("nexova.password_resets", level="WARNING"))

    def test_fourth_request_in_an_hour_answers_the_same_and_sends_nothing(self):
        responses = [self.forgot() for _ in range(4)]
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"message": FORGOT_MESSAGE})
        self.assertEqual(len(self.mailer.sent), 3)
        self.assertEqual(self.last().event, AuditEvent.RESET_LINK_NOT_SENT)
        self.assertEqual(self.last().reason, "rate_limited")
        self.assertEqual(self.last().user_id, self.ana.id)
        [warning] = self.logs.output
        self.assertIn(str(self.ana.id), warning)
        self.assertNotIn("ana@nexova.es", warning)

    def test_the_last_link_sent_still_works(self):
        for _ in range(4):
            self.forgot()
        self.assertEqual(self.reset(self.token_from_last_email()).status_code, 200)

    def test_requests_older_than_an_hour_do_not_count(self):
        for minutes in (0, 1, 2):
            self.request_reset_at(NOW + timedelta(minutes=minutes))
        self.request_reset_at(NOW + timedelta(minutes=30))
        self.assertEqual(len(self.mailer.sent), 3)
        # A las 10:01 la primera ya tiene más de una hora: vuelve a haber hueco.
        self.request_reset_at(NOW + timedelta(minutes=61))
        self.assertEqual(len(self.mailer.sent), 4)

    def test_the_limit_is_per_account(self):
        data = UserCreate(email="bea@nexova.es", password=PASSWORD)
        users_service.create_user(self.users, self.profiles, data)
        for _ in range(4):
            self.forgot()
        self.forgot("bea@nexova.es")
        self.assertEqual([email.to for email in self.mailer.sent][-1], "bea@nexova.es")
        self.assertEqual(len(self.mailer.sent), 4)

    def test_the_limit_comes_from_the_settings(self):
        self.app.state.settings = self.settings.model_copy(update={"reset_requests_per_hour": 1})
        self.forgot()
        self.forgot()
        self.assertEqual(len(self.mailer.sent), 1)

    def test_rejected_requests_do_not_count(self):
        # Pasado el límite, insistir no alarga el bloqueo: solo cuentan los enlaces emitidos.
        for minutes in range(0, 10):
            self.request_reset_at(NOW + timedelta(minutes=minutes))
        self.request_reset_at(NOW + timedelta(minutes=61))
        self.assertEqual(len(self.mailer.sent), 4)

class AtomicLimitTests(unittest.TestCase):
    """Contar y anotar en el mismo cerrojo: diez peticiones a la vez, tres pasan."""

    def test_concurrent_requests_cannot_overshoot_the_limit(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = PasswordResetRepository(Path(tmp.name) / "password_resets.json")
        self.addCleanup(repo.close)
        user_id = uuid4()
        results: list[bool] = []
        start = threading.Barrier(10)

        def attempt():
            entry = AuditEntry(
                id=uuid4(), created_at=NOW, event=AuditEvent.RESET_LINK_ISSUED, user_id=user_id
            )
            start.wait()
            results.append(
                repo.insert_audit_if_under_limit(
                    entry,
                    since=NOW - timedelta(hours=1),
                    limit=3,
                    purge_before=NOW - timedelta(days=90),
                )
            )

        threads = [threading.Thread(target=attempt) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(results.count(True), 3)
        self.assertEqual(len(repo.list_audit(user_id)), 3)


# --- Qué se anota -----------------------------------------------------------


class ForgotPasswordAuditTests(AuditTestCase):
    def test_link_sent(self):
        self.forgot()
        [entry] = self.audit()
        self.assertEqual(entry.event, AuditEvent.RESET_LINK_ISSUED)
        self.assertEqual(entry.user_id, self.ana.id)
        self.assertEqual(entry.ip, TEST_IP)
        self.assertIsNone(entry.reason)

    def test_unknown_email_is_anonymous(self):
        self.forgot("nadie@nexova.es")
        [entry] = self.audit()
        self.assertEqual(entry.event, AuditEvent.RESET_LINK_NOT_SENT)
        self.assertEqual(entry.reason, "unknown_account")
        self.assertIsNone(entry.user_id)
        self.assertEqual(entry.ip, TEST_IP)

    def test_deactivated_account(self):
        self.users.update(self.ana.id, {"is_active": False})
        self.forgot()
        [entry] = self.audit()
        self.assertEqual(entry.event, AuditEvent.RESET_LINK_NOT_SENT)
        self.assertEqual(entry.reason, "inactive_account")
        self.assertEqual(entry.user_id, self.ana.id)

    def test_delivery_failure_leaves_both_entries(self):
        self.app.state.mailer = FakeMailer(fail=True)
        with self.assertLogs("nexova.password_resets", level="ERROR"):
            self.forgot()
        issued, not_sent = self.audit()
        self.assertEqual(issued.event, AuditEvent.RESET_LINK_ISSUED)
        self.assertEqual(not_sent.event, AuditEvent.RESET_LINK_NOT_SENT)
        self.assertEqual(not_sent.reason, "delivery_failed")


    def test_unknown_emails_are_not_limited_but_never_get_anything(self):
        for _ in range(5):
            self.assertEqual(self.forgot("nadie@nexova.es").status_code, 200)
        self.assertEqual(self.mailer.sent, [])
        self.assertEqual({entry.reason for entry in self.audit()}, {"unknown_account"})


class ResetPasswordAuditTests(AuditTestCase):
    def test_success(self):
        self.forgot()
        self.reset(self.token_from_last_email())
        entry = self.last()
        self.assertEqual(entry.event, AuditEvent.PASSWORD_RESET)
        self.assertEqual(entry.user_id, self.ana.id)
        self.assertEqual(entry.ip, TEST_IP)

    def test_reused_link_is_traced_to_its_account(self):
        self.forgot()
        token = self.token_from_last_email()
        self.reset(token)
        self.reset(token, "tercera-contraseña")
        entry = self.last()
        self.assertEqual((entry.event, entry.reason), (AuditEvent.PASSWORD_RESET_FAILED, "used"))
        self.assertEqual(entry.user_id, self.ana.id)

    def test_invented_link_is_anonymous(self):
        self.reset("x" * 43)
        [entry] = self.audit()
        self.assertEqual((entry.event, entry.reason), (AuditEvent.PASSWORD_RESET_FAILED, "unknown"))
        self.assertIsNone(entry.user_id)

    def test_expired_link(self):
        self.request_reset_at(NOW)
        token = self.token_from_last_email()
        with self.assertRaises(InvalidResetTokenError):
            resets_service.reset_password(
                self.users,
                self.resets,
                token,
                NEW_PASSWORD,
                ip=TEST_IP,
                now=NOW + timedelta(hours=1),
            )
        entry = self.last()
        self.assertEqual((entry.reason, entry.user_id), ("expired", self.ana.id))

    def test_account_deactivated_after_asking(self):
        self.forgot()
        self.users.update(self.ana.id, {"is_active": False})
        self.assertEqual(self.reset(self.token_from_last_email()).status_code, 400)
        entry = self.last()
        self.assertEqual((entry.reason, entry.user_id), ("account_unavailable", self.ana.id))

    def test_invalid_body_is_not_audited(self):
        # Un 422 no llega a la ruta: no hay nada que anotar.
        self.reset("x" * 43, "corta")
        self.assertEqual(self.audit(), [])


class ChangePasswordAuditTests(AuditTestCase):
    def test_success(self):
        self.change(PASSWORD)
        [entry] = self.audit()
        self.assertEqual(entry.event, AuditEvent.PASSWORD_CHANGED)
        self.assertEqual((entry.user_id, entry.ip), (self.ana.id, TEST_IP))

    def test_failures(self):
        cases = [
            ("no-es-la-mia", NEW_PASSWORD, "wrong_current_password"),
            (PASSWORD, PASSWORD, "same_password"),
        ]
        for current, new, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(self.change(current, new).status_code, 400)
                entry = self.last()
                self.assertEqual(entry.event, AuditEvent.PASSWORD_CHANGE_FAILED)
                self.assertEqual(entry.reason, reason)
                self.assertEqual(entry.user_id, self.ana.id)


class PersonalDataTests(AuditTestCase):
    def test_no_email_address_is_ever_stored(self):
        # El cambio va primero: después del restablecimiento la sesión ya no valdría.
        self.change("no-es-la-mia")
        self.forgot()
        self.forgot("nadie@nexova.es")
        self.reset(self.token_from_last_email())
        stored = (self.directory / "password_resets.json").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(self.audit()), 4)
        self.assertNotIn("@", stored)

    def write_at(self, when: datetime) -> None:
        resets_service.record(
            self.resets, AuditEvent.PASSWORD_CHANGED, ip=TEST_IP, user_id=self.ana.id, now=when
        )

    def test_entries_older_than_90_days_are_purged_on_the_next_write(self):
        old = NOW - timedelta(days=91)
        recent = NOW - timedelta(days=89)
        for when in (old, recent):
            self.write_at(when)
        self.assertEqual(len(self.audit()), 2)
        self.write_at(NOW)
        self.assertEqual([entry.created_at for entry in self.audit()], [recent, NOW])


if __name__ == "__main__":
    unittest.main()
