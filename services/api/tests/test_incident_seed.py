"""Pruebas del seed del gestor: el CSV del briefing entra una vez y bien.

Cada prueba trabaja sobre un fichero temporal, nunca sobre storage/.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path
from unittest import mock
from uuid import uuid4

from incident_analysis import plan_seed_file

from app.domains.incidents.database import IncidentRepository
from app.domains.incidents.schemas import DESCRIPTION_MAX_LENGTH
from app.domains.incidents.seed import seed_incidents, to_incident

REPO_ROOT = Path(__file__).resolve().parents[3]
BRIEFING_CSV = REPO_ROOT / "scripts" / "incidents-nexova.csv"
SCRIPT = REPO_ROOT / "scripts" / "seed_incidents.py"

# "Valores esperados tras el seed" del briefing.
EXPECTED_STATUS = {"open": 27, "resolved": 56, "discarded": 13}
EXPECTED_CATEGORY = {"technical_failure": 49, "process_error": 35, "client_complaint": 12}


class SeedTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "incidents.json"
        self.plan = plan_seed_file(BRIEFING_CSV)

    def open_repo(self) -> IncidentRepository:
        repo = IncidentRepository(self.path)
        self.addCleanup(repo.close)
        return repo


class SeedIncidentsTests(SeedTestCase):
    def test_first_run_loads_the_96_valid_records(self):
        repo = self.open_repo()
        result = seed_incidents(repo, self.plan)
        self.assertEqual((result.inserted, result.skipped, result.total), (96, 0, 96))
        self.assertEqual(result.model_rejected, ())

    def test_second_run_inserts_nothing(self):
        seed_incidents(self.open_repo(), self.plan)
        # Otra apertura del fichero, como una segunda ejecución del script.
        result = seed_incidents(self.open_repo(), self.plan)
        self.assertEqual((result.inserted, result.skipped, result.total), (0, 96, 96))

    def test_totals_match_the_briefing(self):
        repo = self.open_repo()
        seed_incidents(repo, self.plan)
        incidents = repo.list()
        self.assertEqual(Counter(i.status.value for i in incidents), EXPECTED_STATUS)
        self.assertEqual(Counter(i.category.value for i in incidents), EXPECTED_CATEGORY)

    def test_every_seeded_incident_is_customer_and_central(self):
        repo = self.open_repo()
        seed_incidents(repo, self.plan)
        for incident in repo.list():
            self.assertEqual((incident.origin.value, incident.branch.value), ("customer", "central"))
            self.assertEqual(incident.updated_at, incident.created_at)

    def test_an_interrupted_run_completes_on_the_next(self):
        repo = self.open_repo()
        seed_incidents(repo, replace(self.plan, drafts=self.plan.drafts[:10]))
        result = seed_incidents(repo, self.plan)
        self.assertEqual((result.inserted, result.skipped, result.total), (86, 10, 96))

    def test_form_incidents_are_kept(self):
        repo = self.open_repo()
        form_incident = repo.insert(to_incident(self.plan.drafts[0], uuid4()))
        result = seed_incidents(repo, self.plan)
        self.assertEqual((result.inserted, result.total), (96, 97))
        self.assertEqual(repo.get(form_incident.id), form_incident)

    def test_a_draft_the_model_rejects_is_reported_not_fatal(self):
        too_long = replace(self.plan.drafts[0], description="x" * (DESCRIPTION_MAX_LENGTH + 1))
        plan = replace(self.plan, drafts=(too_long, *self.plan.drafts[1:]))
        result = seed_incidents(self.open_repo(), plan)
        self.assertEqual(result.inserted, 95)
        [rejection] = result.model_rejected
        self.assertEqual((rejection.ticket_id, rejection.fields), (too_long.source_id, ("description",)))


def load_script():
    """Importa scripts/seed_incidents.py, que no es un paquete."""
    spec = importlib.util.spec_from_file_location("seed_incidents_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SeedScriptTests(SeedTestCase):
    def run_script(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        env = {"NEXOVA_API_INCIDENTS_DB_PATH": str(self.path)}
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = load_script().main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_reports_the_rejected_rows_without_emails(self):
        code, out, _ = self.run_script()
        self.assertEqual(code, 0)
        for ticket in ("NXV-000017", "NXV-000043", "NXV-000086", "NXV-000090"):
            self.assertIn(ticket, out)
        self.assertIn("Insertadas ahora:       96", out)
        self.assertNotIn("@", out)

    def test_twice_inserts_zero(self):
        self.run_script()
        _, out, _ = self.run_script()
        self.assertIn("Insertadas ahora:       0", out)
        self.assertIn("Ya cargadas (saltadas): 96", out)

    def test_missing_file(self):
        code, _, err = self.run_script("no-existe.csv")
        self.assertEqual(code, 1)
        self.assertIn("no existe", err)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
