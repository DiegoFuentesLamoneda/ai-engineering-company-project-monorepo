"""Pruebas de la persistencia en TinyDB y del seeder.

Cada prueba trabaja sobre un fichero temporal, nunca sobre storage/.
Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.domains.suppliers.database import SupplierRepository
from app.domains.suppliers.schemas import Category, Country, SupplierCreate, SupplierStatus
from app.domains.suppliers.seed_data import SUPPLIERS_SEED
from app.seed import seed_suppliers

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 11, 12, 9, 30, tzinfo=timezone.utc)


class TempDbTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # Una subcarpeta que no existe: el repositorio tiene que crearla.
        self.path = Path(tmp.name) / "storage" / "suppliers.json"

    def open_repo(self) -> SupplierRepository:
        repo = SupplierRepository(self.path)
        self.addCleanup(repo.close)
        return repo


class RepositoryTests(TempDbTestCase):
    def test_insert_assigns_id_and_updated_at(self):
        repo = self.open_repo()
        created = repo.insert(SupplierCreate.model_validate(SUPPLIERS_SEED[0]), updated_at=NOW)
        self.assertEqual(created.id, 1)
        self.assertEqual(created.updated_at, NOW)
        self.assertEqual(repo.get(created.id), created)

    def test_data_survives_reopening_the_file(self):
        repo = self.open_repo()
        created = repo.insert(SupplierCreate.model_validate(SUPPLIERS_SEED[0]), updated_at=NOW)
        repo.close()

        reopened = self.open_repo()
        self.assertEqual(reopened.get(created.id), created)

    def test_file_is_readable_json_with_accents(self):
        repo = self.open_repo()
        repo.insert(SupplierCreate.model_validate(SUPPLIERS_SEED[0]), updated_at=NOW)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("publicación", text)
        self.assertEqual(len(json.loads(text)["suppliers"]), 1)

    def test_get_unknown_id_returns_none(self):
        self.assertIsNone(self.open_repo().get(99))

    def test_update_changes_only_given_fields(self):
        repo = self.open_repo()
        created = repo.insert(SupplierCreate.model_validate(SUPPLIERS_SEED[0]), updated_at=NOW)
        updated = repo.update(created.id, {"monthly_rate": 1350.0, "updated_at": LATER.isoformat()})
        self.assertEqual(updated.monthly_rate, 1350.0)
        self.assertEqual(updated.updated_at, LATER)
        self.assertEqual(updated.name, created.name)

    def test_update_unknown_id_returns_none(self):
        self.assertIsNone(self.open_repo().update(99, {"status": "suspended"}))

    def test_delete(self):
        repo = self.open_repo()
        created = repo.insert(SupplierCreate.model_validate(SUPPLIERS_SEED[0]), updated_at=NOW)
        self.assertTrue(repo.delete(created.id))
        self.assertIsNone(repo.get(created.id))
        self.assertFalse(repo.delete(created.id))


class ListFilterTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        self.repo = self.open_repo()
        seed_suppliers(self.repo, now=NOW)

    def names(self, **filters) -> set[str]:
        return {s.name for s in self.repo.list(**filters)}

    def test_no_filters_returns_everything(self):
        self.assertEqual(len(self.repo.list()), 15)

    def test_filter_by_country(self):
        spain = self.repo.list(country=Country.SPAIN)
        self.assertEqual(len(spain), 8)
        self.assertTrue(all(s.country == Country.SPAIN for s in spain))
        self.assertEqual(len(self.repo.list(country=Country.USA)), 7)

    def test_filter_by_category(self):
        self.assertEqual(self.names(category=Category.ATS_SOFTWARE), {"Workable", "Greenhouse"})

    def test_filters_combine(self):
        self.assertEqual(self.names(country=Country.USA, category=Category.ATS_SOFTWARE), {"Greenhouse"})

    def test_category_matches_inside_a_multi_category_list(self):
        both = SupplierCreate.model_validate(
            SUPPLIERS_SEED[0] | {"name": "Multi", "categories": ["job_boards", "video_interview"]}
        )
        self.repo.insert(both, updated_at=NOW)
        self.assertEqual(self.names(category=Category.VIDEO_INTERVIEW), {"HireVue", "Multi"})

    def test_filter_with_no_matches(self):
        self.assertEqual(self.repo.list(country=Country.SPAIN, category=Category.BACKGROUND_CHECK), [])


class SeederTests(TempDbTestCase):
    def test_first_run_loads_the_whole_briefing(self):
        result = seed_suppliers(self.open_repo(), now=NOW)
        self.assertEqual((result.inserted, result.skipped, result.total), (15, 0, 15))

    def test_second_run_does_not_duplicate(self):
        repo = self.open_repo()
        seed_suppliers(repo, now=NOW)
        result = seed_suppliers(repo, now=LATER)
        self.assertEqual((result.inserted, result.skipped, result.total), (0, 15, 15))

    def test_only_missing_suppliers_are_added(self):
        repo = self.open_repo()
        seed_suppliers(repo, seed=SUPPLIERS_SEED[:5], now=NOW)
        result = seed_suppliers(repo, now=LATER)
        self.assertEqual((result.inserted, result.skipped, result.total), (10, 5, 15))

    def test_seeded_values_match_the_briefing(self):
        repo = self.open_repo()
        seed_suppliers(repo, now=NOW)
        greenhouse = next(s for s in repo.list() if s.name == "Greenhouse")
        self.assertEqual(greenhouse.status, SupplierStatus.SUSPENDED)
        self.assertEqual(greenhouse.monthly_rate, 620.0)
        self.assertIsNone(greenhouse.contract_renewal_date)
        self.assertEqual(greenhouse.updated_at, NOW)

    def test_invalid_entry_aborts_before_writing(self):
        repo = self.open_repo()
        broken = SUPPLIERS_SEED[:3] + [SUPPLIERS_SEED[3] | {"currency": "USD"}]
        with self.assertRaises(ValueError):
            seed_suppliers(repo, seed=broken, now=NOW)
        self.assertEqual(repo.count(), 0)


if __name__ == "__main__":
    unittest.main()
