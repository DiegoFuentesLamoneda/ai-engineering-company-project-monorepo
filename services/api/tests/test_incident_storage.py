"""Pruebas de la persistencia del gestor de incidencias en TinyDB.

Cada prueba trabaja sobre un fichero temporal, nunca sobre storage/.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from incident_analysis import Branch, IncidentCategory, IncidentOrigin, IncidentStatus

from app.domains.incidents.database import IncidentRepository
from app.domains.incidents.schemas import Incident

NOW = datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc)


def incident(**changes) -> Incident:
    return Incident.model_validate(
        {
            "id": uuid4(),
            "title": "El ATS no carga las candidaturas",
            "description": "Error al abrir cualquier candidatura.",
            "category": "technical_failure",
            "status": "open",
            "origin": "branch",
            "branch": "valencia_operations",
            "created_at": NOW,
            "updated_at": NOW,
        }
        | changes
    )


class TempDbTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # Una subcarpeta que no existe: el repositorio tiene que crearla.
        self.path = Path(tmp.name) / "storage" / "incidents.json"

    def open_repo(self) -> IncidentRepository:
        repo = IncidentRepository(self.path)
        self.addCleanup(repo.close)
        return repo


class ReadWriteTests(TempDbTestCase):
    def test_empty_database_reads_without_failing(self):
        repo = self.open_repo()
        self.assertEqual(repo.list(), [])
        self.assertIsNone(repo.get(uuid4()))
        self.assertEqual(repo.count(), 0)

    def test_insert_and_get(self):
        repo = self.open_repo()
        created = repo.insert(incident())
        self.assertEqual(repo.get(created.id), created)

    def test_data_survives_reopening_the_file(self):
        repo = self.open_repo()
        created = repo.insert(incident())
        repo.close()
        self.assertEqual(self.open_repo().get(created.id), created)

    def test_file_is_readable_json_with_codes(self):
        repo = self.open_repo()
        repo.insert(incident(title="Formación sin aula asignada"))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        [document] = data["incidents"].values()
        self.assertEqual(document["branch"], "valencia_operations")
        self.assertIn("Formación", self.path.read_text(encoding="utf-8"))

    def test_list_is_newest_first(self):
        repo = self.open_repo()
        old = repo.insert(incident(created_at=NOW - timedelta(days=2), updated_at=NOW))
        new = repo.insert(incident())
        self.assertEqual([i.id for i in repo.list()], [new.id, old.id])


class FilterTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        self.repo = self.open_repo()
        self.sla = self.repo.insert(incident(category="sla_breach", origin="customer", branch="central"))
        self.miami = self.repo.insert(incident(branch="miami_office", status="in_progress"))
        self.remote = self.repo.insert(incident(branch="remote", origin="internal"))

    def ids(self, **filters) -> set:
        return {i.id for i in self.repo.list(**filters)}

    def test_each_filter(self):
        self.assertEqual(self.ids(status=IncidentStatus.IN_PROGRESS), {self.miami.id})
        self.assertEqual(self.ids(origin=IncidentOrigin.CUSTOMER), {self.sla.id})
        self.assertEqual(self.ids(branch=Branch.REMOTE), {self.remote.id})
        # El briefing pide que filtrar los sla_breach sea trivial.
        self.assertEqual(self.ids(category=IncidentCategory.SLA_BREACH), {self.sla.id})

    def test_filters_combine(self):
        self.assertEqual(self.ids(status=IncidentStatus.OPEN, origin=IncidentOrigin.BRANCH), set())
        self.assertEqual(
            self.ids(status=IncidentStatus.OPEN, branch=Branch.REMOTE),
            {self.remote.id},
        )

    def test_no_filters_returns_everything(self):
        self.assertEqual(len(self.repo.list()), 3)


class UpdateStatusTests(TempDbTestCase):
    def test_changes_status_and_updated_at(self):
        repo = self.open_repo()
        created = repo.insert(incident())
        later = NOW + timedelta(hours=1)
        updated = repo.update_status(
            created.id, expected=IncidentStatus.OPEN, target=IncidentStatus.IN_PROGRESS, updated_at=later
        )
        self.assertEqual(updated.status, IncidentStatus.IN_PROGRESS)
        self.assertEqual(updated.updated_at, later)
        self.assertEqual(updated.created_at, NOW)
        self.assertEqual(repo.get(created.id), updated)

    def test_does_nothing_if_someone_changed_it_first(self):
        repo = self.open_repo()
        created = repo.insert(incident(status="in_progress"))
        result = repo.update_status(
            created.id, expected=IncidentStatus.OPEN, target=IncidentStatus.DISCARDED, updated_at=NOW
        )
        self.assertIsNone(result)
        self.assertEqual(repo.get(created.id).status, IncidentStatus.IN_PROGRESS)

    def test_unknown_id(self):
        repo = self.open_repo()
        result = repo.update_status(
            uuid4(), expected=IncidentStatus.OPEN, target=IncidentStatus.IN_PROGRESS, updated_at=NOW
        )
        self.assertIsNone(result)

    def test_only_touches_that_incident(self):
        repo = self.open_repo()
        first = repo.insert(incident())
        second = repo.insert(incident())
        repo.update_status(
            first.id, expected=IncidentStatus.OPEN, target=IncidentStatus.IN_PROGRESS, updated_at=NOW
        )
        self.assertEqual(repo.get(second.id), second)


class SeedImportTests(TempDbTestCase):
    def test_same_ticket_is_inserted_once(self):
        repo = self.open_repo()
        self.assertTrue(repo.insert_seeded(incident(), "NXV-000001"))
        self.assertFalse(repo.insert_seeded(incident(), "NXV-000001"))
        self.assertEqual(repo.count(), 1)
        self.assertEqual(repo.seeded_count(), 1)

    def test_remembers_after_reopening(self):
        repo = self.open_repo()
        repo.insert_seeded(incident(), "NXV-000001")
        repo.close()
        self.assertFalse(self.open_repo().insert_seeded(incident(), "NXV-000001"))

    def test_ticket_id_is_not_stored_in_the_incident(self):
        repo = self.open_repo()
        created = incident()
        repo.insert_seeded(created, "NXV-000007")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        [document] = data["incidents"].values()
        self.assertNotIn("ticket_id", document)
        [link] = data["seed_imports"].values()
        self.assertEqual(link, {"ticket_id": "NXV-000007", "incident_id": str(created.id)})

    def test_form_incidents_do_not_count_as_seeded(self):
        repo = self.open_repo()
        repo.insert(incident())
        self.assertEqual(repo.seeded_count(), 0)


if __name__ == "__main__":
    unittest.main()
