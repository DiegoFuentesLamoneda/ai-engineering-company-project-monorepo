# Auditoría de gestión de errores

Ticket del tech lead: el sistema no tiene una estrategia coherente de gestión de errores. Rama `feature/error-handling-audit`, apilada sobre `feature/incident-manager` para auditar todo lo construido hasta hoy.

Auditoría hecha el 20/11/2026 con tres revisores de código en paralelo (backoffice, API, scripts y webs estáticas), con el prompt de detección del enunciado. Los hallazgos de severidad alta se comprobaron después a mano contra el código.

**Alcance:** solo resiliencia y comunicación de errores del código que ya existe. Nada de funcionalidades nuevas ni refactorizaciones ajenas. Lo que queda fuera se apunta al final, con el motivo.

Estado: ✅ corregido · ⬜ pendiente · ➖ se deja como está (con el motivo)

## Backend — `services/api/`

| ID | Severidad | Dónde | Problema | Corrección | Estado |
| --- | --- | --- | --- | --- | --- |
| B1 | Alta | Toda la API salvo el gestor de incidencias | El `422` por defecto de FastAPI devuelve el campo `input` de cada error: una contraseña corta en `POST /users`, `/auth/reset-password` o `/auth/change-password` vuelve en la respuesta, y con ella el token de restablecimiento | Manejador de `RequestValidationError` que deja solo `loc`, `msg` y `type`. Mantiene la forma de lista que lee el backoffice | ✅ `validation_error_handler` en [`errors.py`](../services/api/app/errors.py) |
| B2 | Media | [`config.py`](../services/api/app/config.py) | Si un valor de configuración no valida (un secreto JWT demasiado corto), el error de Pydantic imprime el valor recibido en la consola al arrancar | `hide_input_in_errors` en la configuración | ✅ |
| B3 | Media | [`mailer.py:114-118`](../services/api/app/mailer.py) | Solo captura `HTTPError`, `URLError` y `TimeoutError`. Un corte a mitad de respuesta (`RemoteDisconnected`, `ConnectionResetError`) se escapa sin traducir | Capturar también `OSError` y `http.client.HTTPException` como `EmailDeliveryError` | ✅ |
| B4 | Media | [`password_resets/service.py`](../services/api/app/domains/password_resets/service.py) (tarea en segundo plano) | Un fallo distinto del envío dentro de la tarea de `forgot-password` llega después del `200` y no deja rastro en la auditoría | Registrar el fallo con `logger.exception` en el ámbito de la tarea | ➖ Ya queda en el log: la excepción de la tarea sube por `UnexpectedErrorMiddleware`, que la registra entera antes de relanzarla. Un `try` más sería un segundo registro del mismo fallo |
| B5 | Media | [`password_resets/router.py`](../services/api/app/domains/password_resets/router.py) | Si la cuenta se borra entre pedir el enlace y usarlo, `UserNotFoundError` acaba en `500` en vez del `400` de enlace no válido | Traducirlo al mismo `400` | ➖ No ocurre: `reset_password` comprueba que la cuenta existe y está activa antes de cambiar la contraseña, y si no, da el `400` de enlace no válido (y lo anota en la auditoría). Solo queda una carrera de microsegundos entre esa lectura y la escritura |
| B6 | Media | Repositorios TinyDB (`domains/*/database.py`) | Un fichero JSON corrupto o sin permisos da un `500` genérico. El mensaje es limpio, pero «error del servidor» no le dice a nadie que es el almacenamiento | `503` con «El servicio no está disponible» para `OSError` y JSON corrupto, registrado en el log | ✅ [`json_storage.py`](../services/api/app/json_storage.py): el almacenamiento de los cinco repositorios traduce el fallo en la única operación que toca el disco |
| B7 | Baja | [`mailer.py`](../services/api/app/mailer.py) | El cuerpo de la respuesta de Resend (hasta 300 caracteres) va al log y puede llevar el email de la cuenta | Registrar solo el código de estado | ✅ El código y el `name` de Resend (`validation_error`), nunca su mensaje |

**Ya estaba bien:** el `500` sale siempre en JSON con un mensaje genérico y las cabeceras de CORS ([`errors.py`](../services/api/app/errors.py)); ninguna respuesta lleva trazas ni `str(exc)`; JWT, contraseñas y CSV con excepciones concretas; la clave de Resend nunca aparece en mensajes; `forgot-password` responde siempre igual.

## Frontend — `uis/backoffice/`

| ID | Severidad | Dónde | Problema | Corrección | Estado |
| --- | --- | --- | --- | --- | --- |
| F1 | Crítica | [`app/`](../uis/backoffice/app/) | No hay `error.tsx`, `global-error.tsx` ni `not-found.tsx`. Un error al pintar deja la pantalla de error de Next o una página en blanco, y una URL que no existe, el 404 en inglés de Next | Las tres páginas, en español, con «Reintentar» y enlace al panel | ✅ [`error.tsx`](../uis/backoffice/app/error.tsx), [`global-error.tsx`](../uis/backoffice/app/global-error.tsx) y [`not-found.tsx`](../uis/backoffice/app/not-found.tsx). Sin `error.message`, que en el navegador es el texto técnico; solo el `digest` como referencia. Comprobado: `/esto-no-existe` responde `404` con la página en español |
| F2 | Alta | [`SessionMenu.tsx:43`](../uis/backoffice/components/SessionMenu.tsx) | `me?.profile.name` falla si `profile` llega vacío, y el menú está en todas las vistas protegidas | `me?.profile?.name` | ✅ Sin perfil, el menú enseña el email |
| F3 | Alta | [`lib/api.ts:252`](../uis/backoffice/lib/api.ts) | `res.json()` de una respuesta 2xx sin proteger: un cuerpo HTML o vacío lanza `SyntaxError: Unexpected token <` | Capturarlo y lanzar un `ApiError` legible | ✅ Un cuerpo que no se puede leer lanza «El servidor ha enviado una respuesta que no se puede leer» |
| F4 | Alta | [`useCandidates.ts:38`](../uis/backoffice/hooks/useCandidates.ts), [`lib/api.ts:322`](../uis/backoffice/lib/api.ts) | Los candidatos y las notas vienen de la API mock compartida. Si falta `data`, `.length` y `.map` rompen la vista | `?? []` y `?? 0` | ✅ En `useCandidates` y en `getNotes`: sin sobre, lista vacía y total `0` |
| F5 | Alta | [`CandidateList`](../uis/backoffice/components/CandidateList.tsx), [`PipelineSummary`](../uis/backoffice/components/PipelineSummary.tsx), [`SupplierList`](../uis/backoffice/components/SupplierList.tsx), [`CandidateNotes`](../uis/backoffice/components/CandidateNotes.tsx), [`ProfileForm`](../uis/backoffice/components/ProfileForm.tsx) | Estados de error sin salida: ni reintentar ni enlace | Botón «Reintentar», como ya tienen la lista y el resumen de incidencias | ✅ Los hooks `useCandidates`, `useSuppliers` y `useNotes` devuelven `recargar`, con el mismo patrón que `useIncidents`; el perfil vuelve a pedir `getMe`. Los cinco bloques llevan `role="alert"` |
| F6 | Media | [`lib/api.ts:115-178`](../uis/backoffice/lib/api.ts) | Sin texto para `403`, `429`, `502`, `503` y `504`: salen como «Error inesperado (429).», con el código. El `401` de rutas que no son el login dice «Email o contraseña incorrectos» | Textos para esos códigos y ningún número en el mensaje | ✅ Textos para `403`, `429`, `502`, `503` y `504`; el resto, «Algo ha fallado. Inténtalo de nuevo.». El `401` por defecto ya no habla de credenciales: el del login trae su propio mensaje de la API |
| F7 | Media | [`lib/api.ts:193`](../uis/backoffice/lib/api.ts), [`SupplierList.tsx:30-32`](../uis/backoffice/components/SupplierList.tsx) | Texto para desarrolladores en la interfaz: «Falta la variable NEXT_PUBLIC_… en .env.local», «¿Está arrancada la API? Ver services/api/README.md» | Mensaje para el usuario en pantalla; el detalle técnico, a la consola solo en desarrollo | ✅ En pantalla, «El servicio no está disponible ahora mismo…»; el nombre de la variable, a la consola solo con `NODE_ENV=development`. Fuera la pista de `services/api/README.md` |
| F8 | Media | [`CandidateForm.tsx:197-203`](../uis/backoffice/components/CandidateForm.tsx) | Muestra tal cual los mensajes de la API mock, de terceros y sin traducir | Mensaje propio, como el resto de formularios | ✅ Un `422` marca cada campo con un texto en español y «Revisa los campos marcados»; sin red, el mensaje de `lib/api.ts`; cualquier otro, «No se ha podido guardar la candidatura» |
| F9 | Media | [`IncidentSummaryPanel`](../uis/backoffice/components/IncidentSummaryPanel.tsx), [`IncidentResults`](../uis/backoffice/components/IncidentResults.tsx), [`useIncidents`](../uis/backoffice/hooks/useIncidents.ts), [`useSuppliers`](../uis/backoffice/hooks/useSuppliers.ts), listas y detalle de candidatos | Propiedades anidadas y etiquetas sin `?.` ni valor por defecto: una clave que falta pinta `undefined` o rompe | `?.`, `?? 0`, `?? []` y `?? "—"` | ✅ Las cifras que faltan salen a `0`, las listas vacías y los textos como «—». Una etiqueta que no está en el diccionario enseña el valor tal cual en vez de dejar el hueco |
| F10 | Media | [`LoginForm`](../uis/backoffice/components/LoginForm.tsx), [`RegisterForm`](../uis/backoffice/components/RegisterForm.tsx), [`ResetPasswordForm`](../uis/backoffice/components/ResetPasswordForm.tsx) | El estado de envío se limpia solo en el `catch`. Si la redirección no llega, el botón se queda en «Entrando…» | `finally` | ✅ El `finally` reactiva el botón siempre que el envío no ha salido bien. Si sale bien, sigue desactivado hasta que llega la redirección, para no enviar dos veces |
| F11 | Baja | [`SessionMenu.tsx:28`](../uis/backoffice/components/SessionMenu.tsx) | `.catch(() => {})`: si falla `getMe` por algo que no es un `401`, no queda rastro | Etiqueta de reserva en el menú | ✅ Si `getMe` falla, el menú enseña un enlace «Mi cuenta» junto a «Cerrar sesión» |
| F12 | Baja | [`lib/session.ts:56,62`](../uis/backoffice/lib/session.ts) | `setItem` puede lanzar con el almacenamiento lleno o bloqueado | `try/catch` acotado a esa llamada | ✅ Si `setItem` falla, el login enseña su mensaje genérico en vez de una sesión a medias; si falla `removeItem`, la sesión se da por cerrada igualmente |

**Ya estaba bien:** todo `fetch` pasa por [`lib/api.ts`](../uis/backoffice/lib/api.ts), que traduce los fallos de red y los cuerpos que no son JSON; todos los hooks de carga tienen cargando, error, cancelación y `finally`; la lista y el resumen de incidencias ya tienen «Reintentar»; ni un `console.*` en el backoffice.

## Scripts — `scripts/` y comandos de la API

| ID | Severidad | Dónde | Problema | Corrección | Estado |
| --- | --- | --- | --- | --- | --- |
| S1 | Alta | [`sync_contexts.py:196-210`](../scripts/sync_contexts.py) | Termina con `0` y «Listo» aunque fallen todas las descargas. `mkdir` y `write_bytes` fuera del `try`, y un `TimeoutError` o JSON roto de GitHub salen como traza | Contar fallos, `stderr` y salir con `1`; capturar escritura, tiempo de espera y JSON | ✅ Cinco casos probados con GitHub simulado |
| S2 | Alta | [`app/seed.py`](../services/api/app/seed.py) | Sin ningún `try`: configuración, TinyDB o un dato que no valida acaban en traza, sin código de salida explícito | `try/except` por operación, `stderr` y `sys.exit(1)` | ✅ Probado en `tests/test_cli_errors.py` |
| S3 | Media | [`analyze.py:60-72`](../scripts/analyze.py), [`seed_incidents.py:84-92`](../scripts/seed_incidents.py) | Solo capturan los errores del CSV. Un fichero sin permisos, el `results.csv` abierto en Excel o la base de datos corrupta acaban en traza | Capturar `OSError` en la lectura, en la escritura y al abrir la base | ✅ Probado a mano: base corrupta, configuración mala y `results.csv` bloqueado |
| S4 | Media | [`create_admin.py`](../services/api/app/create_admin.py) | Ctrl+C o una entrada cerrada dan traza; la configuración y la base sin capturar | Salida limpia con «Cancelado» y código distinto de cero | ✅ Probado en `tests/test_cli_errors.py` |
| S5 | Media | [`mailer.py:152,164`](../services/api/app/mailer.py) (prueba por consola) | Uso y error a `stdout` en vez de `stderr` | `file=sys.stderr` | ✅ Hecho con el backend, en el mismo archivo |
| S6 | Baja | [`pandas_clean.py`](../skills/data-analysis/scripts/pandas_clean.py) | Lee `data.csv` sin ninguna comprobación | Comprobación del fichero y de las columnas, `stderr` y `sys.exit(1)` | ✅ Probado a mano: sin fichero y fichero vacío |

**Ya estaba bien:** la librería [`incident-analysis`](../packages/shared/incident-analysis/) lanza excepciones concretas (codificación, CSV vacío, columnas que faltan) y nunca hace `sys.exit`; `analyze.py` y `seed_incidents.py` ya escriben los errores en `stderr` y salen con `1`; ningún `print` saca emails, contraseñas ni claves.

## Webs estáticas — `uis/website/` y `uis/talent-lab/`

Sin `fetch`, sin `localStorage` y sin `console.*`. El formulario de la web pública simula el envío por decisión del hito 1, así que no tiene estados de red que gestionar. ➖

## Verificación

Hecha el 20/11/2026, con todas las correcciones en la rama.

| Comprobación | Resultado |
| --- | --- |
| Pruebas de la API (`uv run python -m unittest discover -s tests`) | ✅ 375 OK |
| Backoffice: `npm run typecheck`, `npm run lint` y `npm run build` | ✅ En verde |
| Skill [`verificar-etiquetas-de-dominio`](../.agents/skills/verificar-etiquetas-de-dominio/SKILL.md) | ✅ Mapas con 4 estados y 5 etapas; los dos `grep` sin resultados; ningún texto con guion bajo en el panel, candidaturas, proveedores ni incidencias |
| Recorrido en el navegador | ✅ 13/13 escenarios |

**Cómo se probó en el navegador.** Un script de Playwright, fuera del repositorio para no añadir dependencias, con el Chromium que ya estaba descargado en el equipo. El backoffice se arrancó en modo desarrollo y la API en un puerto aparte, con las bases de datos en una carpeta temporal y una cuenta de prueba, sin tocar los datos locales. Cada fallo se provoca interceptando la petición (red cortada, `404` o respuesta lenta); después se quita la interceptación y se pulsa «Reintentar».

| Escenario | Lo que se ve | Captura |
| --- | --- | --- |
| Login con la contraseña mal (`401` real) | «Email o contraseña incorrectos.» y el botón se reactiva | — |
| Login con la API caída | «No se ha podido conectar con el servidor.» y el botón se reactiva | [login-sin-api](./screenshots/error-handling-login-sin-api.png) |
| Candidaturas sin el tracker | Título, causa y «Reintentar»; al reintentar, la lista vuelve (100 filas) | [candidaturas-error](./screenshots/error-handling-candidaturas-error.png) |
| Ficha de una candidatura que no existe (`404`) | «No se ha podido cargar la candidatura» y «Volver al listado» | [candidatura-404](./screenshots/error-handling-candidatura-404.png) |
| Proveedores con respuesta lenta | «Cargando proveedores…» | [proveedores-cargando](./screenshots/error-handling-proveedores-cargando.png) |
| Proveedores sin la API | Error con «Reintentar»; al reintentar, los 15 proveedores | — |
| Incidencias con `/summary` caído | Aviso de una línea con «Reintentar», y la lista sigue debajo; al reintentar, el resumen vuelve | [incidencias-resumen-error](./screenshots/error-handling-incidencias-resumen-error.png) |
| Perfil con `/auth/me` caído | «No se ha podido cargar tu perfil» con «Reintentar», y el menú enseña «Mi cuenta» (F11) | [perfil-error](./screenshots/error-handling-perfil-error.png) |
| Una ruta que no existe | La página 404 en español con «Volver al panel» | [ruta-404](./screenshots/error-handling-ruta-404.png) |

**Valores de reserva con el valor crudo.** En [`CandidateList`](../uis/backoffice/components/CandidateList.tsx) (`STATUS_LABELS[…] ?? candidate.status`) y [`IncidentResults`](../uis/backoffice/components/IncidentResults.tsx) (`INCIDENT_STATUS_LABELS[…] ?? fila.status`), el valor de la API solo se pinta si le falta la etiqueta, es decir, si la API manda un valor que `CONTEXT.md` no define. Los mapas están tipados como `Record<…>` y cubren todos los valores conocidos, así que con datos válidos no aparece nunca. Se deja así a propósito: es mejor ver un valor raro que una celda vacía, y lo ve quien tiene que avisar del cambio de contrato.

## Fuera de alcance

Encontrado en la auditoría, pero arreglarlo es una funcionalidad o un cambio de diseño, no gestión de errores. Pasa a la deuda técnica de [`progress.md`](../memory-bank/progress.md).

| Asunto | Por qué no ahora |
| --- | --- |
| Escrituras atómicas en TinyDB (fichero temporal y `os.replace`) | Cambia cómo se guarda en las cinco bases. B6 ya hace que el fallo se comunique bien |
| Límite de tamaño de la subida contado mientras se lee | Hoy el `413` llega tras recibir el fichero entero. Pide un middleware propio |
| El `409` del registro revela si un email ya tiene cuenta | Decisión de producto de AUTH-01, no un error mal gestionado |
| Varios *workers* de uvicorn sobre los mismos ficheros JSON | El cerrojo es por proceso. Se documenta: un solo *worker* |
| `LogMailer` escribe el enlace de restablecimiento en el log si falta la clave de Resend | Es el modo de desarrollo documentado en AUTH-03. Se revisa al desplegar |
