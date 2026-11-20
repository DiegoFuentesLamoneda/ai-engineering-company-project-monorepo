# `packages/shared/` — código que comparten varias aplicaciones

| Paquete | Lenguaje | Qué es | Quién lo usa |
| --- | --- | --- | --- |
| [`incident-analysis/`](./incident-analysis/) | Python | Validación y métricas del CSV de tickets, y vocabulario del gestor de incidencias (estados, categorías, orígenes, sedes, transiciones y mapeo del seed) | [`scripts/analyze.py`](../../scripts/analyze.py), [`scripts/seed_incidents.py`](../../scripts/), [`services/api/`](../../services/api/) |
| [`package.json`](./package.json) · [`types/`](./types/) | TypeScript | `@repo/shared-types`, de la plantilla del monorepo. Hoy solo tiene un ejemplo: ninguna aplicación lo importa | — |

Cada paquete lleva su README con sus comandos.
