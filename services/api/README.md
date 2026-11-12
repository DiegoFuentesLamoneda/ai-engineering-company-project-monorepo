# `api` — backend de Nexova

API de Nexova Solutions sobre **FastAPI**. Es un **monolito modular por dominios**: un solo servicio con un paquete por área de negocio. Su razonamiento está en [`docs/ARCHITECTURE_PROPOSAL.md`](../../docs/ARCHITECTURE_PROPOSAL.md) y las decisiones vigentes, en [`memory-bank/techContext.md`](../../memory-bank/techContext.md).

Hoy tiene dos dominios:

| Dominio | Qué hace | Rutas |
| --- | --- | --- |
| [`incidents`](./app/domains/incidents/) | Analiza la exportación CSV del helpdesk de soporte (Roberto Díaz). La validación y las métricas son las del paquete [`packages/incident-analysis/`](../../packages/incident-analysis/), las mismas que usa el script [`scripts/analyze.py`](../../scripts/analyze.py) | `POST /api/incidents/analyze` · `GET /api/incidents/results/export` |
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
```

`uv run seed` ([`app/seed.py`](./app/seed.py)) mete en la base de datos de TinyDB los 15 proveedores del [BRIEFING del directorio](../../docs/contexts/proyectos/supplier-directory.es.md). Se puede repetir sin miedo: salta los que ya están (por nombre) y dice cuántos ha insertado, cuántos ha saltado y cuántos hay en total. La base de datos es un fichero JSON en `storage/suppliers.json`. No se versiona: cada entorno crea la suya.

`uv run create-admin` ([`app/create_admin.py`](./app/create_admin.py)) pide un email. Si es nuevo, pide la contraseña dos veces sin mostrarla y crea una cuenta `admin` con su perfil vacío. Si el email ya tiene cuenta, la asciende a `admin` sin tocar su contraseña. Hace falta porque `POST /users` crea siempre cuentas `user` y solo un admin puede cambiar roles: sin el comando, el primer admin no podría existir. Aplica las mismas reglas que el alta por la API (email válido, contraseña de 8 caracteres a 72 bytes).

### Dependencias

Se declaran en [`pyproject.toml`](./pyproject.toml) y sus versiones exactas, incluidas las indirectas, quedan fijadas en [`uv.lock`](./uv.lock). Los dos se versionan: así todo el equipo instala exactamente lo mismo. Para añadir una, `uv add <paquete>`, que actualiza ambos. Añadir una dependencia es una decisión de arquitectura y se consulta antes (ver [`AGENTS.md`](../../AGENTS.md) §7).

El paquete compartido [`packages/incident-analysis/`](../../packages/incident-analysis/) se instala en modo editable (`[tool.uv.sources]`): un cambio en él se ve en la API sin reinstalar.

## Configuración

Se lee del entorno **una sola vez, al arrancar** ([`app/config.py`](./app/config.py)). Un valor inválido impide arrancar.

| Variable | Por defecto | Qué es |
| --- | --- | --- |
| `NEXOVA_API_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Orígenes que pueden llamar a la API desde el navegador, separados por comas. Nunca `*` |
| `NEXOVA_API_MAX_UPLOAD_MB` | `200` | Tamaño máximo del CSV subido. La exportación de producción puede llegar al millón de filas (~150 MB) |
| `NEXOVA_API_SUPPLIERS_DB_PATH` | `storage/suppliers.json` (dentro de esta carpeta) | Fichero de TinyDB del directorio de proveedores. La API y `uv run seed` leen la misma variable, así que siempre abren el mismo fichero |
| `NEXOVA_API_USERS_DB_PATH` | `storage/users.json` (dentro de esta carpeta) | Fichero de TinyDB de usuarios (solo credenciales) |
| `NEXOVA_API_PROFILES_DB_PATH` | `storage/profiles.json` (dentro de esta carpeta) | Fichero de TinyDB de perfiles (nombre y contacto) |
| `NEXOVA_API_JWT_SECRET_KEY` | — (obligatoria para arrancar) | **Secreta.** Clave con la que se firman los tokens. Al menos 32 caracteres. Va en `.env`, nunca en el código |
| `NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Minutos de validez de un token, de 1 a 1440 |

El secreto va en `.env`, que no se versiona. [`.env.example`](./.env.example) es la plantilla: lleva las variables, sin el valor, y el comando para generar uno. El seeder no necesita el secreto, porque no firma tokens. Las demás variables no son secretas y se pueden cambiar para una sesión con `$env:NEXOVA_API_MAX_UPLOAD_MB = "5"`.

## Estructura

```
app/
├─ main.py              compone la app: configuración, CORS y routers. Nada más
├─ config.py            configuración tipada, validada al arrancar
├─ dependencies.py      dependencias transversales (get_settings)
├─ seed.py              `uv run seed`: carga los proveedores del BRIEFING
├─ create_admin.py      `uv run create-admin`: el primer admin
└─ domains/
   ├─ auth/             login y el candado de las rutas protegidas
   │  ├─ router.py      POST /auth/login y GET /auth/me
   │  ├─ dependencies.py  get_current_user: token → usuario de la base de datos, o 401
   │  ├─ security.py    firmar y verificar el JWT (HS256). El único módulo que importa jose
   │  ├─ schemas.py     Token y Me
   │  └─ exceptions.py
   ├─ incidents/
   │  ├─ router.py      HTTP: recibe la subida, llama al service, elige el código
   │  ├─ service.py     reglas de la subida y el último análisis. No importa fastapi
   │  ├─ schemas.py     contrato de salida (lo que publica /docs)
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
   │  ├─ service.py     contraseñas (bcrypt), alta con perfil, permisos: tú mismo o admin
   │  ├─ schemas.py     UserCreate/UserUpdate (entrada), User (se guarda), UserPublic (sale, sin hash)
   │  ├─ database.py    TinyDB. Email único: se comprueba dentro del cerrojo de la escritura
   │  ├─ exceptions.py
   │  └─ dependencies.py
   └─ profiles/         nombre y contacto, uno por usuario (user_id)
      ├─ service.py     editar solo los campos enviados; null borra
      ├─ schemas.py
      ├─ database.py    TinyDB. Uno a uno: un segundo perfil del mismo usuario se rechaza
      ├─ exceptions.py
      └─ dependencies.py
storage/                base de datos de TinyDB (no se versiona)
tests/                  pruebas de los services, los modelos, la base de datos, los tokens y la configuración
```

## Rutas de `auth`

| Método y ruta | Qué hace | Respuestas |
| --- | --- | --- |
| `POST /auth/login` | Formulario OAuth2 (`application/x-www-form-urlencoded`): **el email va en `username`**, y `password`. Devuelve `{"access_token", "token_type": "bearer", "expires_in"}` (segundos) | `200` · `401` si el email o la contraseña no valen · `422` si falta un campo |
| `GET /auth/me` | Quién soy: `id`, `email`, `role` y el perfil | `200` · `401` |

Las rutas protegidas piden la cabecera `Authorization: Bearer <token>`. En `/docs`, el botón **Authorize** hace el login y la añade a cada petición: en *username* va el email. Sin token, o con uno caducado, manipulado o de una cuenta borrada o desactivada, la respuesta es `401` con la cabecera `WWW-Authenticate: Bearer`.

Para probar con curl en Windows (Git Bash), una contraseña con tildes o `ñ` puede llegar mal codificada y dar `401`. En `/docs` no pasa.

## Rutas de `incidents`

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
| `400` | Vacío, solo la cabecera o faltan columnas obligatorias |
| `413` | Supera `NEXOVA_API_MAX_UPLOAD_MB` |
| `415` | No tiene extensión `.csv` o no está en UTF-8 |
| `422` | La petición no trae el campo `file` (lo genera FastAPI) |

Todos los errores tienen la forma `{"detail": "mensaje"}`, en español y listos para mostrar.

### `GET /api/incidents/results/export`

El último análisis como CSV descargable (`results.csv`, una métrica por fila). Es **byte a byte el mismo fichero** que escribe el script. Devuelve `404` si todavía no se ha analizado nada.

## Rutas de `suppliers`

Las rutas son las del enunciado, sin el prefijo `/api` de `incidents`. Antes de probarlas, `uv run seed`.

| Método y ruta | Qué hace | Respuestas |
| --- | --- | --- |
| `POST /suppliers` | Da de alta un proveedor. `id` y `updated_at` los pone el sistema; si llegan en el cuerpo, se rechaza | `201` con el proveedor y la cabecera `Location` · `422` |
| `GET /suppliers?country=&category=` | Lista el directorio ordenado por nombre. Los dos filtros son opcionales y se combinan | `200` · `422` si un filtro no es un valor del BRIEFING |
| `GET /suppliers/{id}` | Un proveedor | `200` · `404` |
| `PATCH /suppliers/{id}/rate` | Cambia `monthly_rate` (`> 0`) y renueva `updated_at` | `200` · `404` · `422` |
| `PATCH /suppliers/{id}/status` | `active` o `suspended`. No toca `updated_at` | `200` · `404` · `422` |
| `DELETE /suppliers/{id}` | Borra un proveedor **activo** y lo devuelve | `200` · `404` · `409` si está suspendido |

Los `404` y `409` llevan `{"detail": "mensaje en español"}`. Los `422` son los de FastAPI: `detail` es una lista de errores por campo (`loc`, `msg`).

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
- **El `id` de un usuario es un UUID**, no el número de TinyDB. TinyDB reutiliza los números borrados, y el token de una cuenta eliminada identificaría a la siguiente que se registrase.
- **Quién puede hacer qué lo decide el service**, no el router ([`users/service.py`](./app/domains/users/service.py)). Cada uno ve, edita y borra su propia cuenta. Un `admin`, cualquiera, y es el único que lista usuarios y cambia roles. `manager` todavía no tiene permisos propios. La comprobación de permiso va antes que la de existencia: así quien no es admin no puede averiguar qué IDs existen.
- **El login no dice qué ha fallado.** Un email desconocido, una contraseña incorrecta y una cuenta desactivada dan la misma respuesta. Con un email desconocido se verifica igualmente contra un hash de relleno, para que tarde lo mismo y el tiempo de respuesta no delate qué emails tienen cuenta.
- **Alta en dos ficheros, sin transacciones.** `POST /users` crea primero la cuenta y luego el perfil. Si el perfil falla, se borra la cuenta recién creada. Al borrar va primero la cuenta: si el perfil fallase después, quedaría huérfano, pero no daría acceso a nada.

- **JWT sin estado, sin cookies.** El servidor no guarda sesiones: el token lleva su firma y su caducidad, y el cliente lo envía en cada petición. Cerrar sesión es tirar el token; hasta que caduque sigue valiendo, por eso la caducidad es corta (30 minutos por defecto, `NEXOVA_API_ACCESS_TOKEN_EXPIRE_MINUTES`).
- **El token solo lleva el `id` (`sub`) y las fechas, no el rol.** `get_current_user` lee el usuario de la base de datos en cada petición: un cambio de rol, una cuenta desactivada o borrada cuentan desde la petición siguiente, no cuando caduque el token. Cuesta una lectura de TinyDB por petición.
- **Solo se acepta HS256.** `algorithms=["HS256"]` al verificar rechaza los tokens sin firma (`alg: none`), el truco clásico para colar uno falso.
- **El campo del login se llama `username` aunque lleve un email.** Es el nombre que fija el estándar OAuth2, y respetarlo es lo que hace funcionar el botón *Authorize* de `/docs`.

## Limitaciones conocidas

- **"El último análisis" vive en la memoria del proceso.** El contrato de `GET /results/export` no dice qué análisis exportar, así que el servidor tiene que recordarlo. Eso implica tres cosas:
  1. Se pierde al reiniciar.
  2. Es común a todos los usuarios: si dos personas analizan a la vez, cada una puede descargar el resultado de la otra. Hoy solo contiene cifras agregadas, sin datos personales.
  3. No funciona con varios procesos (`--workers`), porque cada uno tiene su memoria.

  La solución de producción es que el `POST` devuelva un `analysis_id` y que la exportación lo reciba. Cambia el contrato, así que queda para cuando haya más de un usuario.
- **El límite de tamaño se comprueba después de recibir el fichero.** Protege el análisis, pero no la red. En producción el límite también va en el proxy (`client_max_body_size` en nginx).
- **TinyDB puede reutilizar un ID borrado.** Calcula el siguiente ID como el mayor que existe más uno. Si se borra el último proveedor y se reinicia el servidor, el siguiente que se cree recibe su ID, y un enlace antiguo abriría otro proveedor. Postgres, con secuencias, no tiene este problema.
- **Si se borra un proveedor del BRIEFING, `uv run seed` lo vuelve a crear.** El seeder decide por nombre qué falta y no puede distinguir un proveedor borrado a propósito de uno que nunca se cargó.
- **Las rutas se prueban a mano**, con el servidor arrancado. Las pruebas automáticas del router necesitan el cliente de pruebas de FastAPI, y este depende de `httpx`, que todavía no es una dependencia aprobada.
