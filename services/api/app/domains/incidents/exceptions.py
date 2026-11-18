"""Errores del dominio de incidencias.

No saben nada de HTTP: el `service` los lanza y el `router` decide el código
de respuesta. Los errores de contenido del fichero (vacío, sin columnas, no
UTF-8) ya los define el paquete `incident_analysis`: no se duplican aquí.

Ningún mensaje incluye datos de las filas, y menos un email.
"""


class IncidentUploadError(Exception):
    """Base de los errores de la subida, antes de leer el contenido."""


class UnsupportedFileTypeError(IncidentUploadError):
    def __init__(self) -> None:
        super().__init__("El fichero debe ser un CSV (extensión .csv).")


class FileTooLargeError(IncidentUploadError):
    def __init__(self, max_mb: int) -> None:
        super().__init__(f"El fichero supera el tamaño máximo de {max_mb} MB.")


class NoAnalysisYetError(Exception):
    def __init__(self) -> None:
        super().__init__("Todavía no se ha analizado ningún fichero: no hay resultados que exportar.")
