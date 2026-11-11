# `api` — backend de Nexova

API de Nexova Solutions sobre **FastAPI**. Es un **monolito modular por dominios**: un solo servicio con un paquete por área de negocio. Su razonamiento está en [`docs/ARCHITECTURE_PROPOSAL.md`](../../docs/ARCHITECTURE_PROPOSAL.md) y las decisiones vigentes, en [`memory-bank/techContext.md`](../../memory-bank/techContext.md).

Hoy tiene un dominio:

| Dominio | Qué hace | Rutas |
| --- | --- | --- |
| [`incidents`](./app/domains/incidents/) | Analiza la exportación CSV del helpdesk de soporte (Roberto Díaz). La validación y las métricas son las del paquete [`packages/incident-analysis/`](../../packages/incident-analysis/), las mismas que usa el script [`scripts/analyze.py`](../../scripts/analyze.py) | `POST /api/incidents/analyze` · `GET /api/incidents/results/export` |

## Puesta en marcha

Python 3.11 o superior y [uv](https://docs.astral.sh/uv/). Desde esta carpeta:

```powershell
uv sync                                         # crea .venv e instala lo que fija uv.lock
uv run uvicorn app.main:app --reload --port 8000
```

`uv run` ejecuta el comando dentro de `.venv` sin tener que activarlo. La documentación interactiva queda en http://localhost:8000/docs. Desde ahí se pueden probar todas las rutas sin el backoffice.

```powershell
uv run python -m unittest discover -s tests     # pruebas
uv run seed                                     # carga los proveedores del BRIEFING
```

`uv run seed` ([`app/seed.py`](./app/seed.py)) mete en la base de datos de TinyDB los 15 proveedores del [BRIEFING del directorio](../../docs/contexts/proyectos/supplier-directory.es.md). Se puede repetir sin miedo: salta los que ya están (por nombre) y dice cuántos ha insertado, cuántos ha saltado y cuántos hay en total. La base de datos es un fichero JSON en `storage/suppliers.json`. No se versiona: cada entorno crea la suya.

### Dependencias

Se declaran en [`pyproject.toml`](./pyproject.toml) y sus versiones exactas, incluidas las indirectas, quedan fijadas en [`uv.lock`](./uv.lock). Los dos se versionan: así todo el equipo instala exactamente lo mismo. Para añadir una, `uv add <paquete>`, que actualiza ambos. Añadir una dependencia es una decisión de arquitectura y se consulta antes (ver [`AGENTS.md`](../../AGENTS.md) §7).

El paquete compartido [`packages/incident-analysis/`](../../packages/incident-analysis/) se instala en modo editable (`[tool.uv.sources]`): un cambio en él se ve en la API sin reinstalar.

## Configuración

Se lee del entorno **una sola vez, al arrancar** ([`app/config.py`](./app/config.py)). Un valor inválido impide arrancar.

| Variable | Por defecto | Qué es |
| --- | --- | --- |
| `NEXOVA_API_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes que pueden llamar a la API desde el navegador, separados por comas. Nunca `*` |
| `NEXOVA_API_MAX_UPLOAD_MB` | `200` | Tamaño máximo del CSV subido. La exportación de producción puede llegar al millón de filas (~150 MB) |
| `NEXOVA_API_SUPPLIERS_DB_PATH` | `storage/suppliers.json` (dentro de esta carpeta) | Fichero de TinyDB del directorio de proveedores. La API y `uv run seed` leen la misma variable, así que siempre abren el mismo fichero |

Ninguna es secreta, así que no hay `.env`. Se cambian para una sesión con `$env:NEXOVA_API_MAX_UPLOAD_MB = "5"`.

## Estructura

```
app/
├─ main.py              compone la app: configuración, CORS y routers. Nada más
├─ config.py            configuración tipada, validada al arrancar
├─ dependencies.py      dependencias transversales (get_settings)
├─ seed.py              `uv run seed`: carga los proveedores del BRIEFING
└─ domains/
   ├─ incidents/
   │  ├─ router.py      HTTP: recibe la subida, llama al service, elige el código
   │  ├─ service.py     reglas de la subida y el último análisis. No importa fastapi
   │  ├─ schemas.py     contrato de salida (lo que publica /docs)
   │  ├─ exceptions.py  errores del dominio, sin HTTP
   │  └─ dependencies.py
   └─ suppliers/
      ├─ schemas.py     modelos Pydantic: entrada y salida separadas, reglas del BRIEFING
      ├─ database.py    TinyDB. El único módulo que la conoce
      └─ seed_data.py   los 15 proveedores del BRIEFING, copiados literalmente
storage/                base de datos de TinyDB (no se versiona)
tests/                  pruebas de los services, los modelos, la base de datos y la configuración
```

## Rutas de `incidents`

### `POST /api/incidents/analyze`

Subida `multipart/form-data` con el campo `file`. Devuelve el análisis en JSON (ver `AnalysisResponse` en `/docs`):

- totales;
- registros inválidos por regla;
- desglose por categoría y por estado, con porcentajes;
- satisfacción de los tickets `CLOSED`;
- hasta 50 filas inválidas de muestra, con su número de línea.

Los valores son **códigos** (`TECHNICAL`, `CLOSED`, `invalid_email`…). La traducción a texto de interfaz es cosa de cada aplicación.

| Código | Cuándo |
| --- | --- |
| `200` | Analizado. Pasa a ser el último análisis |
| `400` | Vacío, solo la cabecera o faltan columnas obligatorias |
| `413` | Supera `NEXOVA_API_MAX_UPLOAD_MB` |
| `415` | No tiene extensión `.csv` o no está en UTF-8 |
| `422` | La petición no trae el campo `file` (lo genera FastAPI) |

Todos los errores tienen la forma `{"detail": "mensaje"}`, en español y listos para mostrar.

### `GET /api/incidents/results/export`

El último análisis como CSV descargable (`results.csv`, una métrica por fila). Es **byte a byte el mismo fichero** que escribe el script. Devuelve `404` si todavía no se ha analizado nada.

## Decisiones

- **La API no calcula.** Toda la validación y las métricas están en `incident_analysis`. Aquí solo se añade lo propio de recibir un fichero por la red: extensión, tamaño y la conversión de bytes a texto.
- **Se lee en streaming.** FastAPI guarda la subida en un fichero temporal, y el análisis lo lee línea a línea. La memoria no crece con el tamaño del CSV.
- **La extensión decide, no el `Content-Type`.** El navegador deduce el tipo del sistema operativo: en un Windows con Excel, un `.csv` viaja como `application/vnd.ms-excel`. Lo que se valida de verdad es el contenido, UTF-8 y columnas.
- **Rutas síncronas (`def`).** El análisis es cálculo y lectura bloqueante. FastAPI ejecuta las rutas síncronas en un pool de hilos, así que un fichero grande no congela las demás peticiones.
- **El email del cliente no sale.** Ni en la respuesta, ni en los errores, ni en el log del servidor. Hay una prueba que comprueba que la respuesta no contiene ninguna `@`.
- **Un análisis fallido no borra el anterior.** El último análisis solo se sustituye cuando el nuevo termina bien.

## Limitaciones conocidas

- **"El último análisis" vive en la memoria del proceso.** El contrato de `GET /results/export` no dice qué análisis exportar, así que el servidor tiene que recordarlo. Eso implica tres cosas:
  1. Se pierde al reiniciar.
  2. Es común a todos los usuarios: si dos personas analizan a la vez, cada una puede descargar el resultado de la otra. Hoy solo contiene cifras agregadas, sin datos personales.
  3. No funciona con varios procesos (`--workers`), porque cada uno tiene su memoria.

  La solución de producción es que el `POST` devuelva un `analysis_id` y que la exportación lo reciba. Cambia el contrato, así que queda para cuando haya más de un usuario.
- **El límite de tamaño se comprueba después de recibir el fichero.** Protege el análisis, pero no la red. En producción el límite también va en el proxy (`client_max_body_size` en nginx).
- **TinyDB puede reutilizar un ID borrado.** Calcula el siguiente ID como el mayor que existe más uno. Si se borra el último proveedor y se reinicia el servidor, el siguiente que se cree recibe su ID, y un enlace antiguo abriría otro proveedor. Postgres, con secuencias, no tiene este problema.
- **Si se borra un proveedor del BRIEFING, `uv run seed` lo vuelve a crear.** El seeder decide por nombre qué falta y no puede distinguir un proveedor borrado a propósito de uno que nunca se cargó.
- **Las rutas se prueban a mano**, con el servidor arrancado. Las pruebas automáticas del router necesitan el cliente de pruebas de FastAPI, y este depende de `httpx`, que todavía no es una dependencia aprobada.
