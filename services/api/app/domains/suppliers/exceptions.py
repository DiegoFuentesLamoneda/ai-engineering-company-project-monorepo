"""Errores del dominio de proveedores.

No saben nada de HTTP: el `service` los lanza y el `router` decide el código
de respuesta.
"""


class SupplierNotFoundError(Exception):
    def __init__(self, supplier_id: int) -> None:
        super().__init__(f"No existe ningún proveedor con el ID {supplier_id}.")


class SuspendedSupplierDeletionError(Exception):
    """El BRIEFING: un proveedor suspendido no se elimina, para no perder el historial."""

    def __init__(self, name: str) -> None:
        super().__init__(
            f"{name} está suspendido y los proveedores suspendidos no se eliminan: "
            "se conservan para mantener el historial de relaciones comerciales."
        )
