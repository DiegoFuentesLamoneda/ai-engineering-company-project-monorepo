"""El 400 del gestor de incidencias: errores de validación que se entienden.

FastAPI responde 422 cuando el cuerpo, la ruta o la query no cumplen el
modelo, con los mensajes de Pydantic en inglés técnico ("Input should be
'open', 'in_progress'..."). El gestor pide otra cosa: 400 y un mensaje que
diga qué campo falla. Este módulo hace las dos cosas:

- `describe_errors` traduce cada error de Pydantic a un `FieldError` con un
  código estable (`missing`, `too_long`…) que el formulario puede traducir a
  su idioma, y un mensaje en español para quien lea la API directamente.
- `IncidentManagerRoute` aplica esa traducción **solo a las rutas del
  gestor**. El analizador y el resto de dominios siguen con su 422: su
  contrato ya está entregado y el backoffice cuenta con él.

Los mensajes nunca repiten lo que escribió el usuario salvo un valor corto
de un desplegable: un título de 5 000 caracteres no vuelve en la respuesta.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine, Sequence
from typing import Any

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from .schemas import FieldError, ValidationErrorResponse

# Cuánto de un valor inválido se repite en el mensaje, como mucho.
ECHO_MAX_LENGTH = 40

# De dónde viene el dato, para nombrarlo como lo ve quien llama.
_WHERE = {"body": "El campo", "query": "El filtro", "path": "El parámetro"}


def _field_name(loc: Sequence[Any]) -> tuple[str, str]:
    """`("body", "title")` → `("body", "title")`; `("body",)` → `("body", "")`."""
    where = str(loc[0]) if loc else "body"
    name = ".".join(str(part) for part in loc[1:])
    return where, name


def _echo(value: Any) -> str:
    text = str(value)
    return text if len(text) <= ECHO_MAX_LENGTH else text[:ECHO_MAX_LENGTH] + "…"


def describe_error(error: dict[str, Any]) -> FieldError:
    """Un error de Pydantic → un `FieldError` con código y mensaje en español."""
    where, name = _field_name(error.get("loc", ()))
    kind = error.get("type", "")
    ctx = error.get("ctx") or {}

    # Errores del cuerpo entero, no de un campo: JSON roto o que no es un objeto.
    if where == "body" and (not name or kind == "json_invalid"):
        if kind == "missing":
            message = "Falta el cuerpo de la petición: debe ser un objeto JSON."
        elif kind == "json_invalid":
            message = "El cuerpo de la petición no es un JSON válido."
        else:
            message = "El cuerpo de la petición debe ser un objeto JSON con los campos de la incidencia."
        return FieldError(field="body", code="invalid_body", message=message)

    subject = f"{_WHERE.get(where, 'El campo')} '{name}'"
    if kind == "missing":
        code, message = "missing", f"{subject} es obligatorio."
    elif kind == "string_too_short":
        code, message = "blank", f"{subject} no puede estar vacío."
    elif kind == "string_too_long":
        limit = ctx.get("max_length")
        code, message = "too_long", f"{subject} admite como máximo {limit} caracteres."
    elif kind == "enum":
        code = "invalid_choice"
        value = _echo(error.get("input"))
        message = f"{subject} no admite el valor '{value}'. Valores válidos: {ctx.get('expected')}."
    elif kind == "string_type":
        code, message = "not_text", f"{subject} debe ser texto."
    elif kind == "extra_forbidden":
        code, message = "not_allowed", f"{subject} no se puede enviar: lo pone el sistema o no existe."
    elif kind.startswith("uuid"):
        code, message = "invalid_id", f"{subject} no es un ID de incidencia válido."
    else:
        code, message = "invalid", f"{subject} no es válido."
    return FieldError(field=name, code=code, message=message)


def describe_errors(errors: Sequence[dict[str, Any]]) -> ValidationErrorResponse:
    described = [describe_error(error) for error in errors]
    # Un campo, un error: un título vacío no debe salir dos veces.
    unique = list({(e.field, e.code): e for e in described}.values())
    return ValidationErrorResponse(detail=" ".join(e.message for e in unique), errors=unique)


class IncidentManagerRoute(APIRoute):
    """Ruta de FastAPI que responde 400 (y no 422) cuando la petición no valida.

    Es el mecanismo que documenta FastAPI para personalizar una ruta
    ("Custom Request and APIRoute class"): envuelve el manejador de la ruta y
    captura el error de validación antes de que llegue al manejador global.
    Al ir en el router, afecta solo a las rutas declaradas con esta clase.
    """

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def route_handler(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as error:
                body = describe_errors(error.errors())
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=body.model_dump())

        return route_handler
