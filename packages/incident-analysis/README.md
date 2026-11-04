# `incident-analysis` — análisis de ficheros de tickets de soporte

Valida el CSV que exporta el helpdesk del servicio de soporte externalizado y calcula sus métricas. Es **la única implementación** de esa lógica en el monorepo: la usan el script [`scripts/analyze.py`](../../scripts/analyze.py) y la API [`services/api/`](../../services/api/). Si una regla cambia, cambia aquí y los dos consumidores se enteran a la vez.

La especificación es el briefing [`incidents-file-analysis.es.md`](../../docs/contexts/proyectos/incidents-file-analysis.es.md). Campos, categorías, estados, reglas y valores esperados se copian de ahí **literalmente**, en [`schema.py`](./incident_analysis/schema.py).

## Por qué existe

El fichero contiene emails de clientes finales. No puede enviarse a ninguna herramienta de IA externa, así que el análisis tiene que hacerse en casa y con código determinista.

## Módulos

| Archivo | Qué hace |
| --- | --- |
| `schema.py` | El contrato de datos: columnas, valores permitidos y reglas de invalidez |
| `validation.py` | `validate_record(fila)` → lista de reglas que rompe. Función pura |
| `analysis.py` | `analyze_csv` / `analyze_file` → `AnalysisResult`. Una sola pasada, en streaming |
| `export.py` | CSV de resultados, una métrica por fila (`section`, `metric`, `value`) |
| `report.py` | Informe de consola con el formato de la salida esperada del briefing |

## Decisiones

- **Solo librería estándar** (`csv`, no pandas). El fichero se lee fila a fila, así que la memoria no crece con el tamaño: el millón de líneas de producción cabe igual que las 100 de prueba. Sin dependencias, porque lo importan un script y un servicio a la vez.
- **El email entra pero no sale.** Se usa solo para comprobar que tiene `@`. `AnalysisResult` guarda números y códigos de regla, nunca valores de la fila. La muestra de filas inválidas da el número de línea y el `ticket_id`, este solo si tiene el formato `NXV-XXXXXX`. Hay una prueba que lo comprueba.
- **Una fila puede romper varias reglas.** "Registros inválidos" cuenta filas y el desglose cuenta reglas, así que no tienen por qué sumar lo mismo.
- **Tres reglas más que la tabla del briefing**: `ticket_id`, `date` y `status`. La tabla de estructura los marca como obligatorios y el enunciado exige invalidar un registro al que le falte un campo obligatorio o que traiga un estado no permitido. Con el fichero de prueba valen 0.
- **Errores de fichero completo** (`EmptyFileError`, `MissingColumnsError`, `FileEncodingError`, todos subclases de `IncidentFileError`). Una fila mal formada no rompe el análisis: se cuenta como inválida.
- **Se acepta UTF-8 con o sin BOM**, y espacios en la cabecera: es lo que produce Excel.
- **Limitación conocida:** los `ticket_id` duplicados no se detectan. El briefing no los incluye entre las reglas de invalidez y el fichero de prueba no tiene ninguno.

## Comandos

Desde esta carpeta:

```powershell
python -m unittest discover -s tests -t tests   # 44 pruebas
pip install -e .                                # instalarlo en el entorno de la API
```

La prueba [`test_briefing.py`](./tests/test_briefing.py) comprueba los valores esperados del briefing contra [`scripts/incidents-nexova.csv`](../../scripts/incidents-nexova.csv). Si falla, el análisis no se entrega.
