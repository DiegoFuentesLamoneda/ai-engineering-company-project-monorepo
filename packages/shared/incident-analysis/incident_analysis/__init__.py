"""Incidencias de Nexova: análisis de ficheros de tickets y vocabulario del gestor.

La lógica que comparten los scripts (`scripts/analyze.py`,
`scripts/seed_incidents.py`) y la API `services/api`. Solo librería
estándar: sin dependencias de runtime.
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
    iter_rows,
    percentage,
)
from .catalog import (
    ALLOWED_TRANSITIONS,
    BRANCH_LABELS,
    DEFAULT_BRANCH,
    FINAL_STATUSES,
    TITLE_MAX_LENGTH,
    Branch,
    IncidentCategory,
    IncidentOrigin,
    IncidentStatus,
    can_transition,
)
from .export import EXPORT_COLUMNS, metric_rows, results_csv_text, write_results_csv
from .report import render_report
from .seeding import (
    REJECTION_LABELS,
    IncidentDraft,
    SeedPlan,
    plan_seed,
    plan_seed_file,
    transform_record,
)
from .validation import validate_record

__all__ = [
    "ALLOWED_TRANSITIONS",
    "BRANCH_LABELS",
    "DEFAULT_BRANCH",
    "EXPORT_COLUMNS",
    "FINAL_STATUSES",
    "REJECTION_LABELS",
    "TITLE_MAX_LENGTH",
    "AnalysisResult",
    "Branch",
    "EmptyFileError",
    "FileEncodingError",
    "IncidentCategory",
    "IncidentDraft",
    "IncidentFileError",
    "IncidentOrigin",
    "IncidentStatus",
    "InvalidRecord",
    "MissingColumnsError",
    "SeedPlan",
    "analyze_csv",
    "analyze_file",
    "can_transition",
    "iter_rows",
    "metric_rows",
    "percentage",
    "plan_seed",
    "plan_seed_file",
    "render_report",
    "results_csv_text",
    "transform_record",
    "validate_record",
    "write_results_csv",
]
