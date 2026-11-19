# `api` — backend de Nexova

API de Nexova Solutions sobre **FastAPI**. Es un **monolito modular por dominios**: un solo servicio con un paquete por área de negocio. Su razonamiento está en [`docs/ARCHITECTURE_PROPOSAL.md`](../../docs/ARCHITECTURE_PROPOSAL.md) y las decisiones vigentes, en [`memory-bank/techContext.md`](../../memory-bank/techContext.md).

Hoy tiene dos dominios:

| Dominio | Qué hace | Rutas |
| --- | --- | --- |
| [`incidents`](./app/domains/incidents/) | Analiza la exportación CSV del helpdesk de soporte (Roberto Díaz). La validación y las métricas son las del paquete [`packages/shared/incident-analysis/`](../../packages/shared/incident-analysis/), las mismas que usa el script [`scripts/analyze.py`](../../scripts/analyze.py). También es el gestor de incidencias centralizado: alta, consulta con filtros, cambio de estado por el ciclo de vida y resumen | `POST /api/incidents/analyze` · `GET /api/incidents/results/export` · el gestor en `/api/incidents` (ver abajo) |
| [`suppliers`](./app/domains/suppliers/) | Directorio oficial de proveedores externos (Patricia Solís). Persistido en TinyDB, con las reglas del [BRIEFING](../../docs/contexts/proyectos/supplier-directory.es.md) | `/suppliers` (ver abajo) |

## Puesta en marcha

Python 3.11 o superior y [uv](https://docs.astral.sh/uv/). Desde esta carpeta:

```powershell
uv sync                                         # crea .venv e instala lo que fija uv.lock
Copy-Item .env.example .env                     # solo la primera vez: rellena el secreto
uv run --env-file .env uvicorn app.main:app --reload --port 8000
```

`uv run` ejecuta el comando dentro de `.venv` sin tener que activarlo, y `--env-file .env` carga antes las variables del `.env`. Sin `NEXOVA_API_JWT_SECRET_KEY` la API **no arranca**: no tendría con qué firmar los tokens. La documentación interactiva queda en http://localhost:8000/docs. Desde ahí se pueden probar todas las rutas sin el backoffice.

```powershell
uv run python -m unittest discover -s tests     # pruebas
uv run seed                                     # carga los proveedores del BRIEFING
uv run create-admin                             # crea el primer admin (o asciende una cuenta)
uv run python ../../scripts/seed_incidents.py   # carga en el gestor el histórico del CSV (96 incidencias)
```

`uv run seed` ([`app/seed.py`](./app/seed.py)) mete en la base de datos de TinyDB los 15 proveedores del [BRIEFING del directorio](../../docs/contexts/proyectos/supplier-directory.es.md). Se puede repetir sin miedo: salta los que ya están (por nombre) y dice cuántos ha insertado, cuántos ha saltado y cuántos hay en total. La base de datos es un fichero JSON en `storage/suppliers.json`. No se versiona: cada entorno crea la suya.

`uv run create-admin` ([`app/create_admin.py`](./app/create_admin.py)) pide un email. Si es nuevo, pide la contraseña dos veces sin mostrarla y crea una cuenta `admin` con su perfil vacío. Si el email ya tiene cuenta, la asciende a `admin` sin tocar su contraseña. Hace falta porque `POST /users` crea siempre cuentas `user` y solo un admin puede cambiar roles: sin el comando, el primer admin no podría existir. Aplica las mismas reglas que el alta por la API (email válido, contraseña de 8 caracteres a 72 bytes).

### Dependencias

Se declaran en [`pyproject.toml`](./pyproject.toml) y sus versiones exactas, incluidas las indirectas, quedan fijadas en [`uv.lock`](./uv.lock). Los dos se versionan: así todo el equipo instala exactamente lo mismo. Para añadir una, `uv add <paquete>`, que actualiza ambos. Añadir una dependencia es una decisión de arquitectura y se consulta antes (ver [`AGENTS.md`](../../AGENTS.md) §7).

El paquete compartido [`packages/shared/incident-analysis/`](../../packages/shared/incident-analysis/) se instala en modo editable (`[tool.uv.sources]`): un cambio en él se ve en la API sin reinstalar.

## Configuración

Se lee del entorno **una sola vez, al arrancar** ([`app/config.py`](./app/config.py)). Un valor inválido impide arrancar.

| Variable | Por defecto | Qué es |
| --- | --- | --- |
| `NEXOVA_API_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes que pueden llamar a la API desde el navegador, separados por comas. Nunca `*` |
| `NEXOVA_API_MAX_UPLOAD_MB` | `200` | Tamaño máximo del CSV subido. La exportación de producción puede llegar al millón de filas (~150 MB) |
| `NEXOVA_API_SUPPLIERS_DB_PATH` | `storage/suppliers.json` (dentro de esta carpeta) | Fichero de TinyDB del directorio de proveedores. La API y `uv run seed` leen la misma variable, así que siempre abren el mismo fichero |
| `NEXOVA_API_USERS_DB_PATH` | `storage/users.json` (dentro de esta carpeta) | Fichero de TinyDB de usuarios (solo credenciales) |
| `NEXOVA_API_PROFILES_DB_PATH` | `storage/profiles.json` (dentro de esta carpeta) | Fichero de TinyDB de perfiles (nombre y contacto) |
| `NEXOVA_API_INCIDENTS_DB_PATH` | `storage/incidents.json` (dentro de esta carpeta) | Fichero de TinyDB del gestor de incidencias: tabla `incidents` y tabla `seed_imports` (qué `ticket_id` del CSV ya se cargó) |
| `NEXOVA_API_JWT_SECRET_KEY` | — (obligatoria para arrancar) | **Secreta.** Clave con la que se firman los tokens. Al menos 32 caracteres. Va en `.env`, nunca en el código |
| `NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Minutos de validez de un token, de 1 a 1440 |
| `NEXOVA_API_RESEND_API_KEY` | — (opcional) | **Secreta.** API key de [Resend](https://resend.com), el servicio que envía el email de restablecimiento de contraseña. Va en `.env`, nunca en el código. Sin ella la API arranca y escribe el enlace en su log en vez de enviarlo |
| `NEXOVA_API_EMAIL_FROM` | `Nexova Solutions <onboarding@resend.dev>` | Remitente. El de pruebas de Resend no necesita dominio propio, pero solo entrega al email con el que se creó la cuenta de Resend |
| `NEXOVA_API_FRONTEND_URL` | `http://localhost:3000` | URL del backoffice. El email enlaza a `<URL>/reset-password?token=…` |
| `NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES` | `30` | Minutos de validez del enlace de restablecimiento, de 15 a 60 |
| `NEXOVA_API_RESET_REQUESTS_PER_HOUR` | `3` | Enlaces de restablecimiento por cuenta y hora, de 1 a 20. Las solicitudes de más reciben el mismo `200`, pero no envían email |
| `NEXOVA_API_PASSWORD_RESETS_DB_PATH` | `storage/password_resets.json` (dentro de esta carpeta) | Fichero de TinyDB de los tokens de restablecimiento y su registro de auditoría |

Los dos secretos (el del JWT y la API key de Resend) van en `.env`, que no se versiona. [`.env.example`](./.env.example) es la plantilla: lleva las variables, sin el valor, y el comando para generar uno. El seeder no necesita el secreto, porque no firma tokens. Las demás variables no son secretas y se pueden cambiar para una sesión con `$env:NEXOVA_API_MAX_UPLOAD_MB = "5"`.

## Estructura

```
app/
├─ main.py              compone la app: configuración, CORS y routers. Nada más
├─ errors.py            el 500 genérico: mensaje fijo para quien llama, el traceback al log
├─ config.py            configuración tipada, validada al arrancar
├─ dependencies.py      dependencias transversales (get_settings)
├─ mailer.py            envío de emails: Resend si hay API key, el log si no. El único que habla con Resend
├─ seed.py              `uv run seed`: carga los proveedores del BRIEFING
├─ create_admin.py      `uv run create-admin`: el primer admin
└─ domains/
   ├─ auth/             login y el candado de las rutas protegidas
   │  ├─ router.py      POST /auth/login y GET /auth/me
   │  ├─ dependencies.py  get_current_user: token → usuario de la base de datos, o 401
   │  ├─ security.py    firmar y verificar el JWT (HS256). El único módulo que importa jose
   │  ├─ schemas.py     Token y Me
   │  └─ exceptions.py
   ├─ password_resets/  restablecimiento y cambio de contraseña (AUTH-03): enlaces de un solo uso
   │  ├─ router.py      HTTP: /auth/forgot-password, /auth/reset-password y /auth/change-password
   │  ├─ service.py     tokens (aleatorios, 256 bits), auditoría y las tres operaciones: pedir enlace (con el límite por hora), restablecer, cambiar
   │  ├─ emails.py      el email del enlace: HTML con tablas y estilos en línea (legible en el móvil) y versión en texto
   │  ├─ schemas.py     ResetToken (se guarda el SHA-256, nunca el token), AuditEntry y los cuerpos de las tres rutas
   │  ├─ database.py    TinyDB, tablas tokens y audit. Marcar como usado, y contar y anotar para el límite, dentro del mismo cerrojo
   │  ├─ exceptions.py  InvalidResetTokenError (un solo mensaje, el motivo aparte), contraseña actual mal o repetida
   │  └─ dependencies.py  el repositorio de tokens, el mailer y la IP de quien llama
   ├─ incidents/        análisis del CSV y gestor de incidencias centralizado
   │  ├─ router.py      HTTP: el analizador (`router`) y el gestor (`manager`). Llama al service y elige el código
   │  ├─ service.py     reglas de la subida y el último análisis; alta, filtros, ciclo de vida y resumen del gestor. No importa fastapi
   │  ├─ schemas.py     Incident, IncidentCreate, StatusUpdate e IncidentSummary (valores del paquete compartido), el 400 del gestor y el contrato del análisis
   │  ├─ validation_errors.py  el 400 del gestor: traduce cada error de validación a campo, código y mensaje en español
   │  ├─ database.py    TinyDB, tablas incidents y seed_imports. Cambio de estado solo si nadie lo cambió antes
   │  ├─ seed.py        inserta el histórico del CSV; lo lanza scripts/seed_incidents.py
   │  ├─ exceptions.py  errores del dominio, sin HTTP
   │  └─ dependencies.py
   ├─ suppliers/
   │  ├─ router.py      HTTP: valida la entrada, llama al service, traduce errores a códigos
   │  ├─ service.py     reglas: quién pone updated_at, qué se puede borrar. No importa fastapi
   │  ├─ schemas.py     modelos Pydantic: entrada y salida separadas, reglas del BRIEFING
   │  ├─ database.py    TinyDB. El único módulo que la conoce
   │  ├─ exceptions.py  errores del dominio, sin HTTP
   │  ├─ dependencies.py
   │  └─ seed_data.py   los 15 proveedores del BRIEFING, copiados literalmente
   ├─ users/            cuentas: solo credenciales y rol
   │  ├─ router.py      HTTP: /users. Traduce los errores del service a 403, 404 y 409
   │  ├─ service.py     contraseñas (bcrypt), alta con perfil, permisos: tú mismo o admin
   │  ├─ schemas.py     UserCreate/UserUpdate (entrada), User (se guarda), UserPublic (sale, sin hash)
   │  ├─ database.py    TinyDB. Email único: se comprueba dentro del cerrojo de la escritura
   │  ├─ exceptions.py
   │  └─ dependencies.py
   └─ profiles/         nombre y contacto, uno por usuario (user_id)
      ├─ router.py      HTTP: /profiles/me. El perfil sale del token, nunca de la URL
      ├─ service.py     editar solo los campos enviados; null borra
      ├─ schemas.py
      ├─ database.py    TinyDB. Uno a uno: un segundo perfil del mismo usuario se rechaza
      ├─ exceptions.py
      └─ dependencies.py
storage/                base de datos de TinyDB (no se versiona)
tests/                  pruebas de los services, los modelos, la base de datos, los tokens, las rutas y la configuración
└─ http_client.py       cliente HTTP mínimo por ASGI para probar las rutas (hace de TestClient sin httpx)
```

## Rutas de `auth`

| Método y ruta | Qué hace | Respuestas |
| --- | --- | --- |
| `POST /auth/login` | Formulario OAuth2 (`application/x-www-form-urlencoded`): **el email va en `username`**, y `password`. Devuelve `{"access_token", "token_type": "bearer", "expires_in"}` (segundos) | `200` · `401` si el email o la contraseña no valen · `422` si falta un campo |
| `GET /auth/me` | Quién soy: `id`, `email`, `role` y el perfil | `200` · `401` |
| `POST /auth/forgot-password` | **Pública.** `{"email"}`. Si la cuenta existe y está activa, le manda un enlace que caduca en `NEXOVA_API_RESET_TOKEN_EXPIRE_MINUTES` (30 por defecto). Pedir otro anula el anterior. Como mucho `NEXOVA_API_RESET_REQUESTS_PER_HOUR` enlaces por cuenta y hora (3 por defecto) | `200` **siempre** con "Si esa dirección está registrada, recibirás un enlace en breve." · `422` si no es un email |
| `POST /auth/reset-password` | **Pública.** `{"token", "new_password"}`. El token es el del enlace | `200` · `400` si el enlace no existe, ha caducado o ya se usó (el mismo mensaje en los tres casos) · `422` si la contraseña no cumple las reglas |
| `POST /auth/change-password` | Con token. `{"current_password", "new_password"}`. Devuelve un token nuevo, como el login | `200` · `400` si la actual no es correcta o la nueva es igual · `401` · `422` |

Las rutas protegidas piden la cabecera `Authorization: Bearer <token>`. En `/docs`, el botón **Authorize** hace el login y la añade a cada petición: en *username* va el email. Sin token, o con uno caducado, manipulado o de una cuenta borrada o desactivada, la respuesta es `401` con la cabecera `WWW-Authenticate: Bearer`.

Para probar con curl en Windows (Git Bash), una contraseña con tildes o `ñ` puede llegar mal codificada y dar `401`. En `/docs` no pasa.

## Rutas de `users` y `profiles`

Todas piden token salvo el registro. Quién puede qué: **tu propia cuenta, o cualquiera si eres `admin`**.

| Método y ruta | Quién | Qué hace | Respuestas |
| --- | --- | --- | --- |
| `POST /users` | **Pública** | Registro: `email`, `password` y, opcionales, `name`, `phone` y `address`. Crea la cuenta (siempre `user`) y su perfil | `201` con la cuenta, el perfil y la cabecera `Location` · `409` email ya registrado · `422` (también si llega `role`) |
| `GET /users` | Solo admin | Lista las cuentas, sin hash | `200` · `401` · `403` |
| `GET /users/{id}` | Tú o admin | Una cuenta | `200` · `401` · `403` · `404` |
| `PUT /users/{id}` | Tú o admin | Cambia `email` o `password`; `role`, solo un admin. Solo cambia lo enviado | `200` · `401` · `403` · `404` · `409` · `422` |
| `DELETE /users/{id}` | Tú o admin | Borra la cuenta y su perfil | `204` · `401` · `403` · `404` |
| `GET /profiles/me` | Tú | Tu perfil | `200` · `401` |
| `PUT /profiles/me` | Tú | Cambia `name`, `phone` o `address`. Lo no enviado se queda; `null` lo borra | `200` · `401` · `422` |

El `404` solo lo ve un admin. A cualquier otro, una cuenta ajena le da `403` exista o no: el permiso se comprueba antes que la existencia.

## Rutas de `incidents`

Todas piden token (`Authorization: Bearer <token>`). Sin él, o con uno que no vale, `401` antes de leer la subida.

### `POST /api/incidents/analyze`

Subida `multipart/form-data` con el campo `file`. Devuelve el análisis en JSON (ver `AnalysisResponse` en `/docs`):

- totales;
- registros inválidos por regla;
- desglose por categoría y por estado, con porcentajes;
- satisfacción de los tickets `CLOSED`;
- hasta 50 filas inválidas de muestra, con su número de línea.

Los valores son **códigos** (`TECHNICAL`, `CLOSED`, `invalid_email`…). La traducción a texto de interfaz es cosa de cada aplicación.

| Código | Cuándo |
| --- | --- |
| `200` | Analizado. Pasa a ser el último análisis |
| `401` | Sin token, o token no válido o caducado |
| `400` | Vacío, solo la cabecera o faltan columnas obligatorias |
| `413` | Supera `NEXOVA_API_MAX_UPLOAD_MB` |
| `415` | No tiene extensión `.csv` o no está en UTF-8 |
| `422` | La petición no trae el campo `file` (lo genera FastAPI) |

Todos los errores tienen la forma `{"detail": "mensaje"}`, en español y listos para mostrar.

### `GET /api/incidents/results/export`

El último análisis como CSV descargable (`results.csv`, una métrica por fila). Es **byte a byte el mismo fichero** que escribe el script. Devuelve `404` si todavía no se ha analizado nada.

### Gestor de incidencias

Las incidencias que registra el equipo y el histórico del helpdesk (`scripts/seed_incidents.py`). Los valores de estado, categoría, origen y sede son **códigos** del paquete compartido (`open`, `sla_breach`, `remote`…).

| Ruta | Qué hace | Códigos |
| --- | --- | --- |
| `POST /api/incidents` | Registra una incidencia. Nace `open`, con `created_at` = `updated_at`. Cabecera `Location` con su URL | `201` · `400` |
| `GET /api/incidents` | Lista, la más reciente primero. Filtros opcionales y combinables: `?status=`, `?origin=`, `?branch=`, `?category=` (`?category=sla_breach` para las críticas). Sin incidencias, `[]` | `200` · `400` |
| `GET /api/incidents/summary` | Totales por estado, categoría, origen y sede. Salen **todos** los valores, en el orden del catálogo, también los que están a 0 | `200` |
| `GET /api/incidents/{id}` | Una incidencia por su UUID | `200` · `400` · `404` |
| `PATCH /api/incidents/{id}/status` | Cuerpo `{"status": "..."}`. Solo los cambios que permite el ciclo de vida (`ALLOWED_TRANSITIONS`) | `200` · `400` · `404` · `409` |

Y en todas, `401` sin token y `500` si algo falla de forma no prevista.

**El `400` dice qué campo falla.** Además del `detail`, trae la lista `errors` con un código estable por campo, para que el formulario lo traduzca a su idioma:

```json
{
  "detail": "El campo 'title' no puede estar vacío. El campo 'branch' es obligatorio.",
  "errors": [
    {"field": "title", "code": "blank", "message": "El campo 'title' no puede estar vacío."},
    {"field": "branch", "code": "missing", "message": "El campo 'branch' es obligatorio."}
  ]
}
```

| `code` | Cuándo |
| --- | --- |
| `missing` | Falta un campo obligatorio |
| `blank` | Texto vacío o solo espacios |
| `too_long` | Supera el máximo (título 120, descripción 2000) |
| `invalid_choice` | Un valor fuera del catálogo. El mensaje lista los válidos |
| `not_text` | Se esperaba texto |
| `not_allowed` | Un campo que no se puede enviar, como `status` o `id` en el alta |
| `invalid_id` | El `{id}` de la ruta no es un UUID |
| `invalid_body` | El cuerpo no es JSON o no es un objeto (`field: "body"`) |
| `invalid` | Cualquier otro |

**El `409` es un choque con el estado actual**, con `{"detail": "..."}`:

- el ciclo no permite el cambio: "Una incidencia en 'open' no puede pasar a 'resolved'. Desde 'open' solo se puede pasar a: in_progress, discarded.";
- ya estaba en ese estado, o está en un estado final;
- alguien la cambió entre la lectura y la escritura: "Vuelve a cargarla y decide con el estado actual."

**El `500` no enseña nada interno:** `{"detail": "Ha ocurrido un error inesperado en el servidor. Inténtalo de nuevo en unos minutos."}`. El traceback va al log (`nexova.errors`).

## Rutas de `suppliers`

Las rutas son las del enunciado, sin el prefijo `/api` de `incidents`. Antes de probarlas, `uv run seed`.

**Todas piden token.** Sin él, o con uno que no vale, cualquiera de ellas responde `401` y no toca nada. Con token se comportan igual que antes: cualquier cuenta activa puede usarlas, sea cual sea su rol.

| Método y ruta | Qué hace | Respuestas |
| --- | --- | --- |
| `POST /suppliers` | Da de alta un proveedor. `id` y `updated_at` los pone el sistema; si llegan en el cuerpo, se rechaza | `201` con el proveedor y la cabecera `Location` · `422` |
| `GET /suppliers?country=&category=` | Lista el directorio ordenado por nombre. Los dos filtros son opcionales y se combinan | `200` · `422` si un filtro no es un valor del BRIEFING |
| `GET /suppliers/{id}` | Un proveedor | `200` · `404` |
| `PATCH /suppliers/{id}/rate` | Cambia `monthly_rate` (`> 0`) y renueva `updated_at` | `200` · `404` · `422` |
| `PATCH /suppliers/{id}/status` | `active` o `suspended`. No toca `updated_at` | `200` · `404` · `422` |
| `DELETE /suppliers/{id}` | Borra un proveedor **activo** y lo devuelve | `200` · `404` · `409` si está suspendido |

Los `404` y `409` llevan `{"detail": "mensaje en español"}`. Los `422` son los de FastAPI: `detail` es una lista de errores por campo (`loc`, `msg`).

## Verificación manual en `/docs`

Con el servidor arrancado (el `uvicorn` de [Puesta en marcha](#puesta-en-marcha)), en <http://localhost:8000/docs>, con una cuenta de prueba (`user`, nunca un email real):

| # | Paso | Resultado esperado |
| --- | --- | --- |
| 1 | `GET /suppliers` sin haber pulsado *Authorize* | `401` "Falta el token. Inicia sesión en POST /auth/login." y la cabecera `www-authenticate: Bearer` |
| 2 | `POST /users` con email, contraseña y nombre | `201` con `role: "user"`, el perfil creado a la vez, la cabecera `location` y **sin** `hashed_password` |
| 3 | *Authorize*: el email en `username` y la contraseña | El candado de cada ruta se cierra |
| 4 | `GET /auth/me` | `200` con la cuenta y su perfil |
| 5 | `GET /suppliers` otra vez | `200` con el directorio, igual que antes del candado. El curl ya lleva `Authorization: Bearer …` |
| 6 | `GET /users` | `403` "No tienes permiso para esta operación.": la API sabe quién eres, pero solo un `admin` lista usuarios |
| 7 | `DELETE /users/{id}` con el propio `id` (opcional, para limpiar) | `204`, y el mismo token pasa a dar `401` |

`401` es "no sé quién eres"; `403`, "sé quién eres y no puedes". Los dos se ven en el recorrido.

Las capturas de los pasos 1, 2, 4, 5 y 6 van en la PR. El mismo recorrido, ampliado, se ejecutó también con un script contra el servidor real: 29 de 29 comprobaciones bien. Incluye, además de lo anterior:

- un email repetido (`409`);
- una contraseña mala (`401`);
- las 8 rutas de `incidents` (las del analizador) y `suppliers` sin token (`401`);
- un token caducado, uno manipulado y uno firmado con otro secreto (`401`);
- cinco `403` distintos: listar, ver, editar y borrar a otro, y hacerse admin;
- el admin cambiando un rol;
- `PUT /profiles/me`;
- el token de una cuenta borrada (`401`).

## Decisiones

- **La API no calcula.** Toda la validación y las métricas están en `incident_analysis`. Aquí solo se añade lo propio de recibir un fichero por la red: extensión, tamaño y la conversión de bytes a texto.
- **Se lee en streaming.** FastAPI guarda la subida en un fichero temporal, y el análisis lo lee línea a línea. La memoria no crece con el tamaño del CSV.
- **La extensión decide, no el `Content-Type`.** El navegador deduce el tipo del sistema operativo: en un Windows con Excel, un `.csv` viaja como `application/vnd.ms-excel`. Lo que se valida de verdad es el contenido, UTF-8 y columnas.
- **Rutas síncronas (`def`).** El análisis es cálculo y lectura bloqueante. FastAPI ejecuta las rutas síncronas en un pool de hilos, así que un fichero grande no congela las demás peticiones.
- **El email del cliente no sale.** Ni en la respuesta, ni en los errores, ni en el log del servidor. Hay una prueba que comprueba que la respuesta no contiene ninguna `@`.
- **Un análisis fallido no borra el anterior.** El último análisis solo se sustituye cuando el nuevo termina bien.
- **Un proveedor suspendido no se borra: `409`.** El BRIEFING dice que los suspendidos permanecen en el directorio para mantener el historial. La API lo hace cumplir aunque alguien la llame sin pasar por el backoffice. Un activo sí se borra, por ejemplo uno dado de alta por error.
- **Solo la tarifa mueve `updated_at`.** Patricia lo usa para justificar variaciones de presupuesto, y suspender no cambia el precio. Una tarifa repetida sí lo renueva: confirma ese precio en esa fecha.
- **`DELETE` devuelve `200` con el proveedor borrado**, no `204` sin cuerpo. Así el frontend puede decir qué ha borrado sin haberlo guardado antes.
- **La base de datos se abre al arrancar el servidor, no al importar** (`lifespan` en [`main.py`](./app/main.py)), y se cierra al pararlo. Crear la app para las pruebas o para leer el OpenAPI no toca el fichero.
- **El modelo `Incident` no define sus valores válidos.** Estados, categorías, orígenes y sedes son los `StrEnum` de [`incident_analysis.catalog`](../../packages/shared/incident-analysis/incident_analysis/catalog.py), los mismos que usa el seed. Toda incidencia nace `open` (`IncidentCreate` no acepta `status`), el título va de 1 a 120 caracteres, la descripción de 1 a 2000, las fechas llevan zona horaria y `updated_at` nunca es anterior a `created_at`.
- **El cambio de estado se escribe solo si nadie lo cambió antes** (`IncidentRepository.update_status`). Se pasa el estado que se leyó y, dentro del cerrojo, se comprueba que sigue siendo ese. Si dos personas pasan a la vez una incidencia `in_progress` a `resolved` y a `discarded`, la segunda no pisa a la primera sin saberlo.
- **El `400` del gestor solo cambia las rutas del gestor.** El enunciado pide `400` con el campo que falla; FastAPI da `422` con los mensajes de Pydantic en inglés. Se hace con una clase de ruta propia (`IncidentManagerRoute`, en [`validation_errors.py`](./app/domains/incidents/validation_errors.py)) y no con un manejador global: el analizador, proveedores y usuarios siguen con su `422`, que es el contrato que ya usa el backoffice. Por eso el gestor es un `APIRouter` aparte (`manager`) con el mismo prefijo.
- **Los errores del `400` llevan un `code` además del mensaje.** El mensaje en español es para quien lee la API; el formulario se guía por el código y escribe el suyo. Nunca se repite lo que escribió el usuario, salvo un valor corto de un desplegable (40 caracteres como mucho).
- **Un cambio de estado imposible es `409`, no `400`.** La petición está bien formada; lo que choca es el estado en que está la incidencia. Es lo mismo que hace proveedores al borrar un suspendido. Un cambio perdido por llegar segundo también es `409`, con otro mensaje.
- **El `500` es un middleware por dentro de CORS** ([`errors.py`](./app/errors.py)). Sin él, Starlette responde texto plano y por fuera de CORS: el navegador oculta la respuesta y el frontend ve un "Failed to fetch". Así sale el JSON de siempre, con las cabeceras de CORS, y el traceback solo en el log.
- **`/summary` devuelve los ceros.** Todos los estados, categorías, orígenes y sedes, aunque no tengan incidencias: el panel pinta siempre las mismas filas y una base vacía no rompe nada.
- **El `id` de un usuario es un UUID**, no el número de TinyDB. TinyDB reutiliza los números borrados, y el token de una cuenta eliminada identificaría a la siguiente que se registrase.
- **Quién puede hacer qué lo decide el service**, no el router ([`users/service.py`](./app/domains/users/service.py)). Cada uno ve, edita y borra su propia cuenta. Un `admin`, cualquiera, y es el único que lista usuarios y cambia roles. `manager` todavía no tiene permisos propios. La comprobación de permiso va antes que la de existencia: así quien no es admin no puede averiguar qué IDs existen.
- **El login no dice qué ha fallado.** Un email desconocido, una contraseña incorrecta y una cuenta desactivada dan la misma respuesta. Con un email desconocido se verifica igualmente contra un hash de relleno, para que tarde lo mismo y el tiempo de respuesta no delate qué emails tienen cuenta.
- **Alta en dos ficheros, sin transacciones.** `POST /users` crea primero la cuenta y luego el perfil. Si el perfil falla, se borra la cuenta recién creada. Al borrar va primero la cuenta: si el perfil fallase después, quedaría huérfano, pero no daría acceso a nada.

- **JWT sin estado, sin cookies.** El servidor no guarda sesiones: el token lleva su firma y su caducidad, y el cliente lo envía en cada petición. Cerrar sesión es tirar el token; hasta que caduque sigue valiendo, por eso la caducidad es corta (30 minutos por defecto, `NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES`).
- **El token solo lleva el `id` (`sub`) y las fechas, no el rol.** `get_current_user` lee el usuario de la base de datos en cada petición: un cambio de rol, una cuenta desactivada o borrada cuentan desde la petición siguiente, no cuando caduque el token. Cuesta una lectura de TinyDB por petición.
- **Solo se acepta HS256.** `algorithms=["HS256"]` al verificar rechaza los tokens sin firma (`alg: none`), el truco clásico para colar uno falso.
- **El campo del login se llama `username` aunque lleve un email.** Es el nombre que fija el estándar OAuth2, y respetarlo es lo que hace funcionar el botón *Authorize* de `/docs`.

- **`/profiles/me` y no `/profiles/{id}`.** El perfil sale del token, así que no hay forma de pedir el de otra persona: el `403` no hace falta porque no se puede ni intentar.
- **Borrar una cuenta devuelve `204` sin cuerpo**, y no `200` con lo borrado como los proveedores. Quien borra es casi siempre el dueño, que ya sabe qué cuenta era, y así no viajan otra vez sus datos.
- **El candado de `incidents` y `suppliers` va en el router, no en cada ruta.** `APIRouter(dependencies=[Depends(get_current_user)])` lo aplica a todas las rutas del módulo, y una ruta nueva nace protegida sin que nadie se acuerde. Ninguna de estas rutas decide nada según quién llama, así que no reciben el usuario como parámetro. En `users`, en cambio, va ruta a ruta: el registro es público y las demás sí necesitan saber quién eres.
- **Las rutas se prueban por HTTP sin `httpx`.** El `TestClient` de FastAPI lo necesita, y añadir una dependencia es una decisión aparte. [`tests/http_client.py`](./tests/http_client.py) habla con la app por ASGI, como uvicorn, en unas 40 líneas de biblioteca estándar: las pruebas ven los mismos códigos que vería el backoffice.

- **Resend sobre `urllib`, sin su SDK.** Enviar un email es una sola petición `POST https://api.resend.com/emails`, y no compensa una dependencia para eso. Hay que mandar un `User-Agent` propio: Resend está detrás de Cloudflare, que rechaza el de urllib con un `403`.
- **Sin API key, el email va al log.** `build_mailer` elige `LogMailer` y la API arranca igual: se puede desarrollar y probar el flujo entero copiando el enlace de la consola. En los logs el destinatario sale enmascarado (`d***@nexova.es`).
- **El HTML del email es de tablas y estilos en línea.** Gmail borra las etiquetas `<style>` y Outlook ignora el flexbox. Ancho máximo de 480 px, botón de 48 px de alto y el enlace también en texto, por si el cliente de correo no pinta el botón.
- **Prueba de envío real:** `uv run --env-file .env python -m app.mailer <tu-email>`. Con el remitente de pruebas (`onboarding@resend.dev`) solo llega al email con el que se creó la cuenta de Resend.
- **Una API key de Resend por entorno, con el mínimo permiso.** La de desarrollo se llama `nexova-api-local` y tiene permiso *Sending access*: puede enviar emails y nada más (listar los dominios le da `401 restricted_api_key`). Si se filtrara, no serviría para cambiar la cuenta, y se revoca sin tocar la de otro entorno. Producción tendrá la suya, con su propio dominio verificado. La clave que Resend crea al dar de alta la cuenta tiene acceso completo: se borra.
- **Los logs de la API (`nexova.*`) salen en la consola desde el nivel `INFO`** (`configure_logging` en [`main.py`](./app/main.py)). Uvicorn solo configura sus propios loggers, y sin esto se veía cuándo fallaba un envío, pero no cuándo salía bien. Ante un «no me llega el correo», `Email enviado a d***@…` dice si salió de la API; la auditoría dice por qué no, si no salió (`unknown_account`, `rate_limited`, `delivery_failed`).
- **`forgot-password` no delata qué emails tienen cuenta, ni por el texto ni por el tiempo.** La respuesta sale antes de buscar al usuario: la búsqueda, el token y el envío van en una tarea en segundo plano (`BackgroundTasks`). Si Resend falla, se anota en el log y la respuesta sigue siendo `200`; la persona puede pedirlo otra vez.
- **Cambiar la contraseña cierra las demás sesiones.** El usuario guarda `password_changed_at`, y `get_current_user` rechaza los tokens con un `iat` anterior. Quien cambia la contraseña porque sospecha que alguien entró, lo echa. Vale para las tres vías: el enlace del email, `change-password` y `PUT /users/{id}`. Como `iat` va en segundos enteros, se compara con el segundo del cambio redondeado hacia abajo: el token que se emite en el mismo segundo sigue valiendo.
- **`change-password` devuelve un token nuevo.** El anterior deja de valer por la regla de arriba; el backoffice guarda el nuevo y la sesión de quien cambia sigue abierta. También borra los enlaces de restablecimiento pendientes.
- **Una cuenta desactivada no recibe enlace**, y un enlace de una cuenta borrada o desactivada después de pedirlo da `400`, el mismo de un enlace inválido.
- **El límite de `forgot-password` es por cuenta, y no se nota en la respuesta.** Como mucho 3 enlaces por cuenta en la última hora (ventana deslizante); la cuarta solicitud recibe el mismo `200` y no sale email. Es por cuenta y no por email porque solo hay buzón que inundar si la cuenta existe: a un email sin cuenta nunca se le envía nada. Solo cuentan los enlaces emitidos, no las solicitudes rechazadas, así que insistir no alarga el bloqueo. Responder `429` delataría qué emails están registrados.
- **El registro de auditoría hace también de contador del límite.** Cada `reset_link_issued` de la última hora es un enlace enviado. Contar y anotar ocurren dentro del mismo cerrojo: dos solicitudes a la vez no pueden pasar las dos con "2 de 3".
- **Qué guarda la auditoría** (tabla `audit` de `storage/password_resets.json`): una entrada por solicitud a las tres rutas, con la fecha, el evento, la IP, el `user_id` y el motivo si falló (`unknown_account`, `inactive_account`, `rate_limited`, `delivery_failed`, `used`, `expired`, `unknown`, `account_unavailable`, `wrong_current_password`, `same_password`). Un `422` no llega a la ruta y no deja entrada. Decidido con Diego el 18/11/2026, porque son datos de personas:
  - **La cuenta va por `user_id`, nunca por el email.** Un email sin cuenta no se guarda: no acumulamos direcciones de terceros.
  - **La IP va completa.** Es lo que sirve para ver un ataque desde una misma dirección.
  - **Las entradas se borran a los 90 días**, cada vez que se escribe una nueva.

## Limitaciones conocidas

- **"El último análisis" vive en la memoria del proceso.** El contrato de `GET /results/export` no dice qué análisis exportar, así que el servidor tiene que recordarlo. Eso implica tres cosas:
  1. Se pierde al reiniciar.
  2. Es común a todos los usuarios: si dos personas analizan a la vez, cada una puede descargar el resultado de la otra. Hoy solo contiene cifras agregadas, sin datos personales.
  3. No funciona con varios procesos (`--workers`), porque cada uno tiene su memoria.

  La solución de producción es que el `POST` devuelva un `analysis_id` y que la exportación lo reciba. Cambia el contrato, así que queda para cuando haya más de un usuario.
- **El límite de tamaño se comprueba después de recibir el fichero.** Protege el análisis, pero no la red. En producción el límite también va en el proxy (`client_max_body_size` en nginx).
- **TinyDB puede reutilizar un ID borrado.** Calcula el siguiente ID como el mayor que existe más uno. Si se borra el último proveedor y se reinicia el servidor, el siguiente que se cree recibe su ID, y un enlace antiguo abriría otro proveedor. Postgres, con secuencias, no tiene este problema.
- **Si se borra un proveedor del BRIEFING, `uv run seed` lo vuelve a crear.** El seeder decide por nombre qué falta y no puede distinguir un proveedor borrado a propósito de uno que nunca se cargó.
- **La IP de la auditoría es la de quien abre la conexión.** Detrás de un proxy o un balanceador sería la del proxy. No se lee `X-Forwarded-For` porque, sin un proxy de confianza delante, cualquiera puede escribir ahí la IP que quiera. Al desplegar detrás de uno, se arranca uvicorn con `--proxy-headers --forwarded-allow-ips <IP del proxy>`.
- **Cambiar la contraseña con `PUT /users/{id}` no queda en la auditoría.** Solo se auditan las tres rutas de AUTH-03. `PUT /users/{id}` es la gestión de cuentas de AUTH-01 (la propia persona o un admin) y queda fuera del ticket.
- **La purga de 90 días solo ocurre al escribir.** Si nadie usa las tres rutas en meses, las entradas viejas siguen en el fichero hasta la siguiente solicitud.
- **`/docs` sigue anunciando un `422` en las rutas del gestor, que nunca sale.** FastAPI lo añade a toda ruta con parámetros, y la clase de ruta lo convierte en `400` antes de responder. Quitarlo del OpenAPI obliga a reescribir el esquema generado; no compensa para una línea de documentación.
- **Todas las cuentas tienen los mismos permisos sobre proveedores e incidencias.** El candado pide estar identificado, no un rol. Dar o quitar permisos por rol (que solo un `manager` cambie tarifas, por ejemplo) es una decisión de negocio que el enunciado no fija.
