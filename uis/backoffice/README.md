# Backoffice de Nexova Solutions

La **aplicación interna** de Nexova: el sitio donde el equipo trabaja, frente a
[`uis/website`](../website/), que es la cara pública de la empresa.

Hoy cubre las **operaciones de selección**, el **análisis de incidencias de soporte** y el
**directorio de proveedores**, detrás de un **login**. A medida que avancen los hitos irá albergando el
resto de capacidades internas —formación, soporte, RR. HH.— como secciones nuevas, en lugar de
crear una aplicación por cada una.

Hitos 3 y 4 y proyectos «Analizador de Incidencias», «Directorio de Proveedores», «Conectando
el Candado» (AUTH-02) y «La Pieza Que Faltaba» (AUTH-03) del proyecto transversal de AI
Engineering · 4Geeks Academy.

---

## Qué hace

### Acceso (`/login`, `/register`, `/forgot-password`, `/reset-password`)

Todo el backoffice pide sesión. Las cuentas son las de la API propia,
[`services/api`](../../services/api/), que debe estar arrancada.

- **Entrar** con email y contraseña (`POST /auth/login`). El token se guarda en `localStorage`.
- **Crear cuenta** (`POST /users`) con email y contraseña, y nombre, teléfono y dirección
  opcionales. Después entra sola.
- Los errores salen **bajo cada campo**. Un email ya registrado se marca en el campo email; un
  login fallido dice solo «Email o contraseña incorrectos.», sin aclarar cuál de los dos.
- **Sin sesión**, cualquier vista protegida lleva a `/login?next=<ruta>` y, al entrar, vuelve
  a esa ruta. Con sesión, las cuatro pantallas de acceso llevan al panel.
- **Olvidé la contraseña** (enlace «¿Olvidaste tu contraseña?» en `/login`): `/forgot-password`
  pide el email (`POST /auth/forgot-password`) y responde siempre «Si esa dirección está
  registrada, recibirás un enlace en breve.», tenga cuenta o no. Después el formulario queda
  desactivado. Solo un fallo de red o de la API sale como error.
- **Contraseña nueva** con el enlace del email: `/reset-password?token=…` pide la contraseña dos
  veces y no llama a la API si no coinciden (`POST /auth/reset-password`). Si sale bien, lleva a
  `/login` con el aviso «Contraseña actualizada». Si el enlace no vale (inventado, caducado o ya
  usado), muestra el error de la API y un enlace para pedir otro.
- **Cerrar sesión** borra el token y lleva a `/login`. Si la sesión termina sola (caduca a los
  30 minutos, la API responde `401` o se cierra en otra pestaña), `/login` lo explica.

Vistas protegidas: `/`, `/candidates`, `/candidates/new`, `/candidates/[id]`,
`/candidates/[id]/edit`, `/incidents/analyze`, `/incidents/new`, `/suppliers`, `/suppliers/new`, `/account/profile` y
`/account/change-password`.

### Mi perfil (`/account/profile`)

- El **email** de la cuenta, que no se cambia desde aquí.
- **Nombre, teléfono y dirección**, editables (`PUT /profiles/me`). Dejar un campo vacío lo
  borra.
- El nombre del menú de sesión, arriba a la derecha, se actualiza al guardar, sin recargar.
- Un enlace a **Cambiar la contraseña**.

### Cambiar la contraseña (`/account/change-password`)

- Pide la contraseña actual, la nueva y la nueva otra vez (`POST /auth/change-password`).
- Antes de llamar a la API comprueba que la confirmación coincide, la longitud mínima y que la
  nueva no sea igual que la actual. Si algo falla, no se envía nada.
- Si la actual no es correcta, el mensaje de la API sale bajo ese campo y la sesión sigue igual.
- Si sale bien, se guarda el token nuevo que devuelve la API y se sigue dentro. Las sesiones
  abiertas en otros navegadores o equipos se cierran en su siguiente petición.
- En el menú lateral sigue marcado «Mi perfil»: es parte de la cuenta.

### Panel (`/`)

Vista de entrada con el estado del trabajo en curso:

- **Proceso activo**: puesto, sede, perfil buscado y quién lo ha solicitado.
- **Estado del proceso en vivo**: candidaturas por estado y reparto por etapa, leídos de la API.
- **Líneas de negocio y áreas** de la empresa, con sus responsables y el tamaño de cada equipo.

Los datos de empresa salen de [`CONTEXT.md`](../../CONTEXT.md) a través de
[`lib/company.ts`](./lib/company.ts); los del proceso, de la API.

### Candidaturas (`/candidates`)

El Talent Pipeline Tracker, que sustituye la hoja de cálculo compartida con la que se gestionaba
el proceso de **Asistente de Dirección** (sede de Valencia):

- **Listado** de candidaturas con nombre, puesto, estado y etapa.
- **Filtros** por estado y por etapa, y **búsqueda** por nombre o email, sin recargar la página.
- **Detalle** de cada candidatura con todos sus datos.
- **Cambio de estado y etapa** desde el detalle (`PATCH`).
- **Notas internas**: listar, añadir y eliminar.
- **Alta** de nuevas candidaturas (`POST`) y **edición** de las existentes (`PUT`).

### Análisis de incidencias (`/incidents/analyze`)

Análisis de la exportación CSV del helpdesk de soporte al cliente:

- **Subida** del CSV arrastrándolo a la zona de carga o eligiéndolo con el selector de archivos.
- **Totales**: registros leídos, válidos e inválidos.
- **Registros no válidos por tipo**: cuántos incumplen cada regla y, desplegable, en qué línea
  del fichero está cada uno.
- **Desglose por categoría y por estado**, con número de tickets y porcentaje sobre los válidos.
- **Índice de satisfacción**: media de los tickets cerrados y reparto de puntuaciones del 1 al 5.
- **Descarga** de `results.csv`, el mismo fichero que genera `scripts/analyze.py`.

El análisis lo hace la API propia, [`services/api`](../../services/api/), que debe estar
arrancada (ver su README). El email de los clientes no aparece en ninguna parte del resultado.

### Nueva incidencia (`/incidents/new`)

El formulario del gestor de incidencias centralizado: la primera pieza de la herramienta que
sustituye los correos sueltos, los Excel por oficina y las llamadas.

- **Campos**: título (hasta 120 caracteres), descripción (hasta 2000), categoría, quién la
  reporta y sede, todos obligatorios. Título y descripción llevan contador.
- **Ayuda en cada desplegable**: al elegir categoría u origen se lee su descripción del briefing.
- **La sede siempre está a la vista**, con las cuatro oficinas del briefing. Si la reporta
  *Personal de una oficina*, el campo se resalta; si no, la ayuda dice que se use Central.
- **Validación en el navegador** antes de enviar, y los errores de la API bajo su campo.
- Mientras se envía, el botón se desactiva y dice «Registrando…». Al registrarla, el formulario
  se vacía y un aviso confirma el título registrado.

La incidencia nace *Abierta*: el estado no se elige al registrarla.

### Proveedores (`/suppliers`)

El directorio de proveedores externos de las dos oficinas, que sustituye la hoja de cálculo de
Patricia:

- **Tabla** con nombre, país, categorías, tarifa mensual, renovación del contrato y estado.
- **Filtros** por país y por categoría, combinables y sin recargar la página.
- **Cambio de tarifa** en la propia fila, con la fecha del último cambio debajo.
- **Suspender y reactivar** desde la fila. Los suspendidos se ven atenuados y con la etiqueta en
  rojo.
- **Aviso de renovación**: los contratos que renuevan en los próximos 60 días llevan una marca y
  el contador de arriba dice cuántos son.
- **Alta** de proveedores (`/suppliers/new`) con validación en el navegador y los errores de la
  API bajo su campo.

Los datos los guarda la API propia, [`services/api`](../../services/api/), en TinyDB. Para
tener datos de ejemplo, `uv run seed` desde `services/api` (ver su README).

---

## Stack

| Pieza | Versión |
| --- | --- |
| Next.js (App Router) | 16 |
| React | 19 |
| TypeScript | 5 |
| Tailwind CSS | 4 |

Sin librerías de gestión de estado: el estado vive en la URL y en los componentes.

---

## Puesta en marcha

```bash
npm install
cp .env.example .env.local   # en PowerShell: Copy-Item .env.example .env.local
npm run dev
```

La app queda en `http://localhost:3000`.

### Variables de entorno

| Variable | Descripción |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | URL base de la API del tracker |
| `NEXT_PUBLIC_NEXOVA_API_URL` | URL base de la API propia, [`services/api`](../../services/api/) (`http://localhost:8000` en local). Sin ella no se puede entrar: la usan el login, el perfil, incidencias y proveedores |

`.env.local` **no se versiona**. `.env.example` sí, como plantilla.

> El prefijo `NEXT_PUBLIC_` incrusta la variable en el bundle del navegador: es pública.
> Nunca debe usarse para credenciales.

### Comandos

| Comando | Qué hace |
| --- | --- |
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | Build de producción |
| `npm start` | Sirve el build (`npm start -- -p 3001` para otro puerto) |
| `npm run typecheck` | Comprueba tipos (`tsc --noEmit`) |
| `npm run lint` | ESLint |

---

## Estructura

```
app/                         Rutas (App Router)
  layout.tsx                 Layout raíz: html, fuentes y fondo, común a todas las vistas
  (auth)/                    Vistas sin sesión. El grupo no aparece en la URL
    layout.tsx               Tarjeta centrada con el logotipo y GuestGuard
    login/                   Entrar
    register/                Crear cuenta
    forgot-password/         Pedir el enlace para restablecer la contraseña
    reset-password/          Elegir la contraseña nueva con el enlace del email
  (protected)/               Vistas con sesión. El grupo no aparece en la URL
    layout.tsx               AuthGuard, barra lateral, cabecera con el menú de sesión y pie
    page.tsx                 Panel de entrada
    candidates/              Listado
    candidates/new/          Alta
    candidates/[id]/         Detalle
    candidates/[id]/edit/    Edición
    incidents/analyze/       Análisis de incidencias (CSV)
    incidents/new/           Alta de incidencia en el gestor
    suppliers/               Directorio de proveedores
    suppliers/new/           Alta de proveedor
    account/profile/         Mi perfil
    account/change-password/ Cambiar la contraseña con la actual
components/
  AppNav.tsx                 Navegación entre secciones
  AuthGuard.tsx              Sin sesión, a /login?next=…; cierra la sesión cuando caduca
  GuestGuard.tsx             Con sesión, fuera de las pantallas de acceso
  SessionMenu.tsx            Quién ha entrado y «Cerrar sesión»
  LoginNotice.tsx            Avisos de /login según ?reason=
  LoginForm.tsx              Formulario de entrada
  RegisterForm.tsx           Formulario de alta de cuenta
  ForgotPasswordForm.tsx     Pedir el enlace de restablecimiento
  ResetPasswordForm.tsx      Contraseña nueva con el token de ?token=
  ProfileForm.tsx            Formulario de Mi perfil
  ChangePasswordForm.tsx     Cambiar la contraseña con la actual
  FormField.tsx              Campo con etiqueta y error accesible, común a los formularios
  BrandLogo.tsx              Logotipo de Nexova, en línea
  PipelineSummary.tsx        Estado del proceso en vivo
  Candidate*.tsx             Interfaz del tracker
  Incident*.tsx              Análisis del CSV de incidencias (subida, resultado, descarga)
  IncidentForm.tsx           Alta de incidencia en el gestor
  Supplier*.tsx              Filtros, tabla, edición por fila y alta de proveedores
hooks/                       Lógica de datos reutilizable
  useIncidentAnalysis.ts     Estado del análisis: fichero, carga, error y resultado
  useSupplierFilters.ts      Filtros de proveedores leídos de la URL y validados
  useSuppliers.ts            Listado de proveedores: carga, error y refresco de una fila
lib/
  api.ts                     Cliente único de las dos APIs; pone el token y cierra la sesión ante un 401
  session.ts                 Token en localStorage, caducidad leída del JWT y aviso entre pestañas
  useSession.ts              Hook: ¿hay sesión válida? (useSyncExternalStore)
  auth-routes.ts             Rutas de acceso y validación de ?next=
  account.ts                 Validación de los datos de cuenta y aviso de perfil actualizado
  company.ts                 Datos de empresa tomados de CONTEXT.md
  labels.ts                  Etiquetas de dominio en español
  format.ts                  Formato de fechas, importes, números y porcentajes
  suppliers.ts               Reglas del BRIEFING: moneda por país y aviso de renovación
types/auth.ts                Contrato de la API de cuentas y perfiles en TypeScript
types/candidate.ts           Contrato de la API del tracker en TypeScript
types/incident.ts            Contrato del análisis de incidencias (CSV) en TypeScript
types/incident-manager.ts    Contrato del gestor de incidencias en TypeScript
types/supplier.ts            Contrato de la API de proveedores en TypeScript
```

Las páginas son Server Components; `"use client"` se aplica solo en los componentes que
necesitan interacción, para reducir el JavaScript enviado al navegador.

---

## Contrato de la API

Esta sección describe la API del tracker. Las de incidencias y proveedores están documentadas en
[`services/api/README.md`](../../services/api/README.md).

Explorado con Postman antes de escribir código. Lo relevante:

| Endpoint | Respuesta |
| --- | --- |
| `GET /records` | `{ total, page, limit, data[] }` |
| `GET /records/:id` | Objeto plano, **sin** `notes` (solo `notes_count`) |
| `GET /records/:id/notes` | `{ data[], meta: { total } }` |
| `POST /records` | `201` + objeto. Nace como `received` / `pending` |
| `PATCH /records/:id` | Objeto completo. Solo `status` y `stage` |
| `PUT /records/:id` | Objeto completo. **Exige todos los campos obligatorios** |
| `DELETE` | `204` **sin cuerpo** |

Comportamientos a tener en cuenta:

- Un **filtro inválido o una página inexistente devuelven `200` con `data: []`**, no un error.
  Por eso `Status` y `Stage` son tipos cerrados en TypeScript y los valores que llegan por
  la URL se validan antes de usarse.
- Hay **dos formatos de error distintos**, ambos con código 422:
  `{ error, details: { campo } }` y `{ detail: [ { loc, msg } ] }`. `lib/api.ts` los
  normaliza a un único `ApiError`.
- La API **valida tipos pero no sentido**: acepta 7000 años de experiencia. La validación
  razonable se hace en el formulario.

---

## Decisiones tomadas

**Estado en la URL.** Los filtros y la búsqueda viven en query params. Así los enlaces son
compartibles, `F5` no pierde el contexto y volver desde el detalle mantiene los filtros. Como
efecto secundario, el componente de filtros y el listado no se pasan props: cada uno lee la URL.

**Sin librería de estado.** No hace falta: no hay estado global que compartir. La sesión vive en
`localStorage` y se lee con `useSyncExternalStore`; el perfil guardado se avisa con un evento del
navegador (`nexova:profile`).

**Etiquetas de dominio separadas.** `lib/labels.ts` traduce los valores de la API a las
etiquetas del `CONTEXT` de Nexova. Los valores crudos (`in_progress`, `offer_presented`) nunca
aparecen en pantalla.

**Refresco sin recargar.** `PATCH`, `POST` y `PUT` devuelven el objeto actualizado y se usa esa
respuesta para refrescar la vista, en lugar de lanzar una segunda petición.

**No hay borrado de candidaturas.** La API lo permite, pero en un proceso de selección no se
borra a un candidato: se marca como **Descartada**. Borrar destruiría la trazabilidad y las
notas de las entrevistas. `deleteCandidate()` existe en el cliente por si más adelante hiciera
falta para una solicitud de supresión de datos (RGPD), pero no se expone en la interfaz.

**Tema oscuro fijo.** Usa los tokens de marca de `uis/website` (`marca-*`, `acento-*`). Soportar
claro y oscuro obligaría a verificar el contraste dos veces en cada componente.

**Sin paginación.** Se piden 100 candidaturas de una vez (`limit=100`). Con el volumen actual
(~100 registros) es suficiente y evita el problema de sincronizar la página con los filtros. Si
el volumen creciera, habría que paginar y resetear la página al cambiar un filtro.

**Móvil con scroll horizontal.** La tabla no se adapta a pantallas pequeñas. Es una decisión
consciente: la herramienta se usa desde el puesto de trabajo. La alternativa sería una vista de
tarjetas por debajo de 768 px.

**Altura de la tabla con un valor fijo.** En escritorio solo hace scroll la tabla, con
`calc(100vh-20rem)`. Es un número mágico: si crece la cabecera hay que ajustarlo —al añadir el
pie del layout hubo que subirlo de 17rem a 20rem—. La solución robusta sería una cadena de
contenedores flex con `min-h-0`.

**Layout propio, distinto del de la web pública.** Barra lateral de navegación en escritorio,
cabecera con las secciones en móvil y un pie permanente recordando que las candidaturas y las
notas son información sobre personas. La web pública tiene su propia cabecera y su propio pie,
pensados para un visitante; aquí el usuario es alguien que trabaja ocho horas con la herramienta
y necesita saber siempre dónde está. Comparten la identidad visual —los mismos tokens `marca-*`
y `acento-*`, el mismo logotipo— pero no el layout.

**Los datos de empresa, en un módulo con su fuente citada.** `lib/company.ts` recoge las líneas
de negocio, las áreas y el proceso activo tal y como están en `CONTEXT.md`. Tenerlos en un solo
sitio evita que se repitan por los componentes y deja explícito de dónde sale cada cifra. Por la
misma razón el responsable de Ventas aparece sin asignar: el briefing lo nombra de dos formas
distintas, así que la interfaz lo dice en vez de elegir.

**El desglose del panel avisa cuando es parcial.** La API pagina y se piden 100 candidaturas. Si
hubiera más, el reparto por estado y etapa sería el de esa muestra, no el total, y el panel lo
dice en pantalla. Un panel que enseña números parciales como si fueran totales miente, y a
partir de ahí nadie se fía de ninguno.

**Incidencias: el navegador no calcula nada.** Totales, porcentajes y media llegan hechos de la
API, que usa el mismo paquete que el script (`packages/shared/incident-analysis`). Si el front volviera a
calcular, habría dos implementaciones que con el tiempo darían cifras distintas.

**El análisis no vive en la URL.** A diferencia de los filtros del tracker, un fichero no cabe en
un enlace. El resultado está en el estado del componente: al recargar la página hay que volver a
subir el CSV.

**La subida va en `FormData` sin `Content-Type` a mano.** El navegador pone
`multipart/form-data` con su *boundary*, la marca que separa las partes del cuerpo. Fijar la
cabecera a mano la pierde y la API no sabría leer el fichero.

**La descarga pasa por `fetch`, no por un enlace directo.** Así un 404 (no hay análisis) o la API
caída se muestran como un mensaje en pantalla, y no como una pestaña con un JSON de error.

**Las reglas de validación, con etiqueta en español.** Los códigos de la API
(`closed_without_score`, `invalid_email`…) se traducen en `lib/labels.ts`, como los estados del
tracker. La excepción consciente es el error de columnas que faltan: nombra las columnas tal y
como se llaman en la cabecera del CSV, porque es lo que hay que corregir en el fichero.

**Proveedores: etiquetas aprobadas, no inventadas.** El BRIEFING define los valores de país,
categoría y estado, pero no su texto en español. Las etiquetas de `lib/labels.ts` las aprobó Diego
el 11/11/2026 antes de escribirlas. La excepción consciente es la moneda: se muestra `EUR` o
`USD`, el código ISO que usa contabilidad, y en los importes el símbolo (`450,00 €`).

**Gestor de incidencias: dos vocabularios con el mismo nombre.** El analizador del CSV ya tenía
`IncidentStatus` e `IncidentCategory` (`OPEN`, `TECHNICAL`…). Los del gestor son otros valores,
así que sus tipos se llaman `IncidentManagerStatus` e `IncidentManagerCategory`, viven en
[`types/incident-manager.ts`](./types/incident-manager.ts) y sus etiquetas llevan el prefijo
`MANAGER_` en `lib/labels.ts`.

**Gestor de incidencias: etiquetas aprobadas y sedes literales.** Las sedes son la tabla
«Oficinas de Nexova» del briefing, tal cual, para que *Remoto* no se confunda con *Central* ni con
*Valencia — Operaciones*. Estados, categorías y orígenes no tienen nombre corto en el briefing:
sus etiquetas las aprobó Diego el 19/11/2026. Las descripciones de la ayuda sí son literales.

**Gestor de incidencias: solo en español.** El briefing pide versión bilingüe solo si la interfaz
ya la tenía. El backoffice no la tiene: todas sus etiquetas están en español.

**Los errores del gestor se escriben a partir de un código.** El `400` del gestor trae, por cada
campo, un `code` estable (`missing`, `too_long`, `invalid_choice`…) además del mensaje.
`lib/api.ts` los guarda en `fieldCodes` y el formulario escribe su propio texto llano («Falta el
título»). El mensaje de la API («El campo 'title' es obligatorio») está pensado para quien la usa
directamente, no para quien rellena el formulario.

**Los desplegables del gestor empiezan vacíos.** Con *Central* preseleccionada, una incidencia de
Miami se quedaría en Valencia por no mirar el campo. Vacío, hay que elegir.

**La moneda no se elige: la fija el país.** El formulario no tiene campo de moneda. España
factura en EUR y EE. UU. en USD (BRIEFING), así que el formulario la deduce y la API rechaza una
combinación que no cuadre. Un campo que solo admite una respuesta correcta es un error esperando
a pasar.

**El aviso de renovación se calcula en hora local.** `contract_renewal_date` llega como
`YYYY-MM-DD`. `new Date("2026-12-01")` lo interpreta como medianoche UTC, que en Miami es el día
anterior, así que [`lib/suppliers.ts`](./lib/suppliers.ts) construye la fecha con año, mes y día.
Los proveedores del seed renuevan todos en 2025: para ver el aviso hay que dar de alta uno con
la fecha a menos de 60 días.

**Los errores de Pydantic se traducen, no se muestran.** Los mensajes que genera Pydantic llegan
en inglés (`Input should be greater than 0`). El formulario muestra un texto en español por cada
campo rechazado. Las reglas propias de la API ya están en español: `lib/api.ts` solo les quita
el prefijo `Value error, ` que añade Pydantic.

**Sin borrado de proveedores en la interfaz.** El enunciado no lo pide y suspender ya cubre el
caso de uso: el proveedor deja de usarse, pero su historial sigue ahí. La API sí tiene
`DELETE /suppliers/{id}`, y rechaza con 409 borrar uno suspendido.

**La edición por fila no recarga la lista.** Los `PATCH` devuelven el proveedor completo y
`useSuppliers` sustituye esa fila. Ni la tarifa ni el estado cambian el país o las categorías,
así que la fila sigue cumpliendo el filtro activo.

**El token, en `localStorage`, y la guardia, en el navegador.** Lo pide el enunciado de AUTH-02,
sin *middleware* de Next. El servidor no puede leer `localStorage`, así que ninguna página pide
datos desde el servidor: `AuthGuard` no pinta la vista hasta saber que hay sesión, y la API exige
el token en cada petición, que es el candado de verdad. El riesgo de `localStorage` es el XSS, y
por eso aquí no se usa `dangerouslySetInnerHTML` y el token dura 30 minutos. El razonamiento
completo está en [`techContext.md`](../../memory-bank/techContext.md).

**Los formularios no navegan: navega la sesión.** Entrar guarda el token y cerrar sesión lo
borra, nada más. Las guardias ven el cambio y deciden adónde ir. Así, cerrar sesión aquí, en otra
pestaña, por caducidad o por un `401` acaba siempre en `/login`, por el mismo camino.

**`?next=` solo admite rutas propias.** `lib/auth-routes.ts` descarta cualquier otro origen. Un
enlace `/login?next=https://otro-sitio` no saca a nadie fuera del backoffice tras entrar.

**El perfil envía solo lo que cambia.** `PUT /profiles/me` deja como está lo que no llega y borra
lo que llega a `null`. Si no hay cambios, no se llama a la API.

**El login no dice qué ha fallado.** La API da el mismo `401` para un email desconocido y una
contraseña mala, y el formulario lo respeta: decir «ese email no existe» enseñaría qué cuentas
hay.

**«Olvidé la contraseña» tampoco lo dice.** El mensaje tras pedir el enlace es una constante del
frontend, literal del ticket AUTH-03, igual con cuenta o sin ella. Lo único que se muestra como
error es lo que no depende de la cuenta (sin conexión, API caída): ahí decir «recibirás un
enlace» sería mentir.

**El token del enlace no sale de la página.** `/reset-password` lleva `referrer: no-referrer`,
para que ninguna petición a otro sitio reciba la URL con el token en la cabecera `Referer`. Al
acabar se navega con `router.replace`, así «atrás» no vuelve a la URL del token. El token se lee
en el navegador con `useSyncExternalStore`, como `?reason=` en `/login`: la página sigue siendo
estática y no necesita `<Suspense>`.

**Las pantallas de recuperación son solo sin sesión.** Con sesión, `GuestGuard` lleva al panel:
quien ha entrado cambia la contraseña desde su cuenta, sabiendo la actual.

## Posibles mejoras

**Avisar de que el enlace está gastado al abrirlo, no al enviar.** Hoy `/reset-password` pide la
contraseña nueva aunque el enlace ya se haya usado o haya caducado, y el error sale al pulsar
«Guardar». Probado con un email real en la fase 8: funciona, pero hace escribir dos veces una
contraseña para nada. Avisar al abrir tiene tres costes, y por eso no entra en AUTH-03:

- **Una ruta más en la API** (por ejemplo, `GET /auth/reset-password/{token}`) solo para
  consultar si el enlace vale.
- **Que no delate nada.** Tendría que responder lo mismo para un enlace inventado, caducado o
  usado, y sin decir de qué cuenta es. Si no, cualquiera podría probar tokens para averiguar qué
  enlaces existen.
- **Que la consulta no gaste el enlace.** Algunos filtros de correo (Microsoft Safe Links, por
  ejemplo) abren los enlaces antes que la persona. La consulta tiene que ser de solo lectura, como
  hoy lo es abrir la página.
