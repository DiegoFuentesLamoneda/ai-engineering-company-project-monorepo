"""Pruebas de los errores de los comandos de la API (auditoría, fase de scripts).

- S2: `uv run seed` sale con 1 y un mensaje en stderr, sin traza.
- S4: `uv run create-admin` sale limpio con Ctrl+C o con la entrada cerrada.

Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from app import create_admin, seed
from app.config import Settings


def _stream() -> io.TextIOWrapper:
    # Los comandos llaman a `reconfigure`, que un StringIO no tiene.
    return io.TextIOWrapper(io.BytesIO(), encoding="utf-8")


def _text(stream: io.TextIOWrapper) -> str:
    stream.flush()
    return stream.buffer.getvalue().decode("utf-8")


class CliTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.settings = Settings(
            cors_origins=["http://localhost:3000"],
            max_upload_mb=10,
            suppliers_db_path=self.directory / "suppliers.json",
            users_db_path=self.directory / "users.json",
            profiles_db_path=self.directory / "profiles.json",
        )

    def run_main(self, main):
        """Ejecuta `main` y devuelve (código de salida, stdout, stderr)."""
        out, err = _stream(), _stream()
        code = 0
        with redirect_stdout(out), redirect_stderr(err):
            try:
                main()
            except SystemExit as exit_:
                code = exit_.code
        return code, _text(out), _text(err)


class SeedCommandTests(CliTestCase):
    def test_a_corrupt_database_exits_with_1_and_a_clean_message(self):
        self.settings.suppliers_db_path.write_text("{ esto no es JSON", encoding="utf-8")
        with mock.patch.object(seed, "load_settings", return_value=self.settings):
            code, out, err = self.run_main(seed.main)
        self.assertEqual(code, 1)
        self.assertIn("No se pudo leer", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(out, "")

    def test_an_invalid_config_exits_with_1_and_names_the_variable(self):
        with mock.patch.dict(os.environ, {"NEXOVA_API_MAX_UPLOAD_MB": "-5"}):
            code, _out, err = self.run_main(seed.main)
        self.assertEqual(code, 1)
        self.assertIn("Configuración no válida", err)
        self.assertIn("max_upload_mb", err)
        # El valor recibido no se repite.
        self.assertNotIn("-5", err)

    def test_a_valid_run_still_exits_with_0(self):
        with mock.patch.object(seed, "load_settings", return_value=self.settings):
            code, out, err = self.run_main(seed.main)
        self.assertEqual(code, 0)
        self.assertIn("Proveedores insertados", out)
        self.assertEqual(err, "")


class CreateAdminCommandTests(CliTestCase):
    def run_with_input(self, side_effect):
        with (
            mock.patch.object(create_admin, "load_settings", return_value=self.settings),
            mock.patch("builtins.input", side_effect=side_effect),
        ):
            return self.run_main(create_admin.main)

    def test_ctrl_c_cancels_without_a_traceback(self):
        code, _out, _err = self.run_with_input(KeyboardInterrupt)
        # `SystemExit` con texto: Python lo escribe en stderr y sale con 1.
        self.assertIn("Cancelado. No se ha creado nada.", code)

    def test_a_closed_input_cancels_too(self):
        code, _out, _err = self.run_with_input(EOFError)
        self.assertIn("Cancelado", code)

    def test_ctrl_c_at_the_password_cancels_and_creates_nothing(self):
        with mock.patch.object(create_admin, "getpass", side_effect=KeyboardInterrupt):
            code, _out, _err = self.run_with_input(["nuevo@nexova.es"])
        self.assertIn("Cancelado", code)
        self.assertNotIn("nuevo@nexova.es", self.settings.users_db_path.read_text(encoding="utf-8"))

    def test_a_corrupt_database_exits_with_a_clean_message(self):
        self.settings.users_db_path.write_text("{ esto no es JSON", encoding="utf-8")
        code, _out, _err = self.run_with_input(["ana@nexova.es"])
        self.assertIn("No se pudo leer", code)
        self.assertIn("Revisa el fichero", code)


if __name__ == "__main__":
    unittest.main()
