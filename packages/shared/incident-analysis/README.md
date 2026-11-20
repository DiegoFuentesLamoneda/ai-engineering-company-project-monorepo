# `incident-analysis` — lógica compartida de incidencias

Dos cosas que comparten los scripts y la API de Nexova, sin duplicar una línea:

1. **El análisis del CSV de tickets de soporte** que exporta el helpdesk del servicio externalizado: validación y métricas. Lo usan el script [`scripts/analyze.py`](../../../scripts/analyze.py) y la API [`services/api/`](../../../services/api/) (`POST /api/incidents/analyze`).
2. **El vocabulario del gestor de incidencias centralizado** y la transformación del CSV histórico a su modelo: estados, categorías, orígenes, sedes y transiciones. Lo usan el seed [`scripts/seed_incidents.py`](../../../scripts/) y la API (`/api/incidents`).

Es **la única implementación** de todo ello en el monorepo. Si una regla cambia, cambia aquí y todos los consumidores se enteran a la vez.

Especificaciones, copiadas **literalmente**:

| Briefing | Dónde se copia |
| --- | --- |
| [`incidents-file-analysis.es.md`](../../../docs/contexts/proyectos/incidents-file-analysis.es.md): columnas, valores, reglas y valores esperados del CSV | [`schema.py`](./incident_analysis/schema.py) |
| [`centralized-incident-manager.es.md`](../../../docs/contexts/proyectos/centralized-incident-manager.es.md): estados, categorías, orígenes, sedes y transiciones | [`catalog.py`](./incident_analysis/catalog.py) |
| El mismo briefing, sección "Datos históricos — seed desde CSV": mapeos de estado y categoría, título y fechas | [`seeding.py`](./incident_analysis/seeding.py) |

Vive en [`packages/shared/`](../) porque el enunciado del gestor de incidencias pide que la validación del analizador esté ahí y la reutilicen el script y la API. Hasta entonces estaba en `packages/incident-analysis/`.

## Por qué existe

El fichero contiene emails de clientes finales. No puede enviarse a ninguna herramienta de IA externa, así que el análisis tiene que hacerse en casa y con código determinista.

## Módulos

| Archivo | Qué hace |
| --- | --- |
| `schema.py` | El contrato de datos del CSV: columnas, valores permitidos y reglas de invalidez |
| `validation.py` | `validate_record(fila)` → lista de reglas que rompe. Función pura |
| `analysis.py` | `iter_rows` lee el CSV y comprueba el fichero entero. `analyze_csv` / `analyze_file` → `AnalysisResult`. Una sola pasada, en streaming |
| `export.py` | CSV de resultados, una métrica por fila (`section`, `metric`, `value`) |
| `report.py` | Informe de consola con el formato de la salida esperada del briefing |
| `catalog.py` | Vocabulario del gestor: `IncidentStatus`, `IncidentCategory`, `IncidentOrigin`, `Branch` (con sus nombres para mostrar), `can_transition` |
| `seeding.py` | `transform_record(fila)` → `IncidentDraft` o los motivos del rechazo. `plan_seed` / `plan_seed_file` → `SeedPlan`. No toca la base de datos |

## Decisiones

- **Solo librería estándar** (`csv`, no pandas). El fichero se lee fila a fila, así que la memoria no crece con el tamaño: el millón de líneas de producción cabe igual que las 100 de prueba. Sin dependencias, porque lo importan scripts y un servicio a la vez.
- **El email entra pero no sale.** Se usa solo para comprobar que tiene `@`. `AnalysisResult` y `SeedPlan` guardan números, códigos de regla y el `ticket_id`, nunca otros valores de la fila. El `ticket_id` solo se muestra si tiene el formato `NXV-XXXXXX`. Hay pruebas que lo comprueban.
- **Una fila puede romper varias reglas.** "Registros inválidos" cuenta filas y el desglose cuenta reglas, así que no tienen por qué sumar lo mismo.
- **Tres reglas más que la tabla del briefing**: `ticket_id`, `date` y `status`. La tabla de estructura los marca como obligatorios y el enunciado exige invalidar un registro al que le falte un campo obligatorio o que traiga un estado no permitido. Con el fichero de prueba valen 0.
- **Errores de fichero completo** (`EmptyFileError`, `MissingColumnsError`, `FileEncodingError`, todos subclases de `IncidentFileError`). Una fila mal formada no rompe el análisis: se cuenta como inválida.
- **Se acepta UTF-8 con o sin BOM**, y espacios en la cabecera: es lo que produce Excel.
- **Limitación conocida:** los `ticket_id` duplicados no se detectan. El briefing no los incluye entre las reglas de invalidez y el fichero de prueba no tiene ninguno.

### Del gestor de incidencias

- **El seed pasa primero la validación del analizador.** Así carga exactamente los 96 registros válidos del proyecto anterior. Después aplica los mapeos; lo que no se puede mapear se rechaza con su propio código (`unmapped_status`, `unmapped_category`, `empty_title`). Con el CSV actual ninguno salta.
- **Los valores son `StrEnum`.** Cada miembro es también un `str`: se guarda en TinyDB y viaja en JSON como texto, y Pydantic lo usa tal cual para rechazar cualquier otro valor.
- **`ticket_id` no es un campo del modelo.** El briefing dice que no se almacena en la incidencia; `IncidentDraft.source_id` lo lleva solo hasta el seed, que lo apunta aparte para no insertar dos veces. Título + fecha no sirve como clave: en el CSV hay filas distintas con la misma descripción y el mismo día. Hay una prueba que lo demuestra.
- **El título tiene como mucho 120 caracteres** (`TITLE_MAX_LENGTH`), el límite que el briefing fija para el seed. El formulario usará el mismo.
- **Los nombres para mostrar de estados y categorías no están aquí.** El briefing solo da los de las sedes (`BRANCH_LABELS`).

## Comandos

Desde esta carpeta:

```powershell
python -m unittest discover -s tests -t tests   # 76 pruebas
```

No hace falta instalarlo a mano en la API: `uv sync` desde [`services/api/`](../../../services/api/) lo instala en modo editable.

Dos pruebas de aceptación contra [`scripts/incidents-nexova.csv`](../../../scripts/incidents-nexova.csv), con los valores esperados de cada briefing: [`test_briefing.py`](./tests/test_briefing.py) (analizador) y [`test_seeding.py`](./tests/test_seeding.py) (seed del gestor: 96 válidos, 27/56/13 por estado, 49/35/12 por categoría). Si fallan, no se entrega.
