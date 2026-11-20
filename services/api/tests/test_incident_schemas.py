"""Pruebas del modelo de incidencia: cada restricción rechaza lo que debe.

Se ejecutan desde services/api:
    uv run python -m unittest discover -s tests
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pydantic import ValidationError

from app.domains.incidents.schemas import (
    DESCRIPTION_MAX_LENGTH,
    Incident,
    IncidentCreate,
    StatusUpdate,
)

# Lo que enviaría el formulario.
VALID_CREATE = {
    "title": "El ATS no carga las candidaturas",
    "description": "Desde las 9:00 el ATS devuelve un error al abrir cualquier candidatura.",
    "category": "technical_failure",
    "origin": "branch",
    "branch": "miami_office",
}

NOW = datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc)


def stored(**changes) -> dict:
    """Una incidencia tal y como se guarda, con los cambios que pida la prueba."""
    return {
        "id": str(uuid4()),
        **VALID_CREATE,
        "status": "open",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    } | changes


def error_fields(error: ValidationError) -> set[str]:
    """Los campos que señala el error: es lo que leerá el 400 de la API."""
    return {".".join(str(part) for part in e["loc"]) for e in error.errors()}


class IncidentCreateTests(unittest.TestCase):
    def test_valid_body(self):
        data = IncidentCreate.model_validate(VALID_CREATE)
        self.assertEqual(data.branch, "miami_office")
        self.assertEqual(data.category, "technical_failure")

    def test_every_field_is_required(self):
        for field in VALID_CREATE:
            body = {k: v for k, v in VALID_CREATE.items() if k != field}
            with self.subTest(field=field), self.assertRaises(ValidationError) as ctx:
                IncidentCreate.model_validate(body)
            self.assertEqual(error_fields(ctx.exception), {field})

    def test_values_outside_the_briefing_are_rejected(self):
        cases = {
            "category": "TECHNICAL",  # valor del CSV, no del gestor
            "origin": "email",
            "branch": "headquarters",  # el briefing pide usar central
        }
        for field, value in cases.items():
            with self.subTest(field=field), self.assertRaises(ValidationError) as ctx:
                IncidentCreate.model_validate(VALID_CREATE | {field: value})
            self.assertEqual(error_fields(ctx.exception), {field})

    def test_blank_text_is_rejected(self):
        for field in ("title", "description"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                IncidentCreate.model_validate(VALID_CREATE | {field: "    "})

    def test_text_is_trimmed(self):
        data = IncidentCreate.model_validate(VALID_CREATE | {"title": "  Login roto  "})
        self.assertEqual(data.title, "Login roto")

    def test_title_up_to_120_characters(self):
        IncidentCreate.model_validate(VALID_CREATE | {"title": "x" * 120})
        with self.assertRaises(ValidationError):
            IncidentCreate.model_validate(VALID_CREATE | {"title": "x" * 121})

    def test_description_has_a_limit(self):
        IncidentCreate.model_validate(VALID_CREATE | {"description": "x" * DESCRIPTION_MAX_LENGTH})
        with self.assertRaises(ValidationError):
            IncidentCreate.model_validate(VALID_CREATE | {"description": "x" * (DESCRIPTION_MAX_LENGTH + 1)})

    def test_status_and_system_fields_cannot_be_sent(self):
        # Toda incidencia nace open; id y fechas las pone el sistema.
        for field, value in {"status": "resolved", "id": str(uuid4()), "created_at": NOW.isoformat()}.items():
            with self.subTest(field=field), self.assertRaises(ValidationError) as ctx:
                IncidentCreate.model_validate(VALID_CREATE | {field: value})
            self.assertEqual(error_fields(ctx.exception), {field})


class StatusUpdateTests(unittest.TestCase):
    def test_known_status(self):
        self.assertEqual(StatusUpdate.model_validate({"status": "in_progress"}).status, "in_progress")

    def test_unknown_status(self):
        for value in ("closed", "CLOSED", "", None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                StatusUpdate.model_validate({"status": value})


class IncidentTests(unittest.TestCase):
    def test_valid_incident(self):
        incident = Incident.model_validate(stored())
        self.assertEqual(incident.status, "open")
        self.assertEqual(incident.created_at, NOW)

    def test_dates_need_a_timezone(self):
        with self.assertRaises(ValidationError):
            Incident.model_validate(stored(created_at="2026-11-19T10:00:00"))

    def test_updated_at_cannot_be_before_created_at(self):
        earlier = (NOW - timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValidationError):
            Incident.model_validate(stored(updated_at=earlier))

    def test_stored_description_is_not_trimmed(self):
        # El seed copia la descripción del CSV literalmente.
        incident = Incident.model_validate(stored(description=" con espacios "))
        self.assertEqual(incident.description, " con espacios ")

    def test_json_keeps_the_codes(self):
        data = Incident.model_validate(stored()).model_dump(mode="json")
        self.assertEqual(data["branch"], "miami_office")
        self.assertNotIn("ticket_id", data)


if __name__ == "__main__":
    unittest.main()
