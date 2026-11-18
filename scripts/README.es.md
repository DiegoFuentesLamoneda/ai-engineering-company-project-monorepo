# Carpeta `scripts`

Esta carpeta contiene **scripts auxiliares** del monorepo: automatizaciones de desarrollo, utilidades de mantenimiento, tareas repetitivas (setup, lint, migraciones, generación de datos, etc.) y tooling interno.

- **Propósito principal**: agrupar herramientas de soporte que no pertenecen a una app/agente/pipeline específico, pero facilitan el trabajo del equipo.
- **Recomendación**: documenta cada script (qué hace, parámetros, requisitos, ejemplos de uso) y procura que sean reproducibles (y seguros) en distintos entornos.

## Scripts

| Script | Qué hace |
| --- | --- |
| [`analyze.py`](./analyze.py) | Analiza la exportación CSV del helpdesk de soporte: valida cada ticket, imprime las métricas en consola y, si se confirma, escribe `results.csv` (una métrica por fila) en la carpeta desde la que se ejecuta |
| [`sync_contexts.py`](./sync_contexts.py) | Sincroniza `docs/contexts/` desde el syllabus del curso |

### `analyze.py`

```bash
python scripts/analyze.py scripts/incidents-nexova.csv
```

- **Argumento obligatorio:** la ruta del CSV. Sin él, el script muestra su uso y termina.
- **Requisitos:** Python 3.11 o superior. No necesita dependencias: la lógica vive en
  [`packages/incident-analysis`](../packages/incident-analysis/), la misma que usa la API.
- [`incidents-nexova.csv`](./incidents-nexova.csv) es el fichero de prueba del briefing:
  100 registros, 96 válidos y 4 inválidos.
- `results.csv` está en `.gitignore`: es un resultado, no se versiona.
- El email de los clientes no aparece en ninguna salida, ni siquiera en los errores.

