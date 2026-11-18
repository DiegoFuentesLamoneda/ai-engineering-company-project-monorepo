"""Pruebas de la configuración: lo que no es válido no debe dejar arrancar."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.config import (
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_MAX_UPLOAD_MB,
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


if __name__ == "__main__":
    unittest.main()
