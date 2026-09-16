# Estado del desarrollo

> Qué está entregado, qué está en curso y qué viene después.
> **Se actualiza en el mismo commit que cierra un trabajo.** Es el paso 3 del flujo de [`AGENTS.md`](../AGENTS.md).

_Última actualización: 16 de septiembre de 2026 (hito 5 en curso)._

## Entregado

| Hito | Entregable | Dónde | Rama | PR |
| --- | --- | --- | --- | --- |
| 1 — Sitio Web Público | Landing corporativa + formulario de registro de talento. Lighthouse 100/100/100/100. Desplegado en GitHub Pages | [`uis/website/`](../uis/website/) | `hito-01-web-publica` | #1 · fusionada el 14/08/2026 |
| 2 — Fundamentos de Programación | `@repo/talent-core`: filtros, búsquedas lineal y binaria, scoring, ranking, reportes y validaciones. 112 pruebas en verde. Banco de pruebas web | [`packages/talent-core/`](../packages/talent-core/) · [`uis/talent-lab/`](../uis/talent-lab/) | `feature/domain-models` | #2 · fusionada el 16/09/2026 |
| 3 — Talent Pipeline Tracker | Listado, filtros y búsqueda sin recarga, detalle, cambio de estado y etapa, notas internas, alta y edición de candidaturas | [`uis/backoffice/`](../uis/backoffice/) | `feature/talent-pipeline-tracker` | #3 · fusionada el 16/09/2026 |
| 4 — Ingeniería impulsada por IA | Banco de memoria, `AGENTS.md`, reglas y skills en `.agents/`, traslado del tracker a `uis/backoffice/` con panel de entrada propio, CI del backoffice | [`memory-bank/`](../memory-bank/) · [`.agents/`](../.agents/) · [`uis/backoffice/`](../uis/backoffice/) | `feature/agent-memory-bank` | #4 · fusionada el 16/09/2026 |

### Cambio en el modelo de ramas — 16/09/2026

Hasta ahora las ramas **se apilaban**: cada hito salía de la rama del anterior, porque las PRs se dejaban abiertas para la evaluación del campus y `main` solo contenía el hito 1.

Aprobadas ya las cuatro entregas, las PRs #2, #3 y #4 se fusionaron en orden con *merge commit* —no *squash*, que habría reescrito los identificadores de commit y dejado las PRs apiladas con conflictos falsos—. **`main` contiene ahora los cuatro hitos**, y a partir del hito 5 cada rama sale de `main`. Las ramas de hito no se borran: los enlaces de la evaluación siguen apuntando a ellas.

### Decisiones del hito 4

- **El tracker se movió, no se duplicó.** La plantilla del monorepo reserva `uis/backoffice/` para las aplicaciones internas. Se movió con `git mv` para conservar el historial, en un commit separado del que añadía contenido nuevo.
- **`uis/talent-lab/` se queda donde está.** Es un proyecto con interfaz y `uis/` es su sitio según el README de la plantilla.
- **`uis/website/` no se toca.** Ya cumple lo que pide el hito y migrarla a un framework pondría en riesgo el 100 de Lighthouse y el despliegue a Pages.
- **`.agents/` no es `/agents`.** `.agents/` configura las herramientas de desarrollo. `/agents` es producto, y llega en hitos posteriores.

## En curso — hito 5: Backend

Rama `feature/backend-architecture-proposal`, salida de `main`. El hito tiene **dos proyectos encadenados**:

### 5a — Propuesta de arquitectura (en curso)

Documento técnico, no código: [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md). Razonamiento sobre cómo estructurar el backend antes de escribirlo.

| Paso | Estado |
| --- | --- |
| Investigación de convenciones estándar de FastAPI, con fuentes citadas | ✅ |
| Redacción de la propuesta: patrón, estructura, routers, CORS y entorno, decisiones y riesgos | ✅ |
| Actualizar el apéndice de `CONTEXT.md` y `CONTEXT.es.md` al hito 5 | ✅ |
| Actualizar el banco de memoria | ✅ |
| PR hacia `main` | ⏳ |

**Decisiones propuestas en el documento** (pasan a [`techContext.md`](./techContext.md) cuando se implementen):

- **Monolito modular por dominios** sobre FastAPI, no microservicios ni serverless. Justificado por el tamaño del equipo de Tecnología (6 personas), la ausencia de telemetría hasta el hito 6, el acoplamiento natural entre dominios y un volumen de cientos de usuarios.
- **Un servicio, `services/nexova-api/`**, con paquetes por dominio (`app/domains/<dominio>/`) y tres capas: `router` → `service` → `models`.
- **Estructura por dominio, no por tipo de archivo**, siguiendo la convención de `fastapi-best-practices` (inspirada en Netflix Dispatch) sobre la base del tutorial oficial *Bigger Applications*.
- **El motor de scoring se porta a Python.** Ver la deuda técnica más abajo.
- **CORS con lista explícita de orígenes** —`localhost` y `127.0.0.1` incluidos desde el primer commit— y ninguna credencial en variables `NEXT_PUBLIC_`.

### 5b — API de inventario (siguiente)

Implementación del ticket **NXV-0201**: `Asset`, `AssetEntry`, `AssetExit`, stock calculado como entradas menos salidas y todas las rutas bajo `/inventory`. Especificación literal en [`docs/contexts/05-backend-development.es.md`](../docs/contexts/05-backend-development.es.md). Es el hito en el que [`services/`](../services/) deja de estar vacío.

## Próximo

Telemetría (6), pipelines de datos (6b), RAG sobre la base de candidatos (7), memoria y harness de agentes (8), workflows agénticos (9) y tiempo real (10).

## Deuda técnica y decisiones aplazadas

| Asunto | Estado |
| --- | --- |
| **Port del scoring a Python** | Abierto desde el hito 5. `talent-core` es TypeScript y FastAPI no puede importarlo. Se reimplementará dentro del dominio `recruitment` usando sus 112 pruebas como especificación. Hasta que el port esté completo, la lógica vive en dos lenguajes: riesgo de divergencia documentado en [`ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) §8 |
| **Versionado de la API** | Aplazado. Se despliega sin prefijo de versión porque el ticket NXV-0201 exige las rutas literalmente bajo `/inventory`. Se introduce `/api/v1` cuando exista el primer consumidor externo |
| **Migraciones con Alembic** | Aplazado. Se adoptan cuando haya datos que no se puedan perder |
| **npm workspaces** | Aplazado. Cada proyecto se instala por separado. Se reevalúa cuando dos aplicaciones consuman el mismo paquete a la vez |
| **`packages/shared/`** | Viene de la plantilla y está prácticamente vacío. Decidir si se usa o se retira cuando haya tipos que compartir de verdad |
| **Ambigüedad en `CONTEXT.md`** | El responsable de Ventas aparece con dos nombres distintos. Sin resolver — ver [`projectbrief.md`](./projectbrief.md). Bloqueará el dominio de ventas cuando llegue |
| **Dependencia de una API mock compartida** | Los datos los escriben también otros alumnos. Ninguna funcionalidad puede asumir que un registro concreto sigue existiendo. El backend propio **no la envuelve**: convivirán |
