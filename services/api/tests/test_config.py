"""Pruebas de la configuración: lo que no es válido no debe dejar arrancar."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.config import (
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_EMAIL_FROM,
    DEFAULT_FRONTEND_URL,
    DEFAULT_MAX_UPLOAD_MB,
    DEFAULT_RESET_REQUESTS_PER_HOUR,
    DEFAULT_RESET_TOKEN_EXPIRE_MINUTES,
    MissingJwtSecretError,
    load_settings,
)

SECRET = "s" * 32


class LoadSettingsTests(unittest.TestCase):
    def test_defaults_allow_both_local_origins(self):
        settings = load_settings({})
        self.assertEqual(settings.cors_origins, list(DEFAULT_CORS_ORIGINS))
        self.assertIn("http://localhost:3000", settings.cors_origins)
        self.assertIn("http://127.0.0.1:3000", settings.cors_origins)
        self.assertEqual(settings.max_upload_mb, DEFAULT_MAX_UPLOAD_MB)

    def test_reads_values_from_the_environment(self):
        settings = load_settings(
            {
                "NEXOVA_API_CORS_ORIGINS": " https://backoffice.nexova.example , https://nexova.example",
                "NEXOVA_API_MAX_UPLOAD_MB": "5",
            }
        )
        self.assertEqual(
            settings.cors_origins, ["https://backoffice.nexova.example", "https://nexova.example"]
        )
        self.assertEqual(settings.max_upload_bytes, 5 * 1024 * 1024)

    def test_rejects_invalid_values(self):
        cases = [
            {"NEXOVA_API_CORS_ORIGINS": "*"},
            {"NEXOVA_API_CORS_ORIGINS": ","},
            {"NEXOVA_API_MAX_UPLOAD_MB": "diez"},
            {"NEXOVA_API_MAX_UPLOAD_MB": "0"},
        ]
        for env in cases:
            with self.subTest(env=env), self.assertRaises(ValidationError):
                load_settings(env)

    def test_errors_never_print_the_value_received(self):
        # Un secreto del JWT demasiado corto no puede acabar en la consola.
        with self.assertRaises(ValidationError) as caught:
            load_settings({"NEXOVA_API_JWT_SECRET_KEY": "secreto-corto-filtrado"})
        self.assertIn("jwt_secret_key", str(caught.exception))
        self.assertNotIn("secreto-corto-filtrado", str(caught.exception))


class JwtSettingsTests(unittest.TestCase):
    def test_secret_is_optional_until_the_api_needs_it(self):
        # El seeder carga la configuración y no firma tokens: no debe exigirlo.
        for env in ({}, {"NEXOVA_API_JWT_SECRET_KEY": ""}):
            with self.subTest(env=env):
                settings = load_settings(env)
                self.assertIsNone(settings.jwt_secret_key)
                with self.assertRaises(MissingJwtSecretError):
                    settings.require_jwt_secret()

    def test_reads_secret_and_expiry_from_the_environment(self):
        settings = load_settings(
            {"NEXOVA_API_JWT_SECRET_KEY": SECRET, "NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES": "15"}
        )
        self.assertEqual(settings.require_jwt_secret().get_secret_value(), SECRET)
        self.assertEqual(settings.access_token_expire_minutes, 15)

    def test_default_expiry(self):
        self.assertEqual(load_settings({}).access_token_expire_minutes, DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)

    def test_secret_never_shows_in_logs(self):
        settings = load_settings({"NEXOVA_API_JWT_SECRET_KEY": SECRET})
        self.assertNotIn(SECRET, repr(settings))
        self.assertNotIn(SECRET, str(settings))

    def test_rejects_weak_secret_and_impossible_expiry(self):
        cases = [
            {"NEXOVA_API_JWT_SECRET_KEY": "corto"},
            {"NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES": "0"},
            {"NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES": "1441"},
            {"NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES": "media hora"},
        ]
        for env in cases:
            with self.subTest(env=env), self.assertRaises(ValidationError):
                load_settings(env)

    def test_errors_never_print_the_value_received(self):
        # Un secreto del JWT demasiado corto no puede acabar en la consola.
        with self.assertRaises(ValidationError) as caught:
            load_settings({"NEXOVA_API_JWT_SECRET_KEY": "secreto-corto-filtrado"})
        self.assertIn("jwt_secret_key", str(caught.exception))
        self.assertNotIn("secreto-corto-filtrado", str(caught.exception))


class PasswordResetSettingsTests(unittest.TestCase):
    def test_defaults_work_without_an_email_account(self):
        # Sin API key la API arranca: el enlace va al log, no a un buzón.
        settings = load_settings({})
        self.assertIsNone(settings.resend_api_key)
        self.assertEqual(settings.reset_token_expire_minutes, DEFAULT_RESET_TOKEN_EXPIRE_MINUTES)
        self.assertEqual(settings.reset_requests_per_hour, DEFAULT_RESET_REQUESTS_PER_HOUR)
        self.assertEqual(settings.frontend_url, DEFAULT_FRONTEND_URL)
        self.assertEqual(settings.email_from, DEFAULT_EMAIL_FROM)

    def test_reads_values_from_the_environment(self):
        settings = load_settings(
            {
                "NEXOVA_API_RESEND_API_KEY": "re_clave_de_prueba",
                "NEXOVA_API_EMAIL_FROM": "Nexova <no-reply@nexova.example>",
                "NEXOVA_API_FRONTEND_URL": "https://backoffice.nexova.example/",
                "NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES": "15",
                "NEXOVA_API_RESET_REQUESTS_PER_HOUR": "5",
            }
        )
        self.assertEqual(settings.resend_api_key.get_secret_value(), "re_clave_de_prueba")
        self.assertEqual(settings.email_from, "Nexova <no-reply@nexova.example>")
        # Sin la barra final: el enlace no puede quedar con "//reset-password".
        self.assertEqual(settings.frontend_url, "https://backoffice.nexova.example")
        self.assertEqual(settings.reset_token_expire_minutes, 15)
        self.assertEqual(settings.reset_requests_per_hour, 5)

    def test_empty_api_key_counts_as_missing(self):
        # Es como viene en .env.example.
        self.assertIsNone(load_settings({"NEXOVA_API_RESEND_API_KEY": ""}).resend_api_key)

    def test_api_key_never_shows_in_logs(self):
        settings = load_settings({"NEXOVA_API_RESEND_API_KEY": "re_clave_de_prueba"})
        self.assertNotIn("re_clave_de_prueba", repr(settings))

    def test_rejects_values_outside_the_ticket(self):
        cases = [
            # El ticket pide entre 15 y 60 minutos.
            {"NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES": "14"},
            {"NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES": "61"},
            {"NEXOVA_API_RESET_REQUESTS_PER_HOUR": "0"},
            {"NEXOVA_API_FRONTEND_URL": "localhost:3000"},
            {"NEXOVA_API_FRONTEND_URL": "javascript:alert(1)"},
        ]
        for env in cases:
            with self.subTest(env=env), self.assertRaises(ValidationError):
                load_settings(env)

    def test_errors_never_print_the_value_received(self):
        # Un secreto del JWT demasiado corto no puede acabar en la consola.
        with self.assertRaises(ValidationError) as caught:
            load_settings({"NEXOVA_API_JWT_SECRET_KEY": "secreto-corto-filtrado"})
        self.assertIn("jwt_secret_key", str(caught.exception))
        self.assertNotIn("secreto-corto-filtrado", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
