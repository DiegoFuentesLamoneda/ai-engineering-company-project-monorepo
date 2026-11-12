"""Errores del dominio de usuarios.

No saben nada de HTTP: el `service` los lanza y el `router` decide el código
de respuesta. Los mensajes no repiten el email: es un dato personal y los
mensajes de error acaban en logs.
"""


class EmailAlreadyRegisteredError(Exception):
    def __init__(self) -> None:
        super().__init__("Ya existe una cuenta con ese email.")


class UserNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("No existe ningún usuario con ese ID.")
