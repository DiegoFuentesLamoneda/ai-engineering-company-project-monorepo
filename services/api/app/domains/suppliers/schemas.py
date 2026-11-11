"""Modelos Pydantic del directorio de proveedores.

Es la puerta de entrada del dominio: todo lo que llega por la API pasa por
aquí antes de tocar la base de datos. Si un dato no cumple el BRIEFING
(docs/contexts/proyectos/supplier-directory.es.md), FastAPI responde 422 y
la petición no llega a ejecutarse.

Hay modelos separados para entrar y para salir:

- `SupplierCreate`, `RateUpdate` y `StatusUpdate`: lo que puede enviar el
  cliente. No incluyen `id` ni `updated_at`, que los pone el sistema, y
  rechazan cualquier campo que no conozcan (`extra="forbid"`).
- `Supplier`: lo que devuelve la API, con `id` y `updated_at`.

Los nombres de campo y los valores válidos son literales del BRIEFING.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class Country(StrEnum):
    """País del contrato activo."""

    SPAIN = "Spain"
    USA = "USA"


class Currency(StrEnum):
    EUR = "EUR"
    USD = "USD"


class Category(StrEnum):
    """Tipo de servicio que provee. Es `VALID_CATEGORIES` del BRIEFING."""

    JOB_BOARDS = "job_boards"
    ATS_SOFTWARE = "ats_software"
    ASSESSMENT_TOOLS = "assessment_tools"
    TRAINING_PLATFORMS = "training_platforms"
    PAYROLL_AND_HR_SOFTWARE = "payroll_and_hr_software"
    VIDEO_INTERVIEW = "video_interview"
    BACKGROUND_CHECK = "background_check"
    OFFICE_AND_FACILITIES = "office_and_facilities"
    IT_AND_SOFTWARE_LICENSES = "it_and_software_licenses"


class SupplierStatus(StrEnum):
    """Es `VALID_STATUSES` del BRIEFING. Un proveedor suspendido no se borra."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


# Restricción de negocio del BRIEFING: cada país factura en su moneda.
CURRENCY_BY_COUNTRY: dict[Country, Currency] = {
    Country.SPAIN: Currency.EUR,
    Country.USA: Currency.USD,
}

# Texto sin espacios sobrantes y no vacío: "  " no es un nombre.
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# Tarifa mensual: estrictamente mayor que cero. allow_inf_nan=False porque
# un float de Python acepta "infinito", que también es mayor que cero.
MonthlyRate = Annotated[float, Field(gt=0, allow_inf_nan=False)]

# Validación de forma, sin comprobar que el buzón exista. Una librería de
# emails sería una dependencia nueva para un campo opcional.
Email = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class SupplierFields(BaseModel):
    """Campos que escribe una persona. Base común de la entrada y la salida."""

    name: NonEmptyStr
    country: Country
    categories: list[Category] = Field(min_length=1)
    monthly_rate: MonthlyRate
    currency: Currency
    status: SupplierStatus
    # Pydantic exige el formato YYYY-MM-DD y devuelve la fecha en ese formato.
    contract_renewal_date: date | None = None
    contact_email: Email | None = None
    notes: str | None = None


class SupplierCreate(SupplierFields):
    """Cuerpo de `POST /suppliers`."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_business_rules(self) -> Self:
        # Se comprueba en el modelo y no en cada campo porque relaciona dos.
        expected = CURRENCY_BY_COUNTRY[self.country]
        if self.currency != expected:
            raise ValueError(
                f"Un proveedor de {self.country.value} debe facturar en {expected.value}, "
                f"no en {self.currency.value}."
            )
        if len(set(self.categories)) != len(self.categories):
            raise ValueError("Las categorías no pueden repetirse.")
        return self


class RateUpdate(BaseModel):
    """Cuerpo de `PATCH /suppliers/{id}/rate`."""

    model_config = ConfigDict(extra="forbid")

    monthly_rate: MonthlyRate


class StatusUpdate(BaseModel):
    """Cuerpo de `PATCH /suppliers/{id}/status`."""

    model_config = ConfigDict(extra="forbid")

    status: SupplierStatus


class Supplier(SupplierFields):
    """Un proveedor tal y como lo devuelve la API."""

    id: int
    # Fecha y hora (UTC) del último cambio de tarifa. La pone el sistema al
    # dar de alta el proveedor y en cada PATCH de la tarifa.
    updated_at: datetime
