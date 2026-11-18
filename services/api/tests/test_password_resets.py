"""Pruebas de los tokens de restablecimiento de contraseña (AUTH-03).

Cada prueba trabaja sobre un fichero temporal, nunca sobre storage/.
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

from app.domains.password_resets import service
from app.domains.password_resets.database import PasswordResetRepository
from app.domains.password_resets.exceptions import InvalidResetReason, InvalidResetTokenError

NOW = datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)
MINUTES = 30


class RepoTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "storage" / "password_resets.json"
        self.repo = self.open_repo()
        self.user_id = uuid4()

    def open_repo(self) -> PasswordResetRepository:
        repo = PasswordResetRepository(self.path)
        self.addCleanup(repo.close)
        return repo

    def issue(self, minutes_later: int = 0, user_id=None) -> str:
        return service.issue_token(
            self.repo, user_id or self.user_id, MINUTES, now=NOW + timedelta(minutes=minutes_later)
        )

    def assert_rejected(self, token: str, reason: InvalidResetReason, minutes_later: int = 0):
        with self.assertRaises(InvalidResetTokenError) as caught:
            service.consume_token(self.repo, token, now=NOW + timedelta(minutes=minutes_later))
        self.assertEqual(caught.exception.reason, reason)


class IssueTokenTests(RepoTestCase):
    def test_token_is_long_random_and_url_safe(self):
        first, second = self.issue(), self.issue()
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 43)
        self.assertRegex(first, r"^[A-Za-z0-9_-]+$")

    def test_only_the_hash_is_stored(self):
        token = self.issue()
        # Ni la API ni nadie que lea el fichero puede sacar el token de ahí.
        self.assertNotIn(token, self.path.read_text(encoding="utf-8"))
        [stored] = self.repo.list_for_user(self.user_id)
        self.assertEqual(stored.token_hash, service.hash_token(token))

    def test_expiry_is_the_configured_window(self):
        self.issue()
        [stored] = self.repo.list_for_user(self.user_id)
        self.assertEqual(stored.expires_at - stored.created_at, timedelta(minutes=MINUTES))
        self.assertIsNone(stored.used_at)

    def test_a_new_request_cancels_the_previous_link(self):
        old = self.issue()
        new = self.issue(minutes_later=5)
        self.assertEqual(len(self.repo.list_for_user(self.user_id)), 1)
        self.assert_rejected(old, InvalidResetReason.UNKNOWN, minutes_later=6)
        self.assertEqual(service.consume_token(self.repo, new, now=NOW + timedelta(minutes=6)), self.user_id)

    def test_does_not_touch_other_users_links(self):
        other_user = uuid4()
        other = self.issue(user_id=other_user)
        self.issue()
        self.assertEqual(service.consume_token(self.repo, other, now=NOW), other_user)

    def test_expired_links_are_cleaned_up(self):
        other_user = uuid4()
        self.issue(user_id=other_user)
        self.issue(minutes_later=MINUTES + 1)
        self.assertEqual(self.repo.list_for_user(other_user), [])

    def test_tokens_survive_a_restart(self):
        token = self.issue()
        self.repo.close()
        reopened = self.open_repo()
        self.assertEqual(service.consume_token(reopened, token, now=NOW), self.user_id)


class ConsumeTokenTests(RepoTestCase):
    def test_valid_token_returns_its_owner(self):
        token = self.issue()
        self.assertEqual(service.consume_token(self.repo, token, now=NOW + timedelta(minutes=1)), self.user_id)

    def test_cannot_be_used_twice(self):
        token = self.issue()
        service.consume_token(self.repo, token, now=NOW)
        self.assert_rejected(token, InvalidResetReason.USED, minutes_later=1)

    def test_expires_after_the_window(self):
        token = self.issue()
        # Justo en el minuto 30 ya no vale; un segundo antes, sí.
        self.assert_rejected(token, InvalidResetReason.EXPIRED, minutes_later=MINUTES)
        fresh = self.issue(minutes_later=100)
        last_second = NOW + timedelta(minutes=100 + MINUTES) - timedelta(seconds=1)
        self.assertEqual(service.consume_token(self.repo, fresh, now=last_second), self.user_id)

    def test_expired_token_is_rejected_even_if_never_used(self):
        token = self.issue()
        self.assert_rejected(token, InvalidResetReason.EXPIRED, minutes_later=MINUTES + 60)

    def test_unknown_or_tampered_tokens_are_rejected(self):
        token = self.issue()
        for bad in ("", "no-existe", token[:-1], token + "x", token.upper()):
            with self.subTest(token=bad):
                self.assert_rejected(bad, InvalidResetReason.UNKNOWN)

    def test_same_message_whatever_the_reason(self):
        # La respuesta no le cuenta a nadie si el enlace existió alguna vez.
        messages = {
            str(InvalidResetTokenError(reason)) for reason in InvalidResetReason
        }
        self.assertEqual(len(messages), 1)

    def test_only_one_of_two_simultaneous_uses_wins(self):
        token = self.issue()
        results: list[str] = []

        def use():
            try:
                service.consume_token(self.repo, token, now=NOW)
                results.append("ok")
            except InvalidResetTokenError:
                results.append("rechazado")

        threads = [threading.Thread(target=use) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sorted(results), ["ok"] + ["rechazado"] * 4)


class RepositoryTests(RepoTestCase):
    def test_mark_used_only_once(self):
        self.issue()
        [stored] = self.repo.list_for_user(self.user_id)
        self.assertTrue(self.repo.mark_used(stored.id, NOW))
        self.assertFalse(self.repo.mark_used(stored.id, NOW + timedelta(minutes=1)))
        [after] = self.repo.list_for_user(self.user_id)
        self.assertEqual(after.used_at, NOW)

    def test_used_tokens_are_kept_until_they_expire(self):
        # Si se borrasen al usarlos, reutilizar el enlace diría "no existe"
        # en vez de "ya usado". Da igual para la respuesta, no para la auditoría.
        token = self.issue()
        service.consume_token(self.repo, token, now=NOW)
        self.assertEqual(len(self.repo.list_for_user(self.user_id)), 1)
        self.assertEqual(self.repo.delete_expired(NOW + timedelta(minutes=MINUTES)), 1)


if __name__ == "__main__":
    unittest.main()
