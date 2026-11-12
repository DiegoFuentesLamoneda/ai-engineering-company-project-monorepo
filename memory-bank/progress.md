# Estado del desarrollo

> Qué está entregado, qué está en curso y qué viene después.
> **Se actualiza en el mismo commit que cierra un trabajo.** Es el paso 3 del flujo de [`AGENTS.md`](../AGENTS.md).

_Última actualización: 11 de noviembre de 2026 (directorio de proveedores, cierre)._

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
- **Un servicio, `services/nexova-api/`** —ubicado finalmente en `services/api/`, ver [`techContext.md`](./techContext.md)—, con paquetes por dominio (`app/domains/<dominio>/`) y tres capas: `router` → `service` → `models`.
- **Estructura por dominio, no por tipo de archivo**, siguiendo la convención de `fastapi-best-practices` (inspirada en Netflix Dispatch) sobre la base del tutorial oficial *Bigger Applications*.
- **El motor de scoring se porta a Python.** Ver la deuda técnica más abajo.
- **CORS con lista explícita de orígenes** —`localhost` y `127.0.0.1` incluidos desde el primer commit— y ninguna credencial en variables `NEXT_PUBLIC_`.

### 5b — API de inventario (siguiente)

Implementación del ticket **NXV-0201**: `Asset`, `AssetEntry`, `AssetExit`, stock calculado como entradas menos salidas y todas las rutas bajo `/inventory`. Especificación literal en [`docs/contexts/05-backend-development.es.md`](../docs/contexts/05-backend-development.es.md). Es el hito en el que [`services/`](../services/) deja de estar vacío.

**Estado a 04/11/2026:** la PR #5 (propuesta de arquitectura) está fusionada en `main`. La API de inventario **no está empezada**: se pospone para hacer antes el analizador de incidencias, y entrará como otro dominio del mismo servicio `services/api/`.

## En curso — Analizador de incidencias

Rama `feature/incidents-analyzer`, salida de `main`. Especificación: [`docs/contexts/proyectos/incidents-file-analysis.es.md`](../docs/contexts/proyectos/incidents-file-analysis.es.md). Script de análisis del CSV de tickets de soporte de Roberto Díaz, y después la misma lógica en la API y en el backoffice.

| Paso | Estado |
| --- | --- |
| Lógica compartida en [`packages/incident-analysis/`](../packages/incident-analysis/): validación, métricas, exportación e informe. 44 pruebas, incluida la de aceptación contra el briefing | ✅ |
| Script [`scripts/analyze.py`](../scripts/analyze.py): 100 / 96 / 4 y todos los desgloses coinciden con el briefing | ✅ |
| API en [`services/api/`](../services/api/): `POST /api/incidents/analyze` y `GET /api/incidents/results/export`. 18 pruebas del service y la configuración; rutas, errores y CORS verificados con el servidor arrancado; la exportación es idéntica byte a byte a la del script | ✅ |
| Página [`/incidents`](../uis/backoffice/app/incidents/) en el backoffice: subida por arrastre o selector, totales, desglose por categoría y estado, índice de satisfacción, registros inválidos por regla con sus filas y descarga del CSV. Verificada en el navegador con la API arrancada: cifras del briefing, CSV descargado idéntico byte a byte al del script, y errores 400 y 415 mostrados con el mensaje de la API | ✅ |
| Capturas (consola e interfaz) y PR hacia `main`: [#6](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/6), abierta el 04/11/2026 para la evaluación del campus | ✅ |

## En curso — Directorio de proveedores

Rama `feature/supplier-directory`, **apilada sobre `feature/incidents-analyzer`**, porque `services/api/` todavía no está en `main` (PR #6 abierta). Especificación: [`docs/contexts/proyectos/supplier-directory.es.md`](../docs/contexts/proyectos/supplier-directory.es.md). API de proveedores sobre FastAPI + TinyDB + Pydantic, con seeder y página en el backoffice. Lo pide Patricia Solís (HR Manager) para sustituir su hoja de cálculo.

| Fase | Estado |
| --- | --- |
| 1 — Montaje: `services/api` pasa a `pyproject.toml` + uv, TinyDB 4.9.0 añadido, `requirements.txt` retirado. 18 pruebas en verde y la API arranca con `uv run` | ✅ |
| 2 — Modelo de datos: [`schemas.py`](../services/api/app/domains/suppliers/schemas.py) con enums de país, moneda, categoría y estado, tarifa > 0 (y finita), moneda según el país, entrada y salida separadas, `extra="forbid"` en la entrada. 19 pruebas | ✅ |
| 3 — Base de datos y seeder: [`database.py`](../services/api/app/domains/suppliers/database.py) (TinyDB en `services/api/storage/suppliers.json`, ignorado por git, con filtros por país y categoría) y [`seed.py`](../services/api/app/seed.py) (`uv run seed`: 15 insertados la primera vez, 0 la segunda). 55 pruebas en total | ✅ |
| 4 — Endpoints `/suppliers`: [`router.py`](../services/api/app/domains/suppliers/router.py) y [`service.py`](../services/api/app/domains/suppliers/service.py). Alta `201`, listado con filtros, detalle, tarifa (renueva `updated_at`), estado y baja; `404`/`422` y `409` al borrar un suspendido (decisión de Diego, 11/11/2026). Probado a mano con curl y tras reiniciar. 70 pruebas | ✅ |
| 5 — Página [`/suppliers`](../uis/backoffice/app/suppliers/page.tsx) en el backoffice, en el menú: tabla, filtros por país y categoría en la URL, tarifa y estado editables por fila, suspendidos atenuados, aviso de renovación a 60 días y alta en `/suppliers/new` con validación y errores de la API en español. Etiquetas aprobadas por Diego (11/11/2026). Typecheck, lint y build en verde, y 20 comprobaciones en el navegador | ✅ |
| 6 — Cierre: capturas del seeder, de Swagger con un filtro y de la interfaz con un filtro; banco de memoria ([`techContext.md`](./techContext.md): TinyDB detrás de un repositorio y el `409`) y PR hacia `main`: [#7](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/7), abierta el 11/11/2026 para la evaluación del campus | ✅ |

**Estructura:** dominio `app/domains/suppliers/`, no los archivos sueltos que propone el enunciado (`models.py`, `routes/suppliers.py`…). Lo decidió la propuesta de arquitectura del hito 5. La PR lleva una tabla con la equivalencia entre los dos.

**La PR de proveedores incluye los commits de la #6**, porque la rama está apilada. Cuando se fusione la #6, su diff se queda solo con lo de proveedores.

## En curso — Autenticación de la API

Rama `feature/auth-api`, **apilada sobre `feature/supplier-directory`** (PR #7 abierta). Proyecto «Asegurando la API: Autenticación y Restricción de Rutas en FastAPI», ticket **AUTH-01**: usuarios (solo credenciales) y perfiles en TinyDB, login con JWT y `get_current_user` en toda ruta que no sea pública. El enunciado no está en `docs/contexts/`: lo pegó Diego el 12/11/2026.

**Decisiones de Diego (12/11/2026):** las dependencias del enunciado (`python-jose`, `libpass`); se protegen las 8 rutas de `incidents` y `suppliers`; `GET /users` solo para `admin`; el primer admin se crea con un comando, `uv run create-admin`.

| Fase | Estado |
| --- | --- |
| 1 — Preparación: `python-jose[cryptography]==3.5.0` y `libpass[bcrypt]==1.9.4`; secreto, caducidad y fichero de usuarios en [`config.py`](../services/api/app/config.py); [`.env.example`](../services/api/.env.example); sin secreto la API no arranca (el seeder sí). 75 pruebas | ✅ |
| 2 — Modelos `User` y `Profile` y su repositorio en TinyDB: [`users/`](../services/api/app/domains/users/) y [`profiles/`](../services/api/app/domains/profiles/), dos ficheros de TinyDB. `id` UUID (TinyDB reutiliza sus números), email único en minúsculas, contraseña de 8 caracteres a 72 bytes, `role` fuera del alta, `UserPublic` sin hash. 33 pruebas | ✅ |
| 3 — Service de usuarios: hash de contraseñas, CRUD y `uv run create-admin` | ⬜ |
| 4 — Token: `POST /auth/login`, `get_current_user` y `GET /auth/me` | ⬜ |
| 5 — Rutas `/users` y `/profiles` con `401` y `403` | ⬜ |
| 6 — Proteger las rutas existentes | ⬜ |
| 7 — Verificación: pruebas y recorrido en `/docs` | ⬜ |
| 8 — Cierre: banco de memoria, PR y ficha de la biblioteca | ⬜ |

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
| **Regla de ramas desfasada** | [`AGENTS.md`](../AGENTS.md) §9 y [`.agents/rules/commits-y-entrega.md`](../.agents/rules/commits-y-entrega.md) siguen diciendo que cada rama sale de la del hito anterior. Desde el 16/09/2026 salen de `main` (ver arriba). Corregir al cerrar el analizador de incidencias |
| **API de inventario (NXV-0201) pendiente** | Pospuesta el 04/11/2026 para hacer antes el analizador de incidencias. A 11/11/2026 **su enunciado todavía no está publicado** en la web del curso, que marca el orden de los proyectos: probablemente se ha movido más adelante. Su contexto está en `docs/contexts/` porque `sync_contexts.py` descarga todos. Se hará cuando salga |
| **"El último análisis" en memoria** | `GET /api/incidents/results/export` exporta el último análisis del proceso: se pierde al reiniciar, es común a todos los usuarios y no funciona con varios workers. Solución prevista: un `analysis_id` en la respuesta del `POST`. Cambia el contrato del enunciado, así que se aplaza hasta que haya más de un usuario |
| **Pruebas automáticas de las rutas HTTP** | Necesitan el cliente de pruebas de FastAPI, que depende de `httpx`, y `httpx` no está aprobado como dependencia. Hoy se prueban el service y la configuración, y las rutas se verifican a mano |
| **Dependencia de una API mock compartida** | Los datos los escriben también otros alumnos. Ninguna funcionalidad puede asumir que un registro concreto sigue existiendo. El backend propio **no la envuelve**: convivirán |
