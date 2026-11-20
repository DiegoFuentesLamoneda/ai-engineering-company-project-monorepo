# Estado del desarrollo

> Qué está entregado, qué está en curso y qué viene después.
> **Se actualiza en el mismo commit que cierra un trabajo.** Es el paso 3 del flujo de [`AGENTS.md`](../AGENTS.md).

_Última actualización: 20 de noviembre de 2026 (gestor de incidencias centralizado)._

## Entregado

| Hito | Entregable | Dónde | Rama | PR |
| --- | --- | --- | --- | --- |
| 1 — Sitio Web Público | Landing corporativa + formulario de registro de talento. Lighthouse 100/100/100/100. Desplegado en GitHub Pages | [`uis/website/`](../uis/website/) | `hito-01-web-publica` | #1 · fusionada el 14/08/2026 |
| 2 — Fundamentos de Programación | `@repo/talent-core`: filtros, búsquedas lineal y binaria, scoring, ranking, reportes y validaciones. 112 pruebas en verde. Banco de pruebas web | [`packages/talent-core/`](../packages/talent-core/) · [`uis/talent-lab/`](../uis/talent-lab/) | `feature/domain-models` | #2 · fusionada el 16/09/2026 |
| 3 — Talent Pipeline Tracker | Listado, filtros y búsqueda sin recarga, detalle, cambio de estado y etapa, notas internas, alta y edición de candidaturas | [`uis/backoffice/`](../uis/backoffice/) | `feature/talent-pipeline-tracker` | #3 · fusionada el 16/09/2026 |
| 4 — Ingeniería impulsada por IA | Banco de memoria, `AGENTS.md`, reglas y skills en `.agents/`, traslado del tracker a `uis/backoffice/` con panel de entrada propio, CI del backoffice | [`memory-bank/`](../memory-bank/) · [`.agents/`](../.agents/) · [`uis/backoffice/`](../uis/backoffice/) | `feature/agent-memory-bank` | #4 · fusionada el 16/09/2026 |
| 5 — Backend (5a) | Propuesta de arquitectura del backend | [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) | `feature/backend-architecture-proposal` | #5 · fusionada el 18/09/2026 |
| Analizador de incidencias | Paquete de análisis, script por consola, `POST /api/incidents/analyze` con su exportación y página de análisis (hoy en `/incidents/analyze`) | [`packages/shared/incident-analysis/`](../packages/shared/incident-analysis/) · [`scripts/analyze.py`](../scripts/analyze.py) · [`services/api/`](../services/api/) | `feature/incidents-analyzer` | #6 · fusionada el 18/11/2026 |
| Directorio de proveedores | API `/suppliers` sobre TinyDB con seeder y página `/suppliers` | [`services/api/`](../services/api/) · [`uis/backoffice/`](../uis/backoffice/) | `feature/supplier-directory` | #7 · fusionada el 18/11/2026 |
| Autenticación de la API (AUTH-01) | Cuentas, perfiles, login con JWT y candado en las rutas de `incidents` y `suppliers` | [`services/api/`](../services/api/) | `feature/auth-api` | #8 · fusionada el 18/11/2026 |

### Cambio en el modelo de ramas — 16/09/2026

Hasta ahora las ramas **se apilaban**: cada hito salía de la rama del anterior, porque las PRs se dejaban abiertas para la evaluación del campus y `main` solo contenía el hito 1.

Aprobadas ya las cuatro entregas, las PRs #2, #3 y #4 se fusionaron en orden con *merge commit* —no *squash*, que habría reescrito los identificadores de commit y dejado las PRs apiladas con conflictos falsos—. **`main` contiene ahora los cuatro hitos**, y a partir del hito 5 cada rama sale de `main`. Las ramas de hito no se borran: los enlaces de la evaluación siguen apuntando a ellas.

### Decisiones del hito 4

- **El tracker se movió, no se duplicó.** La plantilla del monorepo reserva `uis/backoffice/` para las aplicaciones internas. Se movió con `git mv` para conservar el historial, en un commit separado del que añadía contenido nuevo.
- **`uis/talent-lab/` se queda donde está.** Es un proyecto con interfaz y `uis/` es su sitio según el README de la plantilla.
- **`uis/website/` no se toca.** Ya cumple lo que pide el hito y migrarla a un framework pondría en riesgo el 100 de Lighthouse y el despliegue a Pages.
- **`.agents/` no es `/agents`.** `.agents/` configura las herramientas de desarrollo. `/agents` es producto, y llega en hitos posteriores.

### Fusión de las PRs #6, #7 y #8 — 18/11/2026

Las tres ramas estaban **apiladas**: proveedores salía del analizador y la autenticación, de proveedores, porque `services/api/` todavía no estaba en `main`. Aprobadas las tres, se fusionaron en orden (#6, #7, #8) con *merge commit*, por la misma razón que el 16/09: un *squash* habría reescrito los commits y dejado las siguientes con conflictos falsos. `main` contiene ya `services/api/` completo, y AUTH-02 sale de `main`.

## Hito 5: Backend

Rama `feature/backend-architecture-proposal`, salida de `main`. El hito tiene **dos proyectos encadenados**:

### 5a — Propuesta de arquitectura (en curso)

Documento técnico, no código: [`docs/ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md). Razonamiento sobre cómo estructurar el backend antes de escribirlo.

| Paso | Estado |
| --- | --- |
| Investigación de convenciones estándar de FastAPI, con fuentes citadas | ✅ |
| Redacción de la propuesta: patrón, estructura, routers, CORS y entorno, decisiones y riesgos | ✅ |
| Actualizar el apéndice de `CONTEXT.md` y `CONTEXT.es.md` al hito 5 | ✅ |
| Actualizar el banco de memoria | ✅ |
| PR hacia `main`: #5, fusionada el 18/09/2026 | ✅ |

**Decisiones propuestas en el documento** (pasan a [`techContext.md`](./techContext.md) cuando se implementen):

- **Monolito modular por dominios** sobre FastAPI, no microservicios ni serverless. Justificado por el tamaño del equipo de Tecnología (6 personas), la ausencia de telemetría hasta el hito 6, el acoplamiento natural entre dominios y un volumen de cientos de usuarios.
- **Un servicio, `services/nexova-api/`** —ubicado finalmente en `services/api/`, ver [`techContext.md`](./techContext.md)—, con paquetes por dominio (`app/domains/<dominio>/`) y tres capas: `router` → `service` → `models`.
- **Estructura por dominio, no por tipo de archivo**, siguiendo la convención de `fastapi-best-practices` (inspirada en Netflix Dispatch) sobre la base del tutorial oficial *Bigger Applications*.
- **El motor de scoring se porta a Python.** Ver la deuda técnica más abajo.
- **CORS con lista explícita de orígenes** —`localhost` y `127.0.0.1` incluidos desde el primer commit— y ninguna credencial en variables `NEXT_PUBLIC_`.

### 5b — API de inventario (siguiente)

Implementación del ticket **NXV-0201**: `Asset`, `AssetEntry`, `AssetExit`, stock calculado como entradas menos salidas y todas las rutas bajo `/inventory`. Especificación literal en [`docs/contexts/05-backend-development.es.md`](../docs/contexts/05-backend-development.es.md). Es el hito en el que [`services/`](../services/) deja de estar vacío.

**Estado a 04/11/2026:** la PR #5 (propuesta de arquitectura) está fusionada en `main`. La API de inventario **no está empezada**: se pospone para hacer antes el analizador de incidencias, y entrará como otro dominio del mismo servicio `services/api/`.

## Analizador de incidencias — entregado (#6)

Rama `feature/incidents-analyzer`, salida de `main`. Especificación: [`docs/contexts/proyectos/incidents-file-analysis.es.md`](../docs/contexts/proyectos/incidents-file-analysis.es.md). Script de análisis del CSV de tickets de soporte de Roberto Díaz, y después la misma lógica en la API y en el backoffice.

| Paso | Estado |
| --- | --- |
| Lógica compartida en [`packages/shared/incident-analysis/`](../packages/shared/incident-analysis/): validación, métricas, exportación e informe. 44 pruebas, incluida la de aceptación contra el briefing | ✅ |
| Script [`scripts/analyze.py`](../scripts/analyze.py): 100 / 96 / 4 y todos los desgloses coinciden con el briefing | ✅ |
| API en [`services/api/`](../services/api/): `POST /api/incidents/analyze` y `GET /api/incidents/results/export`. 18 pruebas del service y la configuración; rutas, errores y CORS verificados con el servidor arrancado; la exportación es idéntica byte a byte a la del script | ✅ |
| Página [`/incidents`](../uis/backoffice/components/IncidentAnalyzer.tsx) en el backoffice (desde el gestor de incidencias, en `/incidents/analyze`): subida por arrastre o selector, totales, desglose por categoría y estado, índice de satisfacción, registros inválidos por regla con sus filas y descarga del CSV. Verificada en el navegador con la API arrancada: cifras del briefing, CSV descargado idéntico byte a byte al del script, y errores 400 y 415 mostrados con el mensaje de la API | ✅ |
| Capturas (consola e interfaz) y PR hacia `main`: [#6](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/6), abierta el 04/11/2026 para la evaluación del campus y fusionada el 18/11/2026 | ✅ |

## Directorio de proveedores — entregado (#7)

Rama `feature/supplier-directory`, **apilada sobre `feature/incidents-analyzer`**, porque `services/api/` todavía no está en `main` (PR #6 abierta). Especificación: [`docs/contexts/proyectos/supplier-directory.es.md`](../docs/contexts/proyectos/supplier-directory.es.md). API de proveedores sobre FastAPI + TinyDB + Pydantic, con seeder y página en el backoffice. Lo pide Patricia Solís (HR Manager) para sustituir su hoja de cálculo.

| Fase | Estado |
| --- | --- |
| 1 — Montaje: `services/api` pasa a `pyproject.toml` + uv, TinyDB 4.9.0 añadido, `requirements.txt` retirado. 18 pruebas en verde y la API arranca con `uv run` | ✅ |
| 2 — Modelo de datos: [`schemas.py`](../services/api/app/domains/suppliers/schemas.py) con enums de país, moneda, categoría y estado, tarifa > 0 (y finita), moneda según el país, entrada y salida separadas, `extra="forbid"` en la entrada. 19 pruebas | ✅ |
| 3 — Base de datos y seeder: [`database.py`](../services/api/app/domains/suppliers/database.py) (TinyDB en `services/api/storage/suppliers.json`, ignorado por git, con filtros por país y categoría) y [`seed.py`](../services/api/app/seed.py) (`uv run seed`: 15 insertados la primera vez, 0 la segunda). 55 pruebas en total | ✅ |
| 4 — Endpoints `/suppliers`: [`router.py`](../services/api/app/domains/suppliers/router.py) y [`service.py`](../services/api/app/domains/suppliers/service.py). Alta `201`, listado con filtros, detalle, tarifa (renueva `updated_at`), estado y baja; `404`/`422` y `409` al borrar un suspendido (decisión de Diego, 11/11/2026). Probado a mano con curl y tras reiniciar. 70 pruebas | ✅ |
| 5 — Página [`/suppliers`](../uis/backoffice/components/SupplierList.tsx) en el backoffice, en el menú: tabla, filtros por país y categoría en la URL, tarifa y estado editables por fila, suspendidos atenuados, aviso de renovación a 60 días y alta en `/suppliers/new` con validación y errores de la API en español. Etiquetas aprobadas por Diego (11/11/2026). Typecheck, lint y build en verde, y 20 comprobaciones en el navegador | ✅ |
| 6 — Cierre: capturas del seeder, de Swagger con un filtro y de la interfaz con un filtro; banco de memoria ([`techContext.md`](./techContext.md): TinyDB detrás de un repositorio y el `409`) y PR hacia `main`: [#7](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/7), abierta el 11/11/2026 para la evaluación del campus y fusionada el 18/11/2026 | ✅ |

**Estructura:** dominio `app/domains/suppliers/`, no los archivos sueltos que propone el enunciado (`models.py`, `routes/suppliers.py`…). Lo decidió la propuesta de arquitectura del hito 5. La PR lleva una tabla con la equivalencia entre los dos.

**La rama estaba apilada sobre la #6**, así que su PR mostraba también esos commits. Se fusionó justo después de la #6.

## Autenticación de la API (AUTH-01) — entregado (#8)

Rama `feature/auth-api`, **apilada sobre `feature/supplier-directory`** (PR #7 abierta). Proyecto «Asegurando la API: Autenticación y Restricción de Rutas en FastAPI», ticket **AUTH-01**: usuarios (solo credenciales) y perfiles en TinyDB, login con JWT y `get_current_user` en toda ruta que no sea pública. El enunciado no está en `docs/contexts/`: lo pegó Diego el 12/11/2026.

**Decisiones de Diego (12/11/2026):** las dependencias del enunciado (`python-jose`, `libpass`); se protegen las 8 rutas de `incidents` y `suppliers`; `GET /users` solo para `admin`; el primer admin se crea con un comando, `uv run create-admin`.

| Fase | Estado |
| --- | --- |
| 1 — Preparación: `python-jose[cryptography]==3.5.0` y `libpass[bcrypt]==1.9.4`; secreto, caducidad y fichero de usuarios en [`config.py`](../services/api/app/config.py); [`.env.example`](../services/api/.env.example); sin secreto la API no arranca (el seeder sí). 75 pruebas | ✅ |
| 2 — Modelos `User` y `Profile` y su repositorio en TinyDB: [`users/`](../services/api/app/domains/users/) y [`profiles/`](../services/api/app/domains/profiles/), dos ficheros de TinyDB. `id` UUID (TinyDB reutiliza sus números), email único en minúsculas, contraseña de 8 caracteres a 72 bytes, `role` fuera del alta, `UserPublic` sin hash. 33 pruebas | ✅ |
| 3 — Service de usuarios: [`users/service.py`](../services/api/app/domains/users/service.py) (bcrypt, alta con perfil y marcha atrás si el perfil falla, permisos: tú mismo o admin, rol solo admin, login sin pistas) y [`create_admin.py`](../services/api/app/create_admin.py) (`uv run create-admin`). 137 pruebas | ✅ |
| 4 — Token: [`auth/`](../services/api/app/domains/auth/) con `POST /auth/login` (formulario OAuth2, el email en `username`), `get_current_user` (401 sin token, caducado, manipulado o de cuenta borrada o desactivada; el usuario se relee en cada petición) y `GET /auth/me`. JWT HS256 con solo `sub` y fechas. 156 pruebas | ✅ |
| 5 — Rutas: [`users/router.py`](../services/api/app/domains/users/router.py) (`POST /users` pública con perfil; el resto con token, tú o admin, `403` antes que `404`, `409` email repetido) y [`profiles/router.py`](../services/api/app/domains/profiles/router.py) (`/profiles/me`). Pruebas HTTP de verdad con un cliente ASGI propio ([`http_client.py`](../services/api/tests/http_client.py)), sin `httpx`. 185 pruebas | ✅ |
| 6 — Candado en las 8 rutas que ya existían: las 2 de `incidents` y las 6 de `suppliers`, con `dependencies=[Depends(get_current_user)]` en cada router. Sin token, `401` y nada cambia; con token, igual que antes. Pruebas en [`test_protected_routes.py`](../services/api/tests/test_protected_routes.py). 194 pruebas. Hasta AUTH-02 el backoffice no hacía login y esas pantallas recibían `401` | ✅ |
| 7 — Verificación: 194 pruebas en verde; recorrido en `/docs` con una cuenta de prueba (`401` sin token, alta `201`, *Authorize*, `/auth/me`, `200` con token, `403` en `GET /users`), con 5 capturas para la PR; y un script contra el servidor real, 29/29. Pasos en la sección "Verificación manual en `/docs`" del [README de la API](../services/api/README.md) | ✅ |
| 8 — Cierre: banco de memoria ([`techContext.md`](./techContext.md): decisión de autenticación y dos correcciones; [`projectbrief.md`](./projectbrief.md): vocabulario de cuentas), ficha en la biblioteca y PR hacia `main`: [#8](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/8), abierta el 13/11/2026 para la evaluación del campus, con las 8 rutas protegidas y cómo se verificaron, y fusionada el 18/11/2026 | ✅ |

## Autenticación en el backoffice (AUTH-02) — en revisión (#9)

Rama `feature/auth-frontend`, salida de `main` después de fusionar #6, #7 y #8. Proyecto «Conectando el Candado: Flujos de Autenticación en el Frontend», ticket **AUTH-02**: login, registro y perfil dentro del backoffice, guardia de sesión en el cliente y token en `localStorage`. Cierra la rotura temporal de AUTH-01: las pantallas de incidencias y proveedores vuelven a funcionar, ahora con sesión. El enunciado no está en `docs/contexts/`: lo pegó Diego el 18/11/2026.

| Fase | Estado |
| --- | --- |
| 1 — Sesión en el cliente de la API: [`lib/session.ts`](../uis/backoffice/lib/session.ts) (token en `localStorage`, caducidad leída del JWT, aviso entre pestañas) y [`lib/api.ts`](../uis/backoffice/lib/api.ts), que pone `Authorization: Bearer` en toda llamada a `services/api` y cierra la sesión ante un `401` | ✅ |
| 2 — Grupos de rutas: las vistas internas pasan a `app/(protected)/` y las de acceso, a `app/(auth)/`, con un layout raíz común. El movimiento va en su propio commit | ✅ |
| 3 — `/login` y `/register`: errores bajo cada campo; `POST /users` con nombre, teléfono y dirección opcionales y login automático después; email repetido como error del campo email. 31 comprobaciones en el navegador | ✅ |
| 4 — [`AuthGuard`](../uis/backoffice/components/AuthGuard.tsx) y [`GuestGuard`](../uis/backoffice/components/GuestGuard.tsx): sin sesión, `/login?next=…`; con sesión, fuera de `/login`; cerrar sesión; aviso cuando la sesión se cierra por un `401`, por caducidad o desde otra pestaña; `next` validado contra redirecciones abiertas. 29 comprobaciones | ✅ |
| 5 — [`/account/profile`](../uis/backoffice/components/ProfileForm.tsx): datos de `GET /auth/me`, edición con `PUT /profiles/me` enviando solo lo que cambia, y el menú de sesión se actualiza sin recargar. 25 comprobaciones | ✅ |
| 6 — Verificación de extremo a extremo contra la API real: las 9 vistas protegidas con y sin sesión, registro, perfil, cerrar sesión, login fallido y `401`; `uis/website/` sin cambios frente a `main` y funcionando. 55/55 | ✅ |
| 7 — Cierre: banco de memoria, READMEs, ficha en la biblioteca y PR hacia `main`: [#9](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/9), abierta el 18/11/2026 para la evaluación del campus, con las 9 vistas protegidas y la web pública sin cambios | ✅ |

**Solo se protege el backoffice.** Es la única aplicación Next.js del monorepo y la única que llama a la API propia. `uis/website/` es pública por enunciado, y `uis/talent-lab/` es un banco de pruebas estático de `talent-core`: no llama a ninguna API ni muestra datos de personas.

## Recuperación y cambio de contraseña (AUTH-03) — en revisión (#10)

Rama `feature/password-reset`, **apilada sobre `feature/auth-frontend`** (PR #9 abierta): necesita el `/login` del backoffice. Proyecto «La Pieza Que Faltaba: Flujo de Restablecimiento de Contraseña», ticket **AUTH-03**: `POST /auth/forgot-password`, `/auth/reset-password` y `/auth/change-password`, y sus tres pantallas en el backoffice. El enunciado no está en `docs/contexts/`: lo pegó Diego el 18/11/2026.

**Decisiones de Diego (18/11/2026):** Resend como servicio de correo, y los tres extras opcionales: email en HTML, *rate limiting* por cuenta y hora, y registro de auditoría.

| Fase | Estado |
| --- | --- |
| 1 — Configuración: API key de Resend, remitente, URL del backoffice, caducidad del enlace (15–60 min) y solicitudes por hora en [`config.py`](../services/api/app/config.py) y [`.env.example`](../services/api/.env.example). Sin API key la API arranca y el enlace va al log. 199 pruebas | ✅ |
| 2 — Tokens de restablecimiento: dominio [`password_resets/`](../services/api/app/domains/password_resets/). Token aleatorio de 256 bits; en TinyDB solo su SHA-256, la caducidad y cuándo se usó. Pedir otro anula el anterior; usarlo dos veces, caducado o inventado da el mismo error (el motivo, aparte, para la auditoría). De dos usos simultáneos solo gana uno. 215 pruebas | ✅ |
| 3 — Envío de correo: [`mailer.py`](../services/api/app/mailer.py) (Resend con `urllib`, sin SDK; sin API key, el email va al log y la API arranca igual; los errores nunca llevan la clave) y [`emails.py`](../services/api/app/domains/password_resets/emails.py) (HTML de tablas y estilos en línea, 480 px, botón y enlace en texto, más versión en texto). Prueba real: `python -m app.mailer <email>`. 231 pruebas | ✅ |
| 4 — Rutas: [`password_resets/router.py`](../services/api/app/domains/password_resets/router.py). `forgot-password` responde siempre lo mismo y busca y envía en segundo plano (ni el texto ni el tiempo delatan qué emails existen). `reset-password` da `400` con un enlace usado, caducado o inventado. `change-password` pide la actual y devuelve un token nuevo. Cambiar la contraseña por cualquier vía cierra las demás sesiones (`password_changed_at`). 257 pruebas | ✅ |
| 5 — *Rate limiting* y registro de auditoría: tabla `audit` en `password_resets.json`. Una entrada por solicitud a las tres rutas (evento, IP, `user_id`, motivo). Como mucho 3 enlaces por **cuenta** y hora; la cuarta solicitud recibe el mismo `200` y no sale email. La auditoría hace de contador, y contar y anotar van en el mismo cerrojo. Decisión de Diego (18/11/2026): `user_id` y nunca el email, IP completa, se borra a los 90 días. 279 pruebas | ✅ |
| 6 — Pantallas sin sesión en el [backoffice](../uis/backoffice/): enlace «¿Olvidaste tu contraseña?» en `/login`; `/forgot-password` con el mensaje fijo del ticket y el formulario desactivado tras enviar (solo un fallo de red o de la API sale como error); `/reset-password?token=` con confirmación local, `no-referrer`, éxito a `/login?reason=password-reset` con `replace`, y con enlace no válido el error de la API y «Pedir un enlace nuevo». Ambas estáticas y detrás de `GuestGuard`. Prueba en el navegador con Playwright contra la API real: 26/26 comprobaciones | ✅ |
| 7 — `/account/change-password` en el backoffice, enlazada desde Mi perfil (el menú sigue marcando «Mi perfil»). Confirmación, longitud y «distinta de la actual» se comprueban antes de llamar a la API. Con la actual incorrecta, el mensaje de la API bajo el campo y la sesión intacta. Si sale bien, `lib/api.ts` guarda el token nuevo y se sigue dentro; las demás sesiones acaban en `/login` con «Tu sesión se ha cerrado». Prueba en el navegador con Playwright contra la API real, con una segunda sesión como «otro equipo»: 20/20 comprobaciones | ✅ |
| 8 — Verificación de extremo a extremo con un email real (18/11/2026). Clave de Resend propia del entorno local (`nexova-api-local`), solo *Sending access*: envía, y listar dominios da `401 restricted_api_key`; la de acceso completo que crea el alta de Resend, borrada. Diego hizo el recorrido en el navegador con la API real y bases temporales: alta, «¿Olvidaste tu contraseña?», el email llegó a la bandeja de entrada (no a spam), contraseña nueva, `/login` con la nueva; el mismo enlace otra vez da el error de enlace no válido. La auditoría lo anotó todo, incluido un primer intento con una errata en el email (`unknown_account`, sin envío). Ni la clave ni nada con forma de clave en el historial (gitleaks), los archivos versionados, el log ni el build del backoffice | ✅ |
| 9 — Cierre (19/11/2026): los logs `nexova.*` salen en la consola desde `INFO`, para ver también cuándo un email sale bien; captura del email con el token tapado en [`docs/screenshots/`](../docs/screenshots/); «avisar del enlace gastado al abrirlo» anotado como posible mejora en el [README del backoffice](../uis/backoffice/README.md); banco de memoria ([`techContext.md`](./techContext.md): decisión de email transaccional); ficha en la biblioteca y PR hacia `main`: [#10](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/10), abierta el 19/11/2026 para la evaluación del campus. Apilada sobre #9: hasta que se fusione, su diff incluye los commits de AUTH-02 | ✅ |

## Gestor de incidencias centralizado — en revisión (#11)

Rama `feature/incident-manager`, **apilada sobre `feature/password-reset`** (PR #10 abierta): las rutas nuevas llevan el candado de AUTH-01 y las pantallas necesitan la sesión de AUTH-02. Especificación: [`centralized-incident-manager.es.md`](../docs/contexts/proyectos/centralized-incident-manager.es.md). Un solo sitio para las incidencias que hoy llegan por email, Slack o de viva voz. Lo piden Sergio Molina (CTO), Roberto Díaz (Customer Support Lead) y Laura Mendoza (CEO).

**Decisiones de Diego (19/11/2026):** el gestor guarda en su propio fichero de TinyDB, aparte del analizador; el vocabulario del briefing vive en `packages/shared/incident-analysis/`, que pasa a `packages/shared/` para que lo usen el seed y la API; etiquetas de estados, categorías y orígenes aprobadas; interfaz solo en español.

| Fase | Estado |
| --- | --- |
| 1 — `incident-analysis` se mueve a [`packages/shared/`](../packages/shared/incident-analysis/) (en su propio commit) y gana el vocabulario del gestor, [`catalog.py`](../packages/shared/incident-analysis/incident_analysis/catalog.py), y la transformación de una fila del CSV en incidencia, [`seeding.py`](../packages/shared/incident-analysis/incident_analysis/seeding.py). 76 pruebas | ✅ |
| 2 — Modelo `Incident` y su repositorio: [`database.py`](../services/api/app/domains/incidents/database.py), TinyDB en `storage/incidents.json` con las tablas `incidents` y `seed_imports`. `id` UUID, toda incidencia nace `open`, y el cambio de estado solo se escribe si nadie lo cambió antes | ✅ |
| 3 — Seed: [`scripts/seed_incidents.py`](../scripts/seed_incidents.py) carga las 96 filas válidas del CSV del analizador. Repetirlo no duplica (`seed_imports` recuerda qué `ticket_id` entró) | ✅ |
| 4 — Rutas en [`router.py`](../services/api/app/domains/incidents/router.py): `POST`, `GET` con filtros combinables, `GET /{id}`, `PATCH /{id}/status` y `GET /summary`. `400` con el campo y un `code`, `404`, `409` para un cambio que no permite el ciclo de vida, y `500` en JSON con las cabeceras de CORS. 355 pruebas | ✅ |
| 5 — Alta en `/incidents/new` ([`IncidentForm`](../uis/backoffice/components/IncidentForm.tsx)): errores bajo cada campo, escritos a partir del `code` de la API, y ayuda literal del briefing en categoría y origen | ✅ |
| 6 — Lista en `/incidents` ([`IncidentManagerList`](../uis/backoffice/components/IncidentManagerList.tsx)): filtros en la URL, botón «Solo incumplimientos de SLA», estados de carga, error con «Reintentar» y vacío, y cambio de estado optimista que vuelve atrás si la API lo rechaza. El analizador se mueve a `/incidents/analyze` | ✅ |
| 7 — Panel de resumen ([`IncidentSummaryPanel`](../uis/backoffice/components/IncidentSummaryPanel.tsx)): totales por estado, incumplimientos de SLA y reparto por sede, origen y categoría. Carga aparte de la lista: si `/summary` falla, un aviso y la lista sigue. Se vuelve a pedir tras cada cambio de estado confirmado | ✅ |
| 8 — Verificación y cierre (20/11/2026): Playwright contra la API real, 22/22 comprobaciones (alta desde el formulario, filtros, SLA, `PATCH` real con el resumen al día, `409` simulado que devuelve la fila a «Abierta», `/summary` y la lista caídos con «Reintentar»); capturas en [`docs/screenshots/`](../docs/screenshots/); banco de memoria; ficha en la biblioteca y PR hacia `feature/password-reset`: [#11](https://github.com/DiegoFuentesLamoneda/ai-engineering-company-project-monorepo/pull/11), abierta el 20/11/2026 y entregada en 4Geeks esa misma noche, del 19 al 20/11, para la evaluación del campus. Apilada sobre #10: hasta que se fusione, su diff incluye los commits de AUTH-02 y AUTH-03 | ✅ |

## Próximo

Telemetría (6), pipelines de datos (6b), RAG sobre la base de candidatos (7), memoria y harness de agentes (8), workflows agénticos (9) y tiempo real (10).

**Qué proyecto toca lo marca la web de 4Geeks**, y Diego pega el enunciado al empezar. Que un contexto esté en `docs/contexts/` no lo convierte en el siguiente.

**Rama del siguiente proyecto (20/11/2026):** las PRs #9 (AUTH-02), #10 (AUTH-03, apilada sobre #9) y #11 (gestor de incidencias, apilada sobre #10) siguen abiertas, a la espera de la revisión del campus. Si el siguiente proyecto necesita algo de ellas, su rama sale de `feature/incident-manager`, que ya lo contiene todo, y se apila. Si no lo necesita, sale de `main`. Al fusionar, en orden #9, #10 y #11, con *merge commit*, como el 18/11.

## Deuda técnica y decisiones aplazadas

| Asunto | Estado |
| --- | --- |
| **Port del scoring a Python** | Abierto desde el hito 5. `talent-core` es TypeScript y FastAPI no puede importarlo. Se reimplementará dentro del dominio `recruitment` usando sus 112 pruebas como especificación. Hasta que el port esté completo, la lógica vive en dos lenguajes: riesgo de divergencia documentado en [`ARCHITECTURE_PROPOSAL.md`](../docs/ARCHITECTURE_PROPOSAL.md) §8 |
| **Versionado de la API** | Aplazado. Se despliega sin prefijo de versión porque el ticket NXV-0201 exige las rutas literalmente bajo `/inventory`. Se introduce `/api/v1` cuando exista el primer consumidor externo |
| **Migraciones con Alembic** | Aplazado. Se adoptan cuando haya datos que no se puedan perder |
| **npm workspaces** | Aplazado. Cada proyecto se instala por separado. Se reevalúa cuando dos aplicaciones consuman el mismo paquete a la vez |
| **`packages/shared/`** | Viene de la plantilla y está prácticamente vacío. Decidir si se usa o se retira cuando haya tipos que compartir de verdad |
| **Ambigüedad en `CONTEXT.md`** | El responsable de Ventas aparece con dos nombres distintos. Sin resolver — ver [`projectbrief.md`](./projectbrief.md). Bloqueará el dominio de ventas cuando llegue |
| **Regla de ramas desfasada** | [`AGENTS.md`](../AGENTS.md) §9 y [`.agents/rules/commits-y-entrega.md`](../.agents/rules/commits-y-entrega.md) siguen diciendo que cada rama sale de la del hito anterior. En la práctica, una rama sale de `main` si lo anterior ya está fusionado (AUTH-02) y se apila solo cuando necesita código de una PR abierta (#7 y #8). Pendiente de corregir en esos dos archivos, en un commit propio |
| **API de inventario (NXV-0201) pendiente** | Pospuesta el 04/11/2026 para hacer antes el analizador de incidencias. A 11/11/2026 **su enunciado todavía no está publicado** en la web del curso, que marca el orden de los proyectos: probablemente se ha movido más adelante. Su contexto está en `docs/contexts/` porque `sync_contexts.py` descarga todos. Se hará cuando salga |
| **Remitente de pruebas de Resend** | El email sale de `onboarding@resend.dev`, que solo entrega al email con el que se creó la cuenta de Resend. Para que llegue a cualquier persona de Nexova hace falta verificar un dominio propio en Resend (registros DNS) y cambiar `NEXOVA_API_EMAIL_FROM`, con una clave propia de ese entorno. Se hace al desplegar |
| **"El último análisis" en memoria** | `GET /api/incidents/results/export` exporta el último análisis del proceso: se pierde al reiniciar, es común a todos los usuarios y no funciona con varios workers. Solución prevista: un `analysis_id` en la respuesta del `POST`. Cambia el contrato del enunciado, así que se aplaza hasta que haya más de un usuario |
| **Pruebas automáticas de las rutas HTTP** | Resuelto con AUTH-01: [`tests/http_client.py`](../services/api/tests/http_client.py) prueba las rutas por ASGI, sin `httpx`. El frontend se prueba con scripts de Playwright fuera del repositorio: no hay pruebas automáticas del backoffice en la CI más allá de typecheck, lint y build |
| **Antigüedad de las incidencias abiertas** | Laura Mendoza quiere saber «cuánto tiempo llevan sin resolver». La lista muestra cuándo se registró cada una, pero el resumen no calcula antigüedades ni tiempos de resolución, porque el contrato de `/summary` del enunciado no los incluye. Es la siguiente mejora natural del gestor, junto a asignar responsable al pasar a «En curso» |
| **Dependencia de una API mock compartida** | Los datos los escriben también otros alumnos. Ninguna funcionalidad puede asumir que un registro concreto sigue existiendo. El backend propio **no la envuelve**: convivirán |
