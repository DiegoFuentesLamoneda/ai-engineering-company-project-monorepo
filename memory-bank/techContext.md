# Contexto técnico — monorepo de Nexova

> Qué hay construido, con qué está hecho, qué decisiones ya están tomadas y qué límites no se cruzan.
> Se actualiza **en el mismo commit** que el cambio que lo afecta. Un banco de memoria desfasado es peor que no tenerlo.

## Qué hay hoy en el repositorio

| Ruta | Qué es | Stack | Hito |
| --- | --- | --- | --- |
| [`uis/website/`](../uis/website/) | Web pública de Nexova: landing + formulario de registro de talento | HTML5, Tailwind 4 (CLI), JS sin dependencias | 1 |
| [`packages/talent-core/`](../packages/talent-core/) | Motor de scoring de candidatos y matching de vacantes | TypeScript 5, `node:test`, `tsx` | 2 |
| [`uis/talent-lab/`](../uis/talent-lab/) | Banco de pruebas manual de `talent-core`: dispara sus 18 funciones desde botones | HTML + Tailwind 4 + el `dist/` de `talent-core` | 2 |
| [`uis/backoffice/`](../uis/backoffice/) | Aplicación interna: panel de operaciones, seguimiento de candidaturas, gestor de incidencias centralizado con su análisis del CSV del helpdesk y directorio de proveedores, con login, registro, perfil y recuperación y cambio de contraseña | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind 4 | 3 · 4 · Analizador de incidencias · Directorio de proveedores · AUTH-02 · AUTH-03 · Gestor de incidencias |
| [`packages/shared/`](../packages/shared/) | `@repo/shared-types` — viene de la plantilla, prácticamente vacío | TypeScript | — |
| [`packages/shared/incident-analysis/`](../packages/shared/incident-analysis/) | Validación y métricas de los CSV de tickets de soporte, y el vocabulario del gestor de incidencias con su ciclo de vida. Lógica única que comparten los scripts y la API | Python 3.11+, solo stdlib, `unittest` | Analizador de incidencias · Gestor de incidencias |
| [`scripts/analyze.py`](../scripts/analyze.py) | Analizador de tickets por consola, con exportación a `results.csv` | Python 3, usa `incident-analysis` | Analizador de incidencias |
| [`scripts/seed_incidents.py`](../scripts/seed_incidents.py) | Carga en el gestor de incidencias las filas válidas del CSV del analizador, sin duplicar | Python 3, usa `incident-analysis` y la API | Gestor de incidencias |
| [`scripts/sync_contexts.py`](../scripts/sync_contexts.py) | Descarga los contextos del syllabus y los coloca en `docs/contexts/` | Python 3, solo stdlib | — |
| [`services/api/`](../services/api/) | Backend de Nexova. Dominios: `incidents` (análisis del CSV subido y exportación del último análisis, y el gestor de incidencias centralizado sobre TinyDB), `suppliers` (directorio de proveedores con su seeder, `uv run seed`), `users` y `profiles` (cuentas y sus datos personales, con `uv run create-admin`) `auth` (login con JWT) y `password_resets` (enlace de restablecimiento por email, cambio de contraseña y su auditoría). Todo menos el registro, el login y la recuperación de contraseña pide token. Envía email con Resend | Python 3.11+, FastAPI, Pydantic 2, uvicorn, TinyDB, python-jose, libpass, uv | Analizador de incidencias · Directorio de proveedores · Autenticación (AUTH-01) · AUTH-03 · Gestor de incidencias |

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

El backoffice habla además con la API propia, `services/api/`, para el gestor y el análisis de incidencias y el directorio de proveedores: variable **`NEXT_PUBLIC_NEXOVA_API_URL`** (`http://localhost:8000` en local). Las dos APIs pasan por el mismo `request()` de `lib/api.ts`, cada una con su URL base.

> **Desde AUTH-02 (18/11/2026), el backoffice hace login** y manda el token en `Authorization: Bearer` en cada llamada a la API propia. La API mock del tracker no lo recibe: no es nuestra y no lo pide. Cómo se guarda la sesión y por qué, en la decisión «Backoffice: sesión con el token en `localStorage` y guardia en el cliente».

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

`packages/shared/incident-analysis/` es la **única** implementación de la validación y las métricas del CSV de tickets. El script `scripts/analyze.py` y la API la importan, no la copian. Es un criterio de evaluación del proyecto, y si estuviera duplicada, el día que cambiara una regla los dos darían números distintos. Mismo papel que `talent-core` en TypeScript.

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
| Errores | `422` para validación de forma (automático de Pydantic), `400` para reglas de negocio lanzadas desde el `service`. Un solo formato, `{"detail": "..."}`. Para subidas de ficheros, además: `413` demasiado grande y `415` tipo o codificación no aceptados. `503` si no se puede leer o escribir un fichero de TinyDB. El `422` lleva solo `loc`, `msg` y `type` de cada error, nunca el valor recibido |
| Salida de datos | Los schemas de respuesta son **siempre** distintos de los modelos de tabla. Es lo que impide que una nota interna salga por la API |
| CORS | Lista explícita de orígenes, nunca comodín: `allow_credentials=True` lo prohíbe. `localhost` y `127.0.0.1` ambos incluidos —ya nos costó una tarde en el hito 4— |
| Entorno | Configuración tipada y validada al arrancar en el backend (`app/config.py`, variables `NEXOVA_API_*`). Ninguna credencial en variables `NEXT_PUBLIC_`: se incrustan en el bundle durante el build y son públicas |

> **Corregido el 04/11/2026.** La propuesta situaba el servicio en `services/nexova-api/`. El enunciado del analizador de incidencias lo fija en **`services/api/`**, y la evaluación lo busca ahí. El criterio de fondo no cambia: un servicio por carpeta, con todos los dominios dentro. [`ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) es un entregable del hito 5 y no se reescribe; manda esta tabla.
>
> Dos puntos de la propuesta quedan aplazados para no añadir dependencias antes de necesitarlas:
>
> - **La configuración se valida con `pydantic`, el que ya trae FastAPI, y no con `pydantic-settings` (D-03).** Hoy no hay secretos ni `.env` que cargar.
> - **Las pruebas usan `unittest` sobre el `service`, no `pytest` con el cliente de pruebas (D-08).** Ese cliente necesita `httpx`. Las rutas se verifican con el servidor arrancado.
>
> **Corregido el 13/11/2026, con AUTH-01.** Las dos notas siguen en pie, pero ya no son exactas:
>
> - **Ya hay un secreto.** `NEXOVA_API_JWT_SECRET_KEY` vive en `services/api/.env` (no se versiona; la plantilla es `.env.example`) y lo carga `uv run --env-file .env`. Se sigue validando con `pydantic` en `app/config.py`, sin `pydantic-settings`, y como `SecretStr`, para que no salga en un log. Sin secreto la API no arranca.
> - **Las rutas ya se prueban por HTTP**, sin `httpx`: [`tests/http_client.py`](../services/api/tests/http_client.py) habla con la app por ASGI, como uvicorn, en unas 40 líneas de biblioteca estándar. Si un día entra `httpx`, se sustituye por el `TestClient` sin tocar las pruebas más que en el import.

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

### Autenticación: JWT sin estado y candado por router

Decidido el 12–13/11/2026, con AUTH-01. Lo fija el enunciado: `python-jose` para el token, `libpass[bcrypt]` para las contraseñas, JWT sin estado, sin cookies.

- **El token solo lleva `sub` (el `id`), `iat` y `exp`. HS256 y nada más.** `get_current_user` relee el usuario de TinyDB en cada petición. Un cambio de rol, o una cuenta desactivada o borrada, cuentan desde la petición siguiente, no cuando caduque el token. Caducidad corta: 30 minutos (`NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES`).
- **El `id` de un usuario es un UUID**, no el número de TinyDB. TinyDB reutiliza los números borrados, y el token de una cuenta eliminada identificaría a la siguiente. Los proveedores siguen con el número de TinyDB (limitación conocida).
- **Cuenta y perfil en dos ficheros** (`users.json` y `profiles.json`), uno a uno por `user_id`. El perfil son datos personales que la cuenta no necesita para autenticar, y así nunca viajan junto al hash.
- **Los permisos los decide el `service`**, no el router: cada uno ve, edita y borra lo suyo, y un `admin`, cualquier cosa. Solo un `admin` lista usuarios y cambia roles. La comprobación de permiso va antes que la de existencia, para que nadie averigüe qué IDs existen.
- **El candado de `incidents` y `suppliers` va en el `APIRouter`** (`dependencies=[Depends(get_current_user)]`), no ruta a ruta. Una ruta nueva nace protegida. En `users` va ruta a ruta, porque `POST /users` es público.
- **El primer admin sale de `uv run create-admin`.** `POST /users` crea siempre cuentas `user`, y solo un admin cambia roles.
- **El login no dice qué ha fallado.** Email desconocido, contraseña mala y cuenta desactivada dan el mismo `401`, en el mismo tiempo (se verifica contra un hash de relleno).
- **Amplía la tabla de errores:** `401` para quien no está identificado, con la cabecera `WWW-Authenticate: Bearer`; `403` para quien está identificado pero no tiene permiso.
- **Cambiar la contraseña cierra las demás sesiones** (18/11/2026, con AUTH-03). Sigue la idea de arriba, que el cambio cuente desde la petición siguiente, y la amplía a la contraseña: el usuario guarda `password_changed_at` y `get_current_user` rechaza los tokens con un `iat` anterior (comparado al segundo, redondeando hacia abajo). Vale para el enlace del email, `change-password` y `PUT /users/{id}`. `change-password` devuelve un token nuevo para que quien cambia siga dentro. Las cuentas sin el campo (`None`) no cambian de comportamiento.
- **`forgot-password` responde antes de buscar** (18/11/2026, con AUTH-03): la búsqueda del usuario, el token y el envío van en `BackgroundTasks`. Así ni el texto ni el tiempo de respuesta dicen qué emails tienen cuenta, el mismo principio que el login.
- **Límite por cuenta y registro de auditoría** (18/11/2026, con AUTH-03). La tabla `audit` de `password_resets.json` guarda una entrada por solicitud a las tres rutas, y hace también de contador del límite de `forgot-password` (3 enlaces por cuenta y hora, en el mismo cerrojo que la escritura). El límite es por cuenta, no por email: a un email sin cuenta nunca se le envía nada. Pasado el límite se responde el mismo `200`, no un `429`, para no delatar qué emails existen. **Datos de personas, decidido con Diego:** la cuenta va por `user_id` y nunca por el email (un email sin cuenta no se guarda), la IP va completa y las entradas se borran a los 90 días. La IP es la de `request.client`; detrás de un proxy habrá que arrancar uvicorn con `--proxy-headers`.

### Email transaccional: Resend sobre `urllib`, una clave por entorno

Decidido el 18–19/11/2026, con AUTH-03. Diego eligió Resend para el email de restablecimiento.

- **Sin el SDK de Resend.** Enviar es un solo `POST https://api.resend.com/emails`, y no compensa una dependencia nueva para eso. Lo hace [`mailer.py`](../services/api/app/mailer.py) con `urllib`, con un `User-Agent` propio: Resend está detrás de Cloudflare, que rechaza el de urllib.
- **El servicio no sabe de Resend.** El dominio recibe un `mailer` con un único método, `send`. Sin API key, `build_mailer` elige `LogMailer`, que escribe el email en el log: la API arranca y el flujo se puede probar entero sin cuenta de correo. Cambiar de proveedor es escribir otra clase, no tocar el dominio.
- **La clave es un secreto de la API, nunca del backoffice.** `NEXOVA_API_RESEND_API_KEY` vive en `services/api/.env` como `SecretStr`. Un `NEXT_PUBLIC_` acabaría en el navegador.
- **Una clave por entorno, con el mínimo permiso.** La de desarrollo, `nexova-api-local`, solo tiene *Sending access*: si se filtra, no sirve para tocar la cuenta, y se revoca sin afectar a otro entorno. La de acceso completo que crea el alta de Resend se borra.
- **Los logs `nexova.*` salen en la consola desde `INFO`** (`configure_logging` en [`main.py`](../services/api/app/main.py)). Uvicorn solo configura sus loggers, y sin esto un envío correcto no dejaba rastro. Entre el log («Email enviado a d***@…», siempre con el email enmascarado) y la auditoría, un «no me llega el correo» se diagnostica sin adivinar.

### Backoffice: sesión con el token en `localStorage` y guardia en el cliente

Decidido el 18/11/2026, con AUTH-02. El enunciado fija dos cosas: el token va en `localStorage` y las rutas se protegen con una guardia en el cliente, sin *middleware* de Next.

- **Por qué no una cookie `httpOnly`, que sería más segura.** El enunciado pide `localStorage`, y la API de AUTH-01 es JWT sin estado y sin cookies. Una cookie exigiría cambiar la API y el CORS. Queda anotado para cuando el backoffice salga de la red interna.
- **El riesgo es el XSS: un script inyectado podría leer el token.** Se acota así: React escapa todo lo que pinta, el backoffice no usa `dangerouslySetInnerHTML` (no se añade sin revisar esto), y el token caduca a los 30 minutos.
- **Por qué no *middleware*.** Además de que el enunciado lo excluye, el servidor no puede leer `localStorage`. Por eso el HTML que sale del servidor nunca lleva datos: [`AuthGuard`](../uis/backoffice/components/AuthGuard.tsx) no pinta la vista hasta saber que hay sesión. El candado de verdad sigue en la API: aunque alguien saltara la guardia, sin token recibe `401`.
- **Una sola fuente de verdad para la sesión:** [`lib/session.ts`](../uis/backoffice/lib/session.ts), leída con `useSyncExternalStore`. La caducidad se lee del `exp` del JWT, sin llamar a la API, y la guardia programa un temporizador para cerrar la sesión cuando llegue. El evento `storage` del navegador cierra la sesión en todas las pestañas a la vez.
- **La navegación sigue a la sesión, no al botón.** Los formularios solo guardan o borran el token, y las guardias deciden adónde ir. Cerrar sesión aquí, en otra pestaña o por un `401` acaba en el mismo sitio, por el mismo camino.
- **Un `401` de la API propia cierra la sesión** en [`lib/api.ts`](../uis/backoffice/lib/api.ts), que es la única puerta a la API. Al volver a `/login` se explica por qué (`reason=ended`).
- **El `next` del login se valida** ([`lib/auth-routes.ts`](../uis/backoffice/lib/auth-routes.ts)): solo rutas del propio backoffice. Un enlace con `?next=https://otro-sitio` no saca a nadie fuera tras entrar (redirección abierta).
- **El perfil se guarda enviando solo lo que cambia**, y `null` borra un campo, que es lo que hace `PUT /profiles/me`. Así dos pestañas que editan campos distintos no se pisan.
- **Sin librería de estado, como el tracker.** El menú de sesión se entera de un cambio de perfil con un evento del navegador (`nexova:profile`), no con un *store* global. Si aparecen más datos compartidos entre vistas, se reevalúa.
- **Solo se protege el backoffice.** Es la única aplicación Next.js y la única que llama a la API propia. `uis/website/` es pública por enunciado, y `uis/talent-lab/` no carga datos de nadie.

### Gestor de incidencias: el vocabulario en el paquete compartido y errores pensados para la interfaz

Decidido el 19–20/11/2026, con el gestor de incidencias centralizado.

- **Estados, categorías, orígenes y sedes se definen una sola vez**, como `StrEnum` en [`incident_analysis.catalog`](../packages/shared/incident-analysis/incident_analysis/catalog.py), con el ciclo de vida (`ALLOWED_TRANSITIONS`). Los usan el modelo de la API y el seed. Por eso `incident-analysis` pasó a `packages/shared/`, que es donde la plantilla pone lo que comparten varios proyectos. El backoffice repite los valores en TypeScript ([`types/incident-manager.ts`](../uis/backoffice/types/incident-manager.ts)) porque no puede importar Python, igual que con `talent-core` al revés.
- **El gestor y el analizador conviven en el dominio `incidents`, pero no comparten datos.** El analizador trabaja con el CSV subido y el último análisis en memoria; el gestor, con su fichero de TinyDB (`incidents.json`, `NEXOVA_API_INCIDENTS_DB_PATH`). El seed lleva el histórico del CSV al gestor una vez y recuerda qué tickets entraron, para no duplicarlos.
- **Excepción a la tabla de errores: las rutas del gestor dan `400`, no `422`, en la validación de forma.** Lo pide el enunciado, con el campo que falla. Se hace con una clase de ruta propia en un `APIRouter` aparte, no con un manejador global: el resto de la API sigue con el `422` que ya usa el backoffice. Cada error lleva un `code` estable, y el formulario escribe su texto a partir de él, no del mensaje.
- **`409` para un cambio de estado que el ciclo de vida no permite, y también para el que llega segundo.** El repositorio solo escribe si el estado sigue siendo el que se leyó: dos personas no se pisan sin saberlo.
- **El `500` sale en JSON y con CORS**, desde un middleware por dentro de CORS. Sin él, el navegador oculta la respuesta y el frontend solo ve «Failed to fetch».
- **En el backoffice, el cambio de estado es optimista.** La fila cambia al momento y vuelve atrás con un mensaje propio si la API lo rechaza. La fila que deja de cumplir el filtro se queda hasta recargar, para que no desaparezca bajo el cursor.
- **El resumen carga aparte de la lista y sin filtros.** Si `/summary` falla, solo cae el panel. Se vuelve a pedir tras cada cambio de estado confirmado (un contador, `revision`, sin librería de estado). Es el estado de toda la base, no de lo filtrado.
- **Solo en español.** El briefing pide versión bilingüe solo si la interfaz ya la tenía, y el backoffice no la tiene.

### Gestión de errores: una estrategia por capa

Decidido el 20/11/2026, con la auditoría de [`ERROR_HANDLING_AUDIT.md`](../docs/ERROR_HANDLING_AUDIT.md). Es la regla para todo lo que se construya a partir de ahora.

- **Backoffice: todo `fetch` pasa por [`lib/api.ts`](../uis/backoffice/lib/api.ts).** Convierte cualquier fallo en un `ApiError` con un texto en español y sin el código HTTP. `status 0` significa red o configuración. Un cuerpo que no se puede leer también se convierte en `ApiError`, nunca en `SyntaxError`. Los componentes no escriben mensajes para códigos concretos salvo en los formularios, que traducen el `code` o el campo.
- **Cada carga tiene tres estados y una salida.** Cargando, éxito y error, con texto legible. Cada error lleva «Reintentar» (los hooks devuelven `recargar`, que sube un contador `intento`) o un enlace para volver. Si un bloque falla y el resto de la página no depende de él, solo cae ese bloque, como el resumen de incidencias.
- **Los datos de la API se leen con `?.` y un valor de reserva**: `?? []`, `?? 0` y `?? "—"`. A una etiqueta que falta se le pinta el valor tal cual, para no dejar el hueco.
- **El `finally` de los formularios de acceso solo reactiva el botón si el envío ha fallado.** Si sale bien, se queda bloqueado hasta la redirección.
- **Páginas de error de Next** (`error.tsx`, `global-error.tsx` y `not-found.tsx`): en español y sin `error.message`, que es texto técnico. Como referencia solo se enseña el `digest`.
- **API:** el `422` sin `input` (no devuelve lo que envió el usuario); el `503` cuando falla el almacenamiento; el `500`, en JSON. Cualquier fallo de un servicio externo, incluido un corte a mitad de respuesta, se traduce a un error propio, como el `EmailDeliveryError` de Resend, y en el log solo van su código y su tipo. Nunca salen trazas, valores de configuración ni secretos.
- **Scripts:** `try/except` alrededor de cada lectura, escritura y apertura de base de datos. El mensaje va a `stderr` y el script sale con `sys.exit(1)`. Ctrl+C sale limpio. Un script que procesa varias cosas cuenta los fallos y sale con `1` si hubo alguno.

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
| `packages/shared/incident-analysis/` | `python -m unittest discover -s tests -t tests` |
| `scripts/` | `python analyze.py incidents-nexova.csv` |
| `services/api/` | `uv sync` · `uv run seed` · `uv run python ../../scripts/seed_incidents.py` · `uv run create-admin` · `uv run --env-file .env uvicorn app.main:app --reload --port 8000` · `uv run python -m unittest discover -s tests` |

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
