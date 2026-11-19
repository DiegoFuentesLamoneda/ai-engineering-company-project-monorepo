"""Transformación CSV -> modelo del seed del gestor de incidencias.

La última clase es la prueba de aceptación: los valores esperados tras el
seed, copiados del briefing (centralized-incident-manager.es.md, sección
"Valores esperados tras el seed"). Si falla, el seed no se entrega.
"""

import unittest
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from helpers import csv_lines, row

from incident_analysis import (
    REJECTION_LABELS,
    TITLE_MAX_LENGTH,
    EmptyFileError,
    MissingColumnsError,
    plan_seed,
    plan_seed_file,
    transform_record,
)
from incident_analysis.seeding import CATEGORY_MAP, STATUS_MAP, make_title

SAMPLE = Path(__file__).resolve().parents[4] / "scripts" / "incidents-nexova.csv"


class TransformRecordTest(unittest.TestCase):
    def test_valid_row(self):
        draft, errors = transform_record(row())
        self.assertEqual(errors, ())
        self.assertEqual(draft.source_id, "NXV-000001")
        self.assertEqual(draft.title, "Role permissions not updated")
        self.assertEqual(draft.description, "Role permissions not updated")
        self.assertEqual(draft.category, "technical_failure")  # ACCESS
        self.assertEqual(draft.status, "resolved")  # CLOSED
        self.assertEqual(draft.origin, "customer")
        self.assertEqual(draft.branch, "central")

    def test_dates_are_midnight_utc(self):
        draft, _ = transform_record(row(date="2024-01-18"))
        self.assertEqual(draft.created_at, datetime(2024, 1, 18, tzinfo=UTC))
        self.assertEqual(draft.updated_at, draft.created_at)

    def test_status_map(self):
        self.assertEqual(
            {k: v.value for k, v in STATUS_MAP.items()},
            {"OPEN": "open", "CLOSED": "resolved", "DISCARDED": "discarded"},
        )

    def test_category_map(self):
        self.assertEqual(
            {k: v.value for k, v in CATEGORY_MAP.items()},
            {
                "TECHNICAL": "technical_failure",
                "BILLING": "process_error",
                "ACCESS": "technical_failure",
                "HR_QUERY": "process_error",
                "COMPLAINT": "client_complaint",
            },
        )

    def test_every_csv_value_has_a_mapping(self):
        # Si el analizador acepta un valor nuevo, el seed tiene que saber mapearlo.
        from incident_analysis.schema import CATEGORIES, STATUSES

        self.assertEqual(set(STATUS_MAP), set(STATUSES))
        self.assertEqual(set(CATEGORY_MAP), set(CATEGORIES))

    def test_open_ticket_without_score(self):
        draft, errors = transform_record(row(status="OPEN", satisfaction_score=""))
        self.assertEqual(errors, ())
        self.assertEqual(draft.status, "open")

    def test_invalid_row_reuses_the_analyzer_rules(self):
        draft, errors = transform_record(row(client_company="", customer_email="sin-arroba"))
        self.assertIsNone(draft)
        self.assertEqual(set(errors), {"missing_client_company", "invalid_email"})

    def test_every_rejection_code_has_a_label(self):
        for code in ("missing_client_company", "unmapped_status", "empty_title"):
            self.assertIn(code, REJECTION_LABELS)


class TitleTest(unittest.TestCase):
    def test_long_description_is_cut_at_120(self):
        description = "x" * 200
        draft, _ = transform_record(row(description=description))
        self.assertEqual(len(draft.title), TITLE_MAX_LENGTH)
        # La descripción se copia entera.
        self.assertEqual(draft.description, description)

    def test_title_is_trimmed_after_cutting(self):
        # Si el corte cae justo después de un espacio, no queda colgando.
        description = "a" * 119 + " resto de la frase"
        self.assertEqual(make_title(description), "a" * 119)

    def test_title_is_trimmed_before_cutting(self):
        self.assertEqual(make_title("   Login roto   "), "Login roto")

    def test_empty_title(self):
        self.assertEqual(make_title("     "), "")


class PlanSeedTest(unittest.TestCase):
    def test_counts_and_line_numbers(self):
        plan = plan_seed(csv_lines(row(), row(ticket_id="NXV-000002", category="NOPE")))
        self.assertEqual(plan.total_records, 2)
        self.assertEqual(len(plan.drafts), 1)
        self.assertEqual(len(plan.rejected), 1)
        rejected = plan.rejected[0]
        self.assertEqual(rejected.line, 3)  # la cabecera es la 1
        self.assertEqual(rejected.ticket_id, "NXV-000002")
        self.assertEqual(rejected.rules, ("invalid_category",))

    def test_malformed_ticket_id_is_not_shown(self):
        plan = plan_seed(csv_lines(row(ticket_id="persona@example.com")))
        self.assertEqual(plan.rejected[0].ticket_id, "")

    def test_file_errors_are_the_analyzer_ones(self):
        with self.assertRaises(EmptyFileError):
            plan_seed([])
        with self.assertRaises(MissingColumnsError):
            plan_seed(csv_lines(row(), columns=("ticket_id", "date")))


class BriefingSeedAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = plan_seed_file(SAMPLE)

    def test_96_valid_and_4_rejected(self):
        self.assertEqual(self.plan.total_records, 100)
        self.assertEqual(len(self.plan.drafts), 96)
        self.assertEqual(len(self.plan.rejected), 4)

    def test_status_totals(self):
        self.assertEqual(
            Counter(d.status.value for d in self.plan.drafts),
            {"open": 27, "resolved": 56, "discarded": 13},
        )

    def test_category_totals(self):
        self.assertEqual(
            Counter(d.category.value for d in self.plan.drafts),
            {"technical_failure": 49, "process_error": 35, "client_complaint": 12},
        )

    def test_all_customer_from_central(self):
        self.assertEqual({d.origin.value for d in self.plan.drafts}, {"customer"})
        self.assertEqual({d.branch.value for d in self.plan.drafts}, {"central"})

    def test_ticket_ids_are_unique(self):
        # Es la clave de idempotencia: dos filas con el mismo ticket_id se
        # tomarían por la misma incidencia.
        ids = [d.source_id for d in self.plan.drafts]
        self.assertEqual(len(set(ids)), 96)

    def test_title_and_date_are_not_unique(self):
        # Por eso la idempotencia va por ticket_id y no por título + fecha, la
        # alternativa del briefing: en el CSV hay filas distintas con la misma
        # descripción y el mismo día.
        keys = {(d.title, d.created_at) for d in self.plan.drafts}
        self.assertLess(len(keys), 96)


if __name__ == "__main__":
    unittest.main()
