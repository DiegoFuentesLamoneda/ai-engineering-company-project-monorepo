"""Prueba de aceptación: los valores esperados del briefing, literalmente.

docs/contexts/proyectos/incidents-file-analysis.es.md, sección
"Distribución de datos". Si esta prueba falla, el análisis no se entrega.
"""

import csv
import io
import unittest
from pathlib import Path

from incident_analysis import analyze_file, render_report, write_results_csv

SAMPLE = Path(__file__).resolve().parents[3] / "scripts" / "incidents-nexova.csv"


class BriefingAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze_file(SAMPLE)

    def test_totals(self):
        self.assertEqual(self.result.total_records, 100)
        self.assertEqual(self.result.valid_records, 96)
        self.assertEqual(self.result.invalid_records, 4)

    def test_invalid_rules(self):
        broken = {code: n for code, n in self.result.invalid_by_rule.items() if n}
        self.assertEqual(
            broken,
            {
                "missing_client_company": 1,
                "invalid_category": 1,
                "invalid_email": 1,
                "closed_without_score": 1,
            },
        )

    def test_categories(self):
        self.assertEqual(
            self.result.by_category,
            {"TECHNICAL": 28, "BILLING": 18, "ACCESS": 21, "HR_QUERY": 17, "COMPLAINT": 12},
        )

    def test_statuses(self):
        self.assertEqual(self.result.by_status, {"OPEN": 27, "CLOSED": 56, "DISCARDED": 13})

    def test_percentages(self):
        data = self.result.to_dict()
        self.assertEqual(
            [c["percentage"] for c in data["by_category"]], [29.2, 18.8, 21.9, 17.7, 12.5]
        )
        self.assertEqual([s["percentage"] for s in data["by_status"]], [28.1, 58.3, 13.5])

    def test_satisfaction(self):
        self.assertEqual(self.result.closed_records, 56)
        self.assertEqual(self.result.scored_closed_records, 56)
        self.assertEqual(self.result.score_distribution, {1: 2, 2: 5, 3: 10, 4: 22, 5: 17})
        self.assertEqual(self.result.to_dict()["satisfaction"]["average_score"], 3.84)

    def test_report_shows_the_expected_figures(self):
        report = render_report(self.result, SAMPLE.name)
        for expected in ("Average score: 3.84 / 5.00", "Scored tickets: 56 of 56", "(29.2%)"):
            self.assertIn(expected, report)

    def test_no_output_contains_an_email(self):
        buffer = io.StringIO()
        write_results_csv(self.result, buffer)
        for output in (render_report(self.result, SAMPLE.name), buffer.getvalue()):
            self.assertNotIn("@", output)

    def test_export_has_one_metric_per_row(self):
        buffer = io.StringIO()
        count = write_results_csv(self.result, buffer)
        rows = list(csv.reader(io.StringIO(buffer.getvalue())))
        self.assertEqual(rows[0], ["section", "metric", "value"])
        self.assertEqual(len(rows) - 1, count)
        self.assertTrue(all(len(r) == 3 for r in rows))
        self.assertIn(["satisfaction", "average_score", "3.84"], rows)


if __name__ == "__main__":
    unittest.main()
