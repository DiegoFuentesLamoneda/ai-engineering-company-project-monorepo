# Carpeta `scripts`

Esta carpeta contiene **scripts auxiliares** del monorepo: automatizaciones de desarrollo, utilidades de mantenimiento, tareas repetitivas (setup, lint, migraciones, generación de datos, etc.) y tooling interno.

- **Propósito principal**: agrupar herramientas de soporte que no pertenecen a una app/agente/pipeline específico, pero facilitan el trabajo del equipo.
- **Recomendación**: documenta cada script (qué hace, parámetros, requisitos, ejemplos de uso) y procura que sean reproducibles (y seguros) en distintos entornos.

## Scripts

| Script | Qué hace |
| --- | --- |
| [`analyze.py`](./analyze.py) | Analiza la exportación CSV del helpdesk de soporte: valida cada ticket, imprime las métricas en consola y, si se confirma, escribe `results.csv` (una métrica por fila) en la carpeta desde la que se ejecuta |
| [`seed_incidents.py`](./seed_incidents.py) | Carga en el gestor de incidencias el histórico de ese mismo CSV (`origin: customer`, `branch: central`). Lista en consola las filas rechazadas y se puede repetir sin duplicar |
| [`sync_contexts.py`](./sync_contexts.py) | Sincroniza `docs/contexts/` desde el syllabus del curso |

### `analyze.py`

```bash
python scripts/analyze.py scripts/incidents-nexova.csv
```

- **Argumento obligatorio:** la ruta del CSV. Sin él, el script muestra su uso y termina.
- **Requisitos:** Python 3.11 o superior. No necesita dependencias: la lógica vive en
  [`packages/shared/incident-analysis`](../packages/shared/incident-analysis/), la misma que usa la API.
- [`incidents-nexova.csv`](./incidents-nexova.csv) es el fichero de prueba del briefing:
  100 registros, 96 válidos y 4 inválidos.
- `results.csv` está en `.gitignore`: es un resultado, no se versiona.
- El email de los clientes no aparece en ninguna salida, ni siquiera en los errores.

### `seed_incidents.py`

Desde la raíz del repositorio:

```bash
uv run --project services/api python scripts/seed_incidents.py
```

- **Argumento opcional:** la ruta del CSV. Por defecto, [`incidents-nexova.csv`](./incidents-nexova.csv).
- **Requisitos:** el entorno de la API (`uv sync` en [`services/api`](../services/api/)). `--project services/api`
  lo usa sin activarlo: hace falta porque el seed guarda con TinyDB y el modelo `Incident` de la API.
- **Dónde escribe:** en el mismo fichero que lee la API, `services/api/storage/incidents.json`, o en
  `NEXOVA_API_INCIDENTS_DB_PATH` si está definida.
- **Qué carga:** las transformaciones del briefing son las del paquete compartido
  (`incident_analysis.plan_seed_file`), con la misma validación que `analyze.py`. Del CSV del briefing entran
  96 incidencias: 27 `open`, 56 `resolved` y 13 `discarded`.
- **Idempotente:** cada `ticket_id` cargado se apunta en la tabla `seed_imports`. La segunda ejecución inserta 0.
  El `ticket_id` no se guarda en la incidencia.
- **Filas rechazadas:** se listan todas, con su línea y su `ticket_id`, nunca con el email.

