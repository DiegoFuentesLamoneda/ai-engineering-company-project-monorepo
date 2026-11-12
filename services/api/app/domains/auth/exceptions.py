"""Errores del dominio de autenticación. Sin HTTP: la dependencia decide el 401."""


class InvalidTokenError(Exception):
    """Firma incorrecta, caducado, mal formado o sin usuario.

    Un solo error para todos los casos, a propósito: a quien manda un token
    malo no se le explica qué ha fallado.
    """

    def __init__(self) -> None:
        super().__init__("Token no válido o caducado.")
