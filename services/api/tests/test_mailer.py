"""Pruebas del envío de emails y de la plantilla de restablecimiento (AUTH-03).

Ninguna sale a internet: un `opener` falso ocupa el lugar de `urlopen` y
guarda la petición que se habría enviado a Resend.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import io
import json
import unittest
import urllib.error
from email.message import Message

from pydantic import SecretStr

from app.config import load_settings
from app.domains.password_resets.emails import SUBJECT, build_reset_email, reset_link
from app.mailer import (
    RESEND_ENDPOINT,
    EmailDeliveryError,
    EmailMessage,
    LogMailer,
    ResendMailer,
    build_mailer,
    mask_email,
)

API_KEY = "re_clave_de_prueba_que_no_debe_salir"
MESSAGE = EmailMessage(to="ana@nexova.es", subject="Asunto", html="<p>Hola</p>", text="Hola")


class FakeResponse(io.BytesIO):
    """`urlopen` devuelve algo que se usa con `with` y tiene `read()`."""


class FakeOpener:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error
        return FakeResponse(b'{"id": "123"}')


def http_error(code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(RESEND_ENDPOINT, code, "error", Message(), io.BytesIO(body.encode()))


class ResendMailerTests(unittest.TestCase):
    def send(self, opener: FakeOpener) -> None:
        ResendMailer(SecretStr(API_KEY), "Nexova <no-reply@nexova.es>", opener=opener).send(MESSAGE)

    def test_posts_the_email_to_resend(self):
        opener = FakeOpener()
        self.send(opener)
        [request] = opener.requests
        self.assertEqual(request.full_url, RESEND_ENDPOINT)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            json.loads(request.data),
            {
                "from": "Nexova <no-reply@nexova.es>",
                "to": ["ana@nexova.es"],
                "subject": "Asunto",
                "html": "<p>Hola</p>",
                "text": "Hola",
            },
        )

    def test_authenticates_with_the_key_and_a_custom_user_agent(self):
        opener = FakeOpener()
        self.send(opener)
        [request] = opener.requests
        # urllib guarda las cabeceras con la primera letra en mayúscula.
        self.assertEqual(request.get_header("Authorization"), f"Bearer {API_KEY}")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertNotIn("Python-urllib", request.get_header("User-agent"))

    def test_never_waits_forever(self):
        opener = FakeOpener()
        self.send(opener)
        self.assertLessEqual(opener.timeouts[0], 10)

    def test_rejected_email_raises_without_leaking_the_key(self):
        opener = FakeOpener(error=http_error(422, '{"message": "Invalid `to` field"}'))
        with self.assertRaises(EmailDeliveryError) as caught:
            self.send(opener)
        self.assertIn("422", str(caught.exception))
        self.assertIn("Invalid", str(caught.exception))
        self.assertNotIn(API_KEY, str(caught.exception))

    def test_network_failure_raises_delivery_error(self):
        opener = FakeOpener(error=urllib.error.URLError("sin red"))
        with self.assertRaises(EmailDeliveryError):
            self.send(opener)

    def test_repr_hides_the_key(self):
        mailer = ResendMailer(SecretStr(API_KEY), "Nexova <no-reply@nexova.es>")
        self.assertNotIn(API_KEY, repr(mailer))


class LogMailerTests(unittest.TestCase):
    def test_writes_the_text_but_masks_the_address(self):
        with self.assertLogs("nexova.mailer", level="WARNING") as logs:
            LogMailer().send(MESSAGE)
        output = "\n".join(logs.output)
        self.assertIn("Hola", output)
        self.assertIn("a***@nexova.es", output)
        self.assertNotIn("ana@nexova.es", output)


class BuildMailerTests(unittest.TestCase):
    def test_without_key_falls_back_to_the_log(self):
        with self.assertLogs("nexova.mailer", level="WARNING"):
            mailer = build_mailer(load_settings({}))
        self.assertIsInstance(mailer, LogMailer)

    def test_with_key_uses_resend(self):
        mailer = build_mailer(load_settings({"NEXOVA_API_RESEND_API_KEY": API_KEY}))
        self.assertIsInstance(mailer, ResendMailer)

    def test_mask_email(self):
        self.assertEqual(mask_email("diego@nexova.es"), "d***@nexova.es")
        self.assertEqual(mask_email("sin-arroba"), "***")


class ResetEmailTests(unittest.TestCase):
    TOKEN = "AbC-123_xyz"

    def build(self):
        link = reset_link("https://backoffice.nexova.es", self.TOKEN)
        return build_reset_email("ana@nexova.es", link, 30)

    def test_link_points_to_the_reset_page_with_the_token(self):
        self.assertEqual(
            reset_link("http://localhost:3000", self.TOKEN),
            "http://localhost:3000/reset-password?token=AbC-123_xyz",
        )

    def test_link_is_escaped_if_the_token_ever_changes_shape(self):
        self.assertTrue(reset_link("http://x", "a&b=c").endswith("token=a%26b%3Dc"))

    def test_email_carries_the_link_in_html_and_text(self):
        email = self.build()
        link = "https://backoffice.nexova.es/reset-password?token=AbC-123_xyz"
        self.assertEqual(email.to, "ana@nexova.es")
        self.assertEqual(email.subject, SUBJECT)
        self.assertIn(f'href="{link}"', email.html)
        self.assertIn(link, email.text)

    def test_says_how_long_it_lasts_and_what_to_do_if_unexpected(self):
        email = self.build()
        for body in (email.html, email.text):
            with self.subTest(body=body[:15]):
                self.assertIn("30 minutos", body)
                self.assertIn("solo sirve una vez", body)
                self.assertIn("ignora este email", body)

    def test_html_is_readable_on_a_phone(self):
        html = self.build().html
        self.assertIn('name="viewport"', html)
        self.assertIn("max-width:480px", html)
        self.assertNotIn("<style", html)  # Gmail borra los <style>: todo en línea.

    def test_html_escapes_the_link(self):
        email = build_reset_email("ana@nexova.es", 'http://x/?token="><script>', 30)
        self.assertNotIn("<script>", email.html)
        self.assertIn("&quot;&gt;&lt;script&gt;", email.html)


if __name__ == "__main__":
    unittest.main()
