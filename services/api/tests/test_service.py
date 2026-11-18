"""Pruebas del service de incidencias: la subida, el último análisis y la exportación.

Se ejecutan desde services/api con el venv activo:
    python -m unittest discover -s tests
"""

from __future__ import annotations

import io
import json
import unittest
from pathlib import Path

from incident_analysis import (
    EmptyFileError,
    FileEncodingError,
    MissingColumnsError,
    analyze_file,
    results_csv_text,
)

from app.domains.incidents import service
from app.domains.incidents.exceptions import (
    FileTooLargeError,
    NoAnalysisYetError,
    UnsupportedFileTypeError,
)
from app.domains.incidents.schemas import AnalysisResponse

BRIEFING_CSV = Path(__file__).resolve().parents[3] / "scripts" / "incidents-nexova.csv"
MB = 1024 * 1024


def analyze_bytes(data: bytes, store: service.ResultsStore, filename: str = "tickets.csv"):
    return service.analyze_upload(
        io.BytesIO(data), filename=filename, size=len(data), max_bytes=10 * MB, store=store
    )


class CheckUploadTests(unittest.TestCase):
    def test_accepts_csv_extension_in_any_case(self):
        service.check_upload("tickets.csv", 100, MB)
        service.check_upload("EXPORT.CSV", 100, MB)

    def test_rejects_other_extensions_and_missing_name(self):
        for name in ("tickets.xlsx", "tickets.csv.exe", "tickets", "", None):
            with self.subTest(name=name), self.assertRaises(UnsupportedFileTypeError):
                service.check_upload(name, 100, MB)

    def test_rejects_files_over_the_limit(self):
        service.check_upload("tickets.csv", MB, MB)
        with self.assertRaises(FileTooLargeError) as caught:
            service.check_upload("tickets.csv", MB + 1, MB)
        self.assertIn("1 MB", str(caught.exception))


class AnalyzeUploadTests(unittest.TestCase):
    def setUp(self):
        self.store = service.ResultsStore()

    def test_briefing_file_gives_the_expected_numbers(self):
        result = analyze_bytes(BRIEFING_CSV.read_bytes(), self.store)
        self.assertEqual(
            (result.total_records, result.valid_records, result.invalid_records), (100, 96, 4)
        )
        self.assertEqual(round(result.average_score, 2), 3.84)

    def test_same_numbers_as_the_script(self):
        # La API y el script usan el mismo paquete: mismo fichero, mismo resultado.
        from_upload = analyze_bytes(BRIEFING_CSV.read_bytes(), self.store)
        self.assertEqual(from_upload, analyze_file(BRIEFING_CSV))

    def test_successful_analysis_becomes_the_last_one(self):
        result = analyze_bytes(BRIEFING_CSV.read_bytes(), self.store)
        self.assertIs(self.store.last(), result)

    def test_failed_analysis_keeps_the_previous_one(self):
        good = analyze_bytes(BRIEFING_CSV.read_bytes(), self.store)
        with self.assertRaises(EmptyFileError):
            analyze_bytes(b"", self.store)
        self.assertIs(self.store.last(), good)

    def test_content_errors_come_from_the_shared_package(self):
        cases = {
            b"": EmptyFileError,
            b"ticket_id,date\nNXV-000001,2026-01-01\n": MissingColumnsError,
            "ticket_id,descripción\n".encode("latin-1"): FileEncodingError,
        }
        for data, error in cases.items():
            with self.subTest(error=error.__name__), self.assertRaises(error):
                analyze_bytes(data, self.store)

    def test_accepts_the_excel_bom(self):
        data = b"\xef\xbb\xbf" + BRIEFING_CSV.read_bytes()
        self.assertEqual(analyze_bytes(data, self.store).total_records, 100)

    def test_leaves_the_upload_open(self):
        # FastAPI cierra el fichero subido al acabar la petición; si el
        # service lo cerrara antes, el cierre de FastAPI fallaría.
        stream = io.BytesIO(BRIEFING_CSV.read_bytes())
        service.analyze_upload(
            stream, filename="t.csv", size=None, max_bytes=10 * MB, store=self.store
        )
        self.assertFalse(stream.closed)

    def test_upload_checks_run_before_reading(self):
        with self.assertRaises(UnsupportedFileTypeError):
            analyze_bytes(BRIEFING_CSV.read_bytes(), self.store, filename="tickets.xlsx")
        self.assertIsNone(self.store.last())


class ResponseContractTests(unittest.TestCase):
    def setUp(self):
        store = service.ResultsStore()
        self.payload = analyze_bytes(BRIEFING_CSV.read_bytes(), store).to_dict()

    def test_package_output_matches_the_published_schema(self):
        # Si el paquete añade o renombra un campo y schemas.py no, esto falla
        # aquí y no en el backoffice.
        validated = AnalysisResponse.model_validate(self.payload, strict=True)
        self.assertEqual(validated.model_dump(), self.payload)

    def test_response_never_contains_an_email(self):
        self.assertNotIn("@", json.dumps(self.payload))


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.store = service.ResultsStore()

    def test_export_without_analysis_fails(self):
        with self.assertRaises(NoAnalysisYetError):
            service.export_last(self.store)

    def test_export_is_identical_to_the_script_output(self):
        analyze_bytes(BRIEFING_CSV.read_bytes(), self.store)
        self.assertEqual(
            service.export_last(self.store), results_csv_text(analyze_file(BRIEFING_CSV))
        )


if __name__ == "__main__":
    unittest.main()
