# Contexto técnico — monorepo de Nexova

> Qué hay construido, con qué está hecho, qué decisiones ya están tomadas y qué límites no se cruzan.
> Se actualiza **en el mismo commit** que el cambio que lo afecta. Un banco de memoria desfasado es peor que no tenerlo.

## Qué hay hoy en el repositorio

| Ruta | Qué es | Stack | Hito |
| --- | --- | --- | --- |
| [`uis/website/`](../uis/website/) | Web pública de Nexova: landing + formulario de registro de talento | HTML5, Tailwind 4 (CLI), JS sin dependencias | 1 |
| [`packages/talent-core/`](../packages/talent-core/) | Motor de scoring de candidatos y matching de vacantes | TypeScript 5, `node:test`, `tsx` | 2 |
| [`uis/talent-lab/`](../uis/talent-lab/) | Banco de pruebas manual de `talent-core`: dispara sus 18 funciones desde botones | HTML + Tailwind 4 + el `dist/` de `talent-core` | 2 |
| [`uis/backoffice/`](../uis/backoffice/) | Aplicación interna: panel de operaciones, seguimiento de candidaturas, análisis de incidencias de soporte y directorio de proveedores | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind 4 | 3 · 4 · Analizador de incidencias · Directorio de proveedores |
| [`packages/shared/`](../packages/shared/) | `@repo/shared-types` — viene de la plantilla, prácticamente vacío | TypeScript | — |
| [`packages/incident-analysis/`](../packages/incident-analysis/) | Validación y métricas de los CSV de tickets de soporte. Lógica única que comparten el script y la API | Python 3.11+, solo stdlib, `unittest` | Analizador de incidencias |
| [`scripts/analyze.py`](../scripts/analyze.py) | Analizador de tickets por consola, con exportación a `results.csv` | Python 3, usa `incident-analysis` | Analizador de incidencias |
| [`scripts/sync_contexts.py`](../scripts/sync_contexts.py) | Descarga los contextos del syllabus y los coloca en `docs/contexts/` | Python 3, solo stdlib | — |
| [`services/api/`](../services/api/) | Backend de Nexova. Dos dominios: `incidents` (análisis del CSV subido y exportación del último análisis) y `suppliers` (directorio de proveedores con su seeder, `uv run seed`) | Python 3.11+, FastAPI, Pydantic 2, uvicorn, TinyDB, uv | Analizador de incidencias · Directorio de proveedores |

Las carpetas `data/`, `agents/`, `mcps/`, `workflows/`, `infra/` e `internal/` existen con su README pero **están vacías a propósito**. Se llenarán en los hitos que las necesiten. No se crean subcarpetas "por si acaso".

## Versiones fijadas

| Pieza | Versión | Dónde |
| --- | --- | --- |
| Next.js | 16.3.4 | tracker |
| React / React DOM | 19.2.8 | tracker |
| TypeScript | 5.x | tracker, `talent-core`, `talent-lab` |
| Tailwind CSS | 4.x | website, `talent-lab`, tracker |
| Node en CI | 20 (website) · 22 (`talent-core`) | workflows de GitHub Actions |
| FastAPI | 0.162.0 | `services/api` |
| uvicorn | 0.54.0 | `services/api` |
| python-multipart | 0.0.33 | `services/api` |
| TinyDB | 4.9.0 | `services/api` |
| python-jose[cryptography] | 3.5.0 | `services/api` (firma de los JWT) |
| libpass[bcrypt] | 1.9.4 | `services/api` (hash de contraseñas) |
| uv | 0.13 o superior | gestor del entorno de `services/api` |

## API de datos

| Dato | Valor |
| --- | --- |
| Base URL | `https://playground.4geeks.com/tracker/api/v1` |
| Variable | `NEXT_PUBLIC_API_URL` en `.env.local` |
| Naturaleza | Mock centralizada del curso, **compartida por todos los alumnos** |

Consecuencias prácticas: los datos que devuelve **pueden cambiar o desaparecer** sin aviso, porque otros la escriben. Ninguna funcionalidad debe asumir que un registro concreto sigue ahí. Y no hay autenticación: no se le manda nada sensible.

El prefijo `NEXT_PUBLIC_` incrusta la variable en el bundle del navegador — **es pública**. Nunca debe usarse para credenciales.

El backoffice habla además con la API propia, `services/api/`, para el análisis de incidencias y el directorio de proveedores: variable **`NEXT_PUBLIC_NEXOVA_API_URL`** (`http://localhost:8000` en local). Las dos APIs pasan por el mismo `request()` de `lib/api.ts`, cada una con su URL base.

## Decisiones de arquitectura tomadas

Cada una con su porqué, para no volver a discutirlas ni revertirlas por descuido.

### Tailwind compilado con el CLI, nunca por CDN

El Play CDN descarga ~120 KB de compilador y genera el CSS **en el navegador** durante la carga: dispara el Total Blocking Time y provoca un parpadeo sin estilos. Con el CLI el resultado son 19 KB de CSS y cero JavaScript de Tailwind. La web pública puntúa 100 en las cuatro categorías de Lighthouse; esa cifra depende de esta decisión.

### `uis/website/styles.css` se versiona

El sitio es estático y debe funcionar al clonarlo, sin paso de build. El archivo es **generado**: se edita `src/input.css` y se recompila. Editarlo a mano se pierde en la siguiente compilación.

### Los colores de marca son tokens en `src/input.css`

Es la forma que tiene Tailwind 4 de configurar el tema (ya no hay `tailwind.config.js`). Paleta `marca-*` y `acento-*`, fondo oscuro.

### El tracker no usa librería de gestión de estado

El estado vive en la URL (`useSearchParams`) y en los componentes. Los filtros son compartibles por enlace y el botón "atrás" funciona solo. Redux o Zustand aquí sería peso muerto.

> Todo componente que use `useSearchParams` necesita una frontera de `<Suspense>` por encima, o el prerenderizado falla en el build.

### Una sola puerta a la API por aplicación

Todo `fetch` pasa por `lib/api.ts`. Un solo sitio donde tocar cabeceras, manejo de errores o URL base.

### `talent-core` no tiene dependencias de runtime

Funciones puras sin estado, probadas con el runner de `node:test` (112 pruebas). Sin Jest ni Vitest: menos superficie que mantener y arranque instantáneo. No puede arrastrar dependencias porque lo consumen varias interfaces a la vez.

> **Corregido el 16/09/2026.** Esta decisión afirmaba que `talent-core` "se consumirá desde `services/`". Se escribió antes de elegir el lenguaje del backend y dejó de ser cierta al decidir FastAPI: un proceso Python no puede importar un paquete TypeScript. El motor de scoring **se reimplementará en Python** dentro del dominio `recruitment`, usando las 112 pruebas existentes como especificación, y `talent-core` queda como librería de las interfaces. El razonamiento completo y el riesgo de divergencia están en [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) (decisiones D-05 y D-06, riesgo R-05).

### El análisis de tickets vive en un paquete Python, no en el script ni en la API

`packages/incident-analysis/` es la **única** implementación de la validación y las métricas del CSV de tickets. El script `scripts/analyze.py` y la API la importan, no la copian. Es un criterio de evaluación del proyecto, y si estuviera duplicada, el día que cambiara una regla los dos darían números distintos. Mismo papel que `talent-core` en TypeScript.

- **Librería estándar, sin pandas.** Se lee el CSV en streaming con `csv.DictReader`: la memoria no crece con el tamaño del fichero, que en producción puede llegar al millón de líneas.
- **El script no exige instalar el paquete**: añade su carpeta a `sys.path`. La API sí lo instala, en modo editable, desde su `pyproject.toml`.
- **El email del cliente no sale del validador.** `AnalysisResult` contiene solo números y códigos de regla. Hay una prueba que lo comprueba.
- **Prueba de aceptación**: `test_briefing.py` fija los valores esperados del briefing contra `scripts/incidents-nexova.csv`.

### Sin npm workspaces todavía

Cada proyecto tiene su `package.json` y su `package-lock.json`, y se instala por separado desde su carpeta. Es más ruidoso, pero mantiene los proyectos independientes y los workflows de CI acotados por ruta. Se reevaluará cuando dos aplicaciones necesiten compartir el mismo paquete a la vez.

### La API mock del tracker no se envuelve

La API del tracker es la mock centralizada del curso. No se envuelve en un backend propio para aparentar arquitectura: el tracker la sigue llamando directamente. El primer servicio propio, `services/api/`, llegó con el analizador de incidencias y solo sirve lo que es nuestro.

### El backend será un monolito modular por dominios sobre FastAPI

Decidido en el hito 5 y razonado por extenso en [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md). Lo que fija, en corto:

| Punto | Decisión |
| --- | --- |
| Patrón | Monolito modular por dominios. No microservicios (6 personas en Tecnología, sin telemetría hasta el hito 6) ni serverless (arranques en frío y conexiones persistentes del RAG) |
| Ubicación | Un servicio por carpeta: [`services/api/`](../services/api/). Solo se crea el dominio que se implementa |
| Organización interna | Paquetes por dominio (`app/domains/<dominio>/`), no por tipo de archivo. Convención de `fastapi-best-practices`, inspirada en Netflix Dispatch, sobre la base del tutorial oficial *Bigger Applications* |
| Capas | `router` (HTTP) → `service` (negocio) → `models` (persistencia). Un `service` nunca importa `fastapi`; un `router` nunca calcula; un dominio nunca importa los modelos de otro |
| Rutas | Un `APIRouter` por dominio con `prefix` y `tags`. `main.py` solo compone. Sin prefijo de versión mientras los consumidores sean nuestras propias interfaces |
| Errores | `422` para validación de forma (automático de Pydantic), `400` para reglas de negocio lanzadas desde el `service`. Un solo formato, `{"detail": "..."}`. Para subidas de ficheros, además: `413` demasiado grande y `415` tipo o codificación no aceptados |
| Salida de datos | Los schemas de respuesta son **siempre** distintos de los modelos de tabla. Es lo que impide que una nota interna salga por la API |
| CORS | Lista explícita de orígenes, nunca comodín: `allow_credentials=True` lo prohíbe. `localhost` y `127.0.0.1` ambos incluidos —ya nos costó una tarde en el hito 4— |
| Entorno | Configuración tipada y validada al arrancar en el backend (`app/config.py`, variables `NEXOVA_API_*`). Ninguna credencial en variables `NEXT_PUBLIC_`: se incrustan en el bundle durante el build y son públicas |

> **Corregido el 04/11/2026.** La propuesta situaba el servicio en `services/nexova-api/`. El enunciado del analizador de incidencias lo fija en **`services/api/`**, y la evaluación lo busca ahí. El criterio de fondo no cambia: un servicio por carpeta, con todos los dominios dentro. [`ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) es un entregable del hito 5 y no se reescribe; manda esta tabla.
>
> Dos puntos de la propuesta quedan aplazados para no añadir dependencias antes de necesitarlas:
>
> - **La configuración se valida con `pydantic`, el que ya trae FastAPI, y no con `pydantic-settings` (D-03).** Hoy no hay secretos ni `.env` que cargar.
> - **Las pruebas usan `unittest` sobre el `service`, no `pytest` con el cliente de pruebas (D-08).** Ese cliente necesita `httpx`. Las rutas se verifican con el servidor arrancado.

### `services/api` se gestiona con uv y `pyproject.toml`

Decidido el 11/11/2026, con el directorio de proveedores. Sustituye a `pip` + `requirements.txt`.

- **Por qué.** El enunciado de proveedores exige que el seeder corra con `uv run seed`. Eso pide un `pyproject.toml` que declare el comando. Mantener a la vez `requirements.txt` dejaría las dependencias en dos listas que acabarían desincronizadas, así que se retira.
- **`uv.lock` se versiona.** Fija la versión exacta de cada paquete, también los indirectos. Con `requirements.txt` solo se fijaban los directos.
- **La API es un paquete instalable** (`nexova-api`, backend `setuptools`, el mismo que `incident-analysis`). Es lo que permite declarar comandos en `[project.scripts]`.
- **Las versiones directas se siguen fijando con `==`** en `pyproject.toml`, como hasta ahora. Una actualización es un cambio deliberado, no algo que pasa al reinstalar.

### Proveedores: TinyDB detrás de un repositorio

Decidido el 11/11/2026, con el directorio de proveedores. El enunciado pide almacenamiento ligero: TinyDB, un fichero JSON sin servidor.

- **El fichero no se versiona.** `services/api/storage/suppliers.json` está en el `.gitignore` y se rellena con `uv run seed`. La ruta se cambia con `NEXOVA_API_SUPPLIERS_DB_PATH`, que es lo que usan las pruebas y las capturas para no tocar la base de datos de trabajo.
- **Solo `database.py` importa `tinydb`.** El `service` habla con un `SupplierRepository`. Pasar a Postgres es reescribir ese archivo, no el dominio.
- **El seeder no duplica.** Decide por nombre qué falta y valida cada entrada con el mismo modelo que `POST /suppliers`.
- **Códigos de error del dominio:** `404` si no existe y `409` al borrar un suspendido. El BRIEFING dice que los suspendidos se quedan en el directorio por el historial, y la API lo hace cumplir aunque alguien la llame sin pasar por el backoffice. Amplía la tabla de errores de arriba: `409` para una operación que no se permite en el estado actual del recurso.
- **El backoffice no deja escribir la moneda.** La deduce del país (España → EUR, EE. UU. → USD, según el BRIEFING), y la API rechaza una combinación que no cuadre.

### CI acotada por rutas

Cada workflow se dispara solo cuando cambia su carpeta. Ver [`.github/workflows/`](../.github/workflows/):

| Workflow | Qué hace | Se dispara con |
| --- | --- | --- |
| `deploy-website.yml` | Compila Tailwind y publica `uis/website/` en GitHub Pages | push a `main` en `uis/website/**` |
| `verificar-talent-core.yml` | `typecheck` + las 112 pruebas | push a `main` y **toda PR** que toque `packages/talent-core/**` |
| `verificar-backoffice.yml` | `lint`, `build`, `typecheck` y la comprobación de etiquetas de dominio | push a `main` y **toda PR** que toque `uis/backoffice/**` |

## Comandos por carpeta

No hay runner en la raíz. Cada comando se ejecuta **desde su carpeta**.

| Carpeta | Comandos |
| --- | --- |
| `uis/website/` | `npm run dev` (http-server en :3000) · `npm run build:css` · `npm run watch:css` |
| `uis/talent-lab/` | `npm run dev` · `npm run build` (compila la librería + el CSS) |
| `uis/backoffice/` | `npm run dev` · `npm run build` · `npm run typecheck` · `npm run lint` |
| `packages/talent-core/` | `npm run typecheck` · `npm test` · `npm run demo` · `npm run build` |
| `packages/incident-analysis/` | `python -m unittest discover -s tests -t tests` |
| `scripts/` | `python analyze.py incidents-nexova.csv` |
| `services/api/` | `uv sync` · `uv run seed` · `uv run --env-file .env uvicorn app.main:app --reload --port 8000` · `uv run python -m unittest discover -s tests` |

## Restricciones técnicas

- **Entorno de desarrollo: Windows + PowerShell.** Los comandos de la documentación llevan su equivalente cuando difieren (`cp` → `Copy-Item`).
- **`localhost` y `127.0.0.1` son orígenes distintos para el navegador**, aunque apunten a la misma máquina: la política del mismo origen compara el texto del host, no la IP. Next bloquea por defecto sus recursos de desarrollo desde un origen ajeno, así que entrando por `127.0.0.1` la página **no se hidrata y los componentes se quedan colgados en su estado de carga, sin ningún error visible** —la petición a la API ni siquiera llega a hacerse—. `uis/backoffice/next.config.ts` declara `allowedDevOrigins` para que ambas direcciones funcionen.
- **Artefactos generados que no se editan a mano:** `uis/website/styles.css`, `uis/talent-lab/styles.css` y `dist/`, `packages/talent-core/dist/`, `.next/`.
- **`.env*` no se versiona** (salvo `.env.example`). Está en el `.gitignore`.
- **`uis/backoffice/AGENTS.md`** contiene un bloque entre marcadores `BEGIN/END:nextjs-agent-rules` que **regenera `next dev`**. Borrarlo solo lo hace reaparecer sucio en el diff; se commitea tal cual.
- **`CONTEXT.md`, `CONTEXT.es.md` y `docs/contexts/`** se sincronizan desde el syllabus con `scripts/sync_contexts.py`. No se editan a mano salvo el apéndice del hito en curso.
- **`docs/contexts-archive/`** contiene los contextos de las otras tres empresas del track (155 archivos). Está en el [`.ignore`](../.ignore) de la raíz y **no se incluye en búsquedas**: taparía cualquier resultado sobre Nexova.

## Convenciones de código

- Código, nombres de variables y carpetas en **inglés**. Comentarios, documentación, textos de interfaz y mensajes de commit en **español**.
- Cada carpeta de primer nivel tiene su responsabilidad y su `README.md`. Se lee antes de escribir código ahí.
- Cada aplicación, servicio o paquete nuevo va en su subcarpeta y lleva README propio.
- Nada de archivos de implementación en la raíz del repositorio.
