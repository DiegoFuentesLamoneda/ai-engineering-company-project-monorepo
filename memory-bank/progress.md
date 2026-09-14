# Estado del desarrollo

> Qué está entregado, qué está en curso y qué viene después.
> **Se actualiza en el mismo commit que cierra un trabajo.** Es el paso 3 del flujo de [`AGENTS.md`](../AGENTS.md).

_Última actualización: 14 de septiembre de 2026 (hito 4 en curso)._

## Entregado

| Hito | Entregable | Dónde | Rama | PR |
| --- | --- | --- | --- | --- |
| 1 — Sitio Web Público | Landing corporativa + formulario de registro de talento. Lighthouse 100/100/100/100. Desplegado en GitHub Pages | [`uis/website/`](../uis/website/) | `hito-01-web-publica` | #1 · fusionada el 14/08/2026 |
| 2 — Fundamentos de Programación | `@repo/talent-core`: filtros, búsquedas lineal y binaria, scoring, ranking, reportes y validaciones. 112 pruebas en verde. Banco de pruebas web | [`packages/talent-core/`](../packages/talent-core/) · [`uis/talent-lab/`](../uis/talent-lab/) | `feature/domain-models` | #2 · abierta desde el 21/08/2026 |
| 3 — Talent Pipeline Tracker | Listado, filtros y búsqueda sin recarga, detalle, cambio de estado y etapa, notas internas, alta y edición de candidaturas | [`uis/talent-pipeline-tracker/`](../uis/talent-pipeline-tracker/) | `feature/talent-pipeline-tracker` | #3 · abierta desde el 03/09/2026 |

> Las PRs #2 y #3 siguen abiertas para la evaluación del campus. Por eso las ramas se apilan: cada hito nuevo sale de la rama del anterior, no de `main`. `main` solo tiene el hito 1.

## En curso — hito 4: Ingeniería impulsada por IA

Rama `feature/agent-memory-bank`. Infraestructura para que cualquier agente de código trabaje en este repositorio sin romper lo construido, más la reorganización de la capa de aplicación según la plantilla del monorepo.

| Paso | Estado |
| --- | --- |
| Banco de memoria (`memory-bank/`) con contexto de negocio y técnico | ✅ |
| `AGENTS.md` en la raíz: qué leer, flujo antes de cada commit, qué no se toca | ⬜ |
| Reglas de desarrollo en `.agents/rules/` con su ámbito de aplicación | ⬜ |
| Skills en `.agents/skills/` con inputs y criterios verificables | ⬜ |
| Mover el tracker a `uis/backoffice/` y el listado a la ruta `/candidates` | ⬜ |
| Panel de entrada del backoffice en `/` con layout propio y datos de Nexova | ⬜ |
| Actualizar `CONTEXT.md` y la documentación al hito 4 | ⬜ |

### Decisiones de este hito

- **El tracker se mueve, no se duplica.** La plantilla del monorepo reserva `uis/backoffice/` para las aplicaciones internas. Se mueve con `git mv` para conservar el historial, en un commit separado del que añade contenido nuevo: así el diff del movimiento es legible.
- **`uis/talent-lab/` se queda donde está.** Es un proyecto con interfaz y `uis/` es su sitio según el README de la plantilla. Moverlo no aportaría nada y rompería sus rutas relativas.
- **`uis/website/` no se toca.** Ya cumple lo que pide el hito y migrarla a un framework pondría en riesgo el 100 de Lighthouse y el despliegue a Pages.
- **`.agents/` no es `/agents`.** `.agents/` configura las herramientas de desarrollo (reglas y skills del agente de código). `/agents` es producto: los agentes de IA que Nexova usará, y llega en hitos posteriores.

## Próximo

**Hito 5 — Backend.** Primer servicio propio en [`services/`](../services/), en FastAPI y como aplicación única con routers por dominio, no como microservicios. Es el hito en el que `services/` deja de estar vacío y donde `talent-core` deja de consumirse solo desde interfaces.

Después: telemetría (6), pipelines de datos (6b), RAG sobre la base de candidatos (7), memoria y harness de agentes (8), workflows agénticos (9) y tiempo real (10).

## Deuda técnica y decisiones aplazadas

| Asunto | Estado |
| --- | --- |
| **npm workspaces** | Aplazado. Cada proyecto se instala por separado. Se reevalúa cuando dos aplicaciones consuman el mismo paquete a la vez. |
| **`packages/shared/`** | Viene de la plantilla y está prácticamente vacío. Decidir si se usa o se retira cuando haya tipos que compartir de verdad. |
| **Sin CI para el tracker** | `typecheck`, `lint` y `build` se ejecutan solo en local. Falta el workflow equivalente al de `talent-core`. |
| **Ambigüedad en `CONTEXT.md`** | El responsable de Ventas aparece con dos nombres distintos. Sin resolver — ver [`projectbrief.md`](./projectbrief.md). |
| **Dependencia de una API mock compartida** | Los datos los escriben también otros alumnos. Ninguna funcionalidad puede asumir que un registro concreto sigue existiendo. |
