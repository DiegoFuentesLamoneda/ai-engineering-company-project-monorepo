"""Métricas, errores de fichero completo y privacidad del resultado."""

import io
import json
import unittest

from incident_analysis import (
    EmptyFileError,
    FileEncodingError,
    MissingColumnsError,
    analyze_csv,
    percentage,
)
from incident_analysis.analysis import MAX_INVALID_SAMPLES
from incident_analysis.schema import CATEGORIES, COLUMNS, STATUSES

from helpers import csv_lines, row


class MetricsTest(unittest.TestCase):
    def setUp(self):
        self.result = analyze_csv(
            csv_lines(
                row(category="TECHNICAL", status="CLOSED", satisfaction_score="4"),
                row(category="TECHNICAL", status="CLOSED", satisfaction_score="3"),
                row(category="BILLING", status="OPEN", satisfaction_score=""),
                row(category="ACCESS", status="DISCARDED", satisfaction_score=""),
                row(client_company="", customer_email="", satisfaction_score=""),
            )
        )

    def test_counts_valid_and_invalid_separately(self):
        self.assertEqual(self.result.total_records, 5)
        self.assertEqual(self.result.valid_records, 4)
        self.assertEqual(self.result.invalid_records, 1)

    def test_invalid_rows_count_once_but_every_rule_is_counted(self):
        # 1 fila inválida con 3 reglas rotas: las reglas suman 3, las filas 1.
        broken = {k: v for k, v in self.result.invalid_by_rule.items() if v}
        self.assertEqual(
            broken,
            {"missing_client_company": 1, "invalid_email": 1, "closed_without_score": 1},
        )

    def test_metrics_only_use_valid_records(self):
        self.assertEqual(self.result.by_category["TECHNICAL"], 2)
        # La fila inválida era ACCESS/CLOSED y no aparece en ningún desglose.
        self.assertEqual(self.result.by_category["ACCESS"], 1)
        self.assertEqual(self.result.by_status["CLOSED"], 2)

    def test_every_category_and_status_is_present_even_with_zero(self):
        self.assertEqual(tuple(self.result.by_category), CATEGORIES)
        self.assertEqual(tuple(self.result.by_status), STATUSES)
        self.assertEqual(self.result.by_category["COMPLAINT"], 0)
        self.assertEqual(self.result.by_category["HR_QUERY"], 0)

    def test_average_score_of_closed_tickets(self):
        self.assertEqual(self.result.average_score, 3.5)
        self.assertEqual(self.result.scored_closed_records, 2)

    def test_open_ticket_score_does_not_count_in_satisfaction(self):
        result = analyze_csv(
            csv_lines(
                row(status="CLOSED", satisfaction_score="2"),
                row(status="OPEN", satisfaction_score="5"),
            )
        )
        self.assertEqual(result.average_score, 2.0)
        self.assertEqual(result.score_distribution[5], 0)

    def test_no_closed_tickets_means_no_average(self):
        result = analyze_csv(csv_lines(row(status="OPEN", satisfaction_score="")))
        self.assertIsNone(result.average_score)
        self.assertIsNone(result.to_dict()["satisfaction"]["average_score"])


class InvalidSamplesTest(unittest.TestCase):
    def test_sample_points_to_the_file_line(self):
        result = analyze_csv(csv_lines(row(), row(category="")))
        [sample] = result.invalid_samples
        self.assertEqual(sample.line, 3)  # cabecera = 1, primera fila = 2
        self.assertEqual(sample.rules, ("invalid_category",))

    def test_malformed_ticket_id_is_not_echoed(self):
        result = analyze_csv(csv_lines(row(ticket_id="persona@example.com")))
        self.assertEqual(result.invalid_samples[0].ticket_id, "")

    def test_samples_are_capped(self):
        many = [row(category="") for _ in range(MAX_INVALID_SAMPLES + 10)]
        result = analyze_csv(csv_lines(*many))
        self.assertEqual(result.invalid_records, MAX_INVALID_SAMPLES + 10)
        self.assertEqual(len(result.invalid_samples), MAX_INVALID_SAMPLES)


class PrivacyTest(unittest.TestCase):
    def test_no_email_reaches_the_result(self):
        result = analyze_csv(
            csv_lines(
                row(customer_email="valido@example.com"),
                row(customer_email="invalido.example.com"),
                row(customer_email="otro@example.com", category=""),
            )
        )
        serialized = json.dumps(result.to_dict())
        self.assertNotIn("example.com", serialized)
        self.assertNotIn("@", serialized)


class FileErrorTest(unittest.TestCase):
    def test_empty_file(self):
        with self.assertRaises(EmptyFileError):
            analyze_csv([])

    def test_header_without_records(self):
        with self.assertRaises(EmptyFileError):
            analyze_csv(csv_lines())

    def test_missing_columns_are_listed(self):
        columns = tuple(c for c in COLUMNS if c not in ("status", "agent_id"))
        with self.assertRaises(MissingColumnsError) as ctx:
            analyze_csv(csv_lines(row(), columns=columns))
        self.assertEqual(ctx.exception.missing, ["agent_id", "status"])

    def test_header_with_bom_and_spaces_is_accepted(self):
        lines = csv_lines(row())
        lines[0] = "﻿" + lines[0].replace(",", " , ")
        self.assertEqual(analyze_csv(lines).valid_records, 1)

    def test_not_utf8(self):
        raw = "".join(csv_lines(row(client_company="Logística Ñandú"))).encode("latin-1")
        stream = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
        with self.assertRaises(FileEncodingError):
            analyze_csv(stream)


class PercentageTest(unittest.TestCase):
    def test_rounds_to_one_decimal(self):
        self.assertEqual(percentage(28, 96), 29.2)

    def test_never_divides_by_zero(self):
        self.assertEqual(percentage(0, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
