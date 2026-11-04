"""Análisis de ficheros de tickets de soporte de Nexova.

La lógica que comparten el script `scripts/analyze.py` y la API
`services/api`. Solo librería estándar: sin dependencias de runtime.
"""

from .analysis import (
    AnalysisResult,
    EmptyFileError,
    FileEncodingError,
    IncidentFileError,
    InvalidRecord,
    MissingColumnsError,
    analyze_csv,
    analyze_file,
    percentage,
)
from .export import EXPORT_COLUMNS, metric_rows, results_csv_text, write_results_csv
from .report import render_report
from .validation import validate_record

__all__ = [
    "EXPORT_COLUMNS",
    "AnalysisResult",
    "EmptyFileError",
    "FileEncodingError",
    "IncidentFileError",
    "InvalidRecord",
    "MissingColumnsError",
    "analyze_csv",
    "analyze_file",
    "metric_rows",
    "percentage",
    "render_report",
    "results_csv_text",
    "validate_record",
    "write_results_csv",
]
