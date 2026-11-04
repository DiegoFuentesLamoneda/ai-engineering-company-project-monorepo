# `api` — backend de Nexova

API de Nexova Solutions sobre **FastAPI**. Es un **monolito modular por dominios**: un solo servicio con un paquete por área de negocio. Su razonamiento está en [`docs/ARCHITECTURE_PROPOSAL.md`](../../docs/ARCHITECTURE_PROPOSAL.md) y las decisiones vigentes, en [`memory-bank/techContext.md`](../../memory-bank/techContext.md).

Hoy tiene un dominio:

| Dominio | Qué hace | Rutas |
| --- | --- | --- |
| [`incidents`](./app/domains/incidents/) | Analiza la exportación CSV del helpdesk de soporte (Roberto Díaz). La validación y las métricas son las del paquete [`packages/incident-analysis/`](../../packages/incident-analysis/), las mismas que usa el script [`scripts/analyze.py`](../../scripts/analyze.py) | `POST /api/incidents/analyze` · `GET /api/incidents/results/export` |

## Puesta en marcha

Python 3.11 o superior. Desde esta carpeta, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt      # incluye el paquete compartido en modo editable
uvicorn app.main:app --reload --port 8000
```

La documentación interactiva queda en http://localhost:8000/docs. Desde ahí se puede subir un CSV y probar las dos rutas sin el backoffice.

```powershell
python -m unittest discover -s tests     # pruebas, con el venv activo
```

## Configuración

Se lee del entorno **una sola vez, al arrancar** ([`app/config.py`](./app/config.py)). Un valor inválido impide arrancar.

| Variable | Por defecto | Qué es |
| --- | --- | --- |
| `NEXOVA_API_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes que pueden llamar a la API desde el navegador, separados por comas. Nunca `*` |
| `NEXOVA_API_MAX_UPLOAD_MB` | `200` | Tamaño máximo del CSV subido. La exportación de producción puede llegar al millón de filas (~150 MB) |

Ninguna es secreta, así que no hay `.env`. Se cambian para una sesión con `$env:NEXOVA_API_MAX_UPLOAD_MB = "5"`.

## Estructura

```
app/
├─ main.py              compone la app: configuración, CORS y routers. Nada más
├─ config.py            configuración tipada, validada al arrancar
├─ dependencies.py      dependencias transversales (get_settings)
└─ domains/
   └─ incidents/
      ├─ router.py      HTTP: recibe la subida, llama al service, elige el código
      ├─ service.py     reglas de la subida y el último análisis. No importa fastapi
      ├─ schemas.py     contrato de salida (lo que publica /docs)
      ├─ exceptions.py  errores del dominio, sin HTTP
      └─ dependencies.py
tests/                  pruebas del service y de la configuración
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
- **Las rutas se prueban a mano**, con el servidor arrancado. Las pruebas automáticas del router necesitan el cliente de pruebas de FastAPI, y este depende de `httpx`, que todavía no es una dependencia aprobada.
