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


# --- Gestor de incidencias ---------------------------------------------------
# Los mensajes usan los códigos (`open`, `in_progress`…), no textos de
# interfaz: cada aplicación los traduce a su idioma.


class IncidentNotFoundError(Exception):
    def __init__(self, incident_id: object) -> None:
        super().__init__(f"No existe ninguna incidencia con el ID {incident_id}.")


class InvalidTransitionError(Exception):
    """El ciclo de vida no permite pasar del estado actual al pedido."""

    def __init__(self, current: str, target: str, allowed: list[str]) -> None:
        if current == target:
            message = f"La incidencia ya está en '{current}'."
        elif not allowed:
            message = f"'{current}' es un estado final: la incidencia ya no cambia de estado."
        else:
            message = (
                f"Una incidencia en '{current}' no puede pasar a '{target}'. "
                f"Desde '{current}' solo se puede pasar a: {', '.join(allowed)}."
            )
        super().__init__(message)


class StatusChangedError(Exception):
    """Otra petición cambió el estado entre la lectura y la escritura."""

    def __init__(self) -> None:
        super().__init__(
            "Alguien ha cambiado el estado de esta incidencia mientras tanto. "
            "Vuelve a cargarla y decide con el estado actual."
        )
