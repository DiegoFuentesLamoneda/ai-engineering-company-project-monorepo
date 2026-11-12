"""Pruebas de las reglas del directorio de proveedores (service).

Aquí se prueba todo lo que decide algo, sobre un fichero temporal de TinyDB.
Las rutas HTTP, con su candado, están en `test_protected_routes.py`.

Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.domains.suppliers import service
from app.domains.suppliers.database import SupplierRepository
from app.domains.suppliers.exceptions import SupplierNotFoundError, SuspendedSupplierDeletionError
from app.domains.suppliers.schemas import (
    Category,
    Country,
    RateUpdate,
    StatusUpdate,
    SupplierCreate,
    SupplierStatus,
)
from app.domains.suppliers.seed_data import SUPPLIERS_SEED
from app.main import create_app
from app.seed import seed_suppliers

SEEDED_AT = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)
MISSING_ID = 999


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = SupplierRepository(Path(tmp.name) / "suppliers.json")
        self.addCleanup(self.repo.close)
        seed_suppliers(self.repo, now=SEEDED_AT)

    def by_name(self, name: str):
        return next(s for s in self.repo.list() if s.name == name)


class ReadTests(ServiceTestCase):
    def test_list_is_sorted_by_name(self):
        names = [s.name for s in service.list_suppliers(self.repo)]
        self.assertEqual(names, sorted(names, key=str.casefold))
        self.assertEqual(len(names), 15)

    def test_list_passes_filters(self):
        found = service.list_suppliers(self.repo, country=Country.SPAIN, category=Category.JOB_BOARDS)
        self.assertEqual([s.name for s in found], ["InfoJobs Premium", "LinkedIn Talent Solutions"])

    def test_get_unknown_id(self):
        with self.assertRaises(SupplierNotFoundError):
            service.get_supplier(self.repo, MISSING_ID)


class CreateTests(ServiceTestCase):
    def test_create_sets_id_and_updated_at(self):
        data = SupplierCreate.model_validate(SUPPLIERS_SEED[0] | {"name": "Personio"})
        created = service.create_supplier(self.repo, data, now=NOW)
        self.assertEqual(created.updated_at, NOW)
        self.assertEqual(service.get_supplier(self.repo, created.id), created)


class RateTests(ServiceTestCase):
    def test_rate_change_renews_updated_at(self):
        workable = self.by_name("Workable")
        updated = service.update_rate(self.repo, workable.id, RateUpdate(monthly_rate=329.0), now=NOW)
        self.assertEqual(updated.monthly_rate, 329.0)
        self.assertEqual(updated.updated_at, NOW)
        self.assertEqual(updated.status, workable.status)

    def test_rate_change_persists(self):
        workable = self.by_name("Workable")
        service.update_rate(self.repo, workable.id, RateUpdate(monthly_rate=329.0), now=NOW)
        self.assertEqual(service.get_supplier(self.repo, workable.id).monthly_rate, 329.0)

    def test_rate_unknown_id(self):
        with self.assertRaises(SupplierNotFoundError):
            service.update_rate(self.repo, MISSING_ID, RateUpdate(monthly_rate=10.0), now=NOW)


class StatusTests(ServiceTestCase):
    def test_suspend_and_reactivate(self):
        workable = self.by_name("Workable")
        suspended = service.update_status(self.repo, workable.id, StatusUpdate(status="suspended"))
        self.assertEqual(suspended.status, SupplierStatus.SUSPENDED)
        active = service.update_status(self.repo, workable.id, StatusUpdate(status="active"))
        self.assertEqual(active.status, SupplierStatus.ACTIVE)

    def test_status_change_does_not_touch_updated_at(self):
        workable = self.by_name("Workable")
        updated = service.update_status(self.repo, workable.id, StatusUpdate(status="suspended"))
        self.assertEqual(updated.updated_at, SEEDED_AT)

    def test_status_unknown_id(self):
        with self.assertRaises(SupplierNotFoundError):
            service.update_status(self.repo, MISSING_ID, StatusUpdate(status="active"))


class DeleteTests(ServiceTestCase):
    def test_active_supplier_is_deleted_and_returned(self):
        workable = self.by_name("Workable")
        deleted = service.delete_supplier(self.repo, workable.id)
        self.assertEqual(deleted, workable)
        with self.assertRaises(SupplierNotFoundError):
            service.get_supplier(self.repo, workable.id)

    def test_suspended_supplier_is_kept(self):
        greenhouse = self.by_name("Greenhouse")
        with self.assertRaises(SuspendedSupplierDeletionError):
            service.delete_supplier(self.repo, greenhouse.id)
        self.assertEqual(service.get_supplier(self.repo, greenhouse.id), greenhouse)

    def test_delete_unknown_id(self):
        with self.assertRaises(SupplierNotFoundError):
            service.delete_supplier(self.repo, MISSING_ID)


class RoutesTests(unittest.TestCase):
    """El contrato que publica /docs: cada ruta del enunciado, con su método."""

    def test_supplier_routes_are_published(self):
        paths = create_app().openapi()["paths"]
        expected = {
            "/suppliers": {"get", "post"},
            "/suppliers/{supplier_id}": {"get", "delete"},
            "/suppliers/{supplier_id}/rate": {"patch"},
            "/suppliers/{supplier_id}/status": {"patch"},
        }
        for path, methods in expected.items():
            with self.subTest(path=path):
                self.assertEqual(set(paths[path]), methods)

    def test_post_answers_201(self):
        post = create_app().openapi()["paths"]["/suppliers"]["post"]
        self.assertIn("201", post["responses"])


if __name__ == "__main__":
    unittest.main()
