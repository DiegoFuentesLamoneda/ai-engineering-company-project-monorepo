"""Pruebas de la configuración: lo que no es válido no debe dejar arrancar."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.config import DEFAULT_CORS_ORIGINS, DEFAULT_MAX_UPLOAD_MB, load_settings


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


if __name__ == "__main__":
    unittest.main()
