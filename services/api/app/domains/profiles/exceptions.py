"""Errores del dominio de perfiles. Sin HTTP: el router decide el código."""


class ProfileAlreadyExistsError(Exception):
    """El vínculo es uno a uno: un usuario no puede tener dos perfiles."""

    def __init__(self) -> None:
        super().__init__("Ese usuario ya tiene un perfil.")

