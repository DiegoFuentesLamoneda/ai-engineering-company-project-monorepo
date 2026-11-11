"""Pruebas del modelo de proveedor: cada regla del BRIEFING rechaza lo que debe.

Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from pydantic import ValidationError

from app.domains.suppliers.schemas import (
    Category,
    Country,
    Currency,
    RateUpdate,
    StatusUpdate,
    Supplier,
    SupplierCreate,
    SupplierStatus,
)

# Un proveedor del BRIEFING, con todos los campos.
LINKEDIN = {
    "name": "LinkedIn Talent Solutions",
    "country": "Spain",
    "categories": ["job_boards"],
    "monthly_rate": 1200.0,
    "currency": "EUR",
    "status": "active",
    "contract_renewal_date": "2025-03-31",
    "contact_email": "account@linkedin.com",
    "notes": "Licencia corporativa para publicación de ofertas y búsqueda de candidatos.",
}


def with_changes(**changes) -> dict:
    return {**LINKEDIN, **changes}


def without(field: str) -> dict:
    data = dict(LINKEDIN)
    del data[field]
    return data


class SupplierCreateTests(unittest.TestCase):
    def assertRejected(self, data: dict) -> None:
        with self.assertRaises(ValidationError):
            SupplierCreate.model_validate(data)

    def test_accepts_a_briefing_supplier(self):
        supplier = SupplierCreate.model_validate(LINKEDIN)
        self.assertEqual(supplier.country, Country.SPAIN)
        self.assertEqual(supplier.categories, [Category.JOB_BOARDS])
        self.assertEqual(supplier.contract_renewal_date, date(2025, 3, 31))

    def test_optional_fields_can_be_missing(self):
        minimal = {k: LINKEDIN[k] for k in ("name", "country", "categories", "monthly_rate", "currency", "status")}
        supplier = SupplierCreate.model_validate(minimal)
        self.assertIsNone(supplier.contract_renewal_date)
        self.assertIsNone(supplier.contact_email)
        self.assertIsNone(supplier.notes)

    def test_required_fields(self):
        for field in ("name", "country", "categories", "monthly_rate", "currency", "status"):
            with self.subTest(field=field):
                self.assertRejected(without(field))

    def test_status_only_accepts_briefing_values(self):
        for status in ("inactive", "Active", "paused", ""):
            with self.subTest(status=status):
                self.assertRejected(with_changes(status=status))

    def test_monthly_rate_must_be_positive(self):
        for rate in (0, 0.0, -1, -1200.0, float("inf"), float("nan")):
            with self.subTest(rate=rate):
                self.assertRejected(with_changes(monthly_rate=rate))

    def test_country_only_accepts_spain_or_usa(self):
        for country in ("Mexico", "spain", "ES", ""):
            with self.subTest(country=country):
                self.assertRejected(with_changes(country=country))

    def test_currency_must_match_country(self):
        self.assertRejected(with_changes(country="Spain", currency="USD"))
        self.assertRejected(with_changes(country="USA", currency="EUR"))
        usa = SupplierCreate.model_validate(with_changes(country="USA", currency="USD"))
        self.assertEqual(usa.currency, Currency.USD)

    def test_categories_need_at_least_one_valid_value(self):
        self.assertRejected(with_changes(categories=[]))
        self.assertRejected(with_changes(categories=["catering"]))
        self.assertRejected(with_changes(categories="job_boards"))

    def test_categories_cannot_repeat(self):
        self.assertRejected(with_changes(categories=["job_boards", "job_boards"]))

    def test_several_categories_are_allowed(self):
        supplier = SupplierCreate.model_validate(with_changes(categories=["job_boards", "ats_software"]))
        self.assertEqual(len(supplier.categories), 2)

    def test_blank_name_is_rejected(self):
        self.assertRejected(with_changes(name="   "))

    def test_name_is_trimmed(self):
        self.assertEqual(SupplierCreate.model_validate(with_changes(name="  Workable ")).name, "Workable")

    def test_renewal_date_must_be_yyyy_mm_dd(self):
        for value in ("31/03/2025", "2025-13-01", "mañana"):
            with self.subTest(value=value):
                self.assertRejected(with_changes(contract_renewal_date=value))

    def test_contact_email_needs_email_shape(self):
        for value in ("account", "account@", "@linkedin.com", "a b@linkedin.com"):
            with self.subTest(value=value):
                self.assertRejected(with_changes(contact_email=value))

    def test_client_cannot_send_system_fields(self):
        # updated_at e id los pone el sistema: si llegan, la petición se rechaza.
        self.assertRejected(with_changes(updated_at="2026-01-01T00:00:00Z"))
        self.assertRejected(with_changes(id=99))

    def test_unknown_fields_are_rejected(self):
        self.assertRejected(with_changes(rate=100))


class PatchBodyTests(unittest.TestCase):
    def test_rate_update(self):
        self.assertEqual(RateUpdate.model_validate({"monthly_rate": 1350.5}).monthly_rate, 1350.5)
        for rate in (0, -10, float("inf")):
            with self.subTest(rate=rate), self.assertRaises(ValidationError):
                RateUpdate.model_validate({"monthly_rate": rate})
        with self.assertRaises(ValidationError):
            RateUpdate.model_validate({"monthly_rate": 100, "updated_at": "2026-01-01T00:00:00Z"})

    def test_status_update(self):
        self.assertEqual(StatusUpdate.model_validate({"status": "suspended"}).status, SupplierStatus.SUSPENDED)
        for status in ("inactive", "deleted", None):
            with self.subTest(status=status), self.assertRaises(ValidationError):
                StatusUpdate.model_validate({"status": status})


class SupplierResponseTests(unittest.TestCase):
    def test_serializes_with_id_and_updated_at(self):
        supplier = Supplier.model_validate(
            {**LINKEDIN, "id": 1, "updated_at": datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)}
        )
        data = supplier.model_dump(mode="json")
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["updated_at"], "2026-11-11T12:00:00Z")
        # La fecha sale en el mismo formato en que entró.
        self.assertEqual(data["contract_renewal_date"], "2025-03-31")
        self.assertEqual(data["status"], "active")


if __name__ == "__main__":
    unittest.main()
