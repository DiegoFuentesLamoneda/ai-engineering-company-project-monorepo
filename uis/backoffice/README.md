# Backoffice de Nexova Solutions

La **aplicación interna** de Nexova: el sitio donde el equipo trabaja, frente a
[`uis/website`](../website/), que es la cara pública de la empresa.

Hoy cubre las **operaciones de selección**, el **análisis de incidencias de soporte** y el
**directorio de proveedores**. A medida que avancen los hitos irá albergando el
resto de capacidades internas —formación, soporte, RR. HH.— como secciones nuevas, en lugar de
crear una aplicación por cada una.

Hitos 3 y 4 y proyectos «Analizador de Incidencias» y «Directorio de Proveedores» del proyecto
transversal de AI Engineering · 4Geeks Academy.

---

## Qué hace

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

### Incidencias (`/incidents`)

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
| `NEXT_PUBLIC_NEXOVA_API_URL` | URL base de la API propia, [`services/api`](../../services/api/) (`http://localhost:8000` en local) |

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
  layout.tsx                 Layout propio: barra lateral, cabecera y pie
  page.tsx                   Panel de entrada
  candidates/                Listado
  candidates/new/            Alta
  candidates/[id]/           Detalle
  candidates/[id]/edit/      Edición
  incidents/                 Análisis de incidencias
  suppliers/                 Directorio de proveedores
  suppliers/new/             Alta de proveedor
components/
  AppNav.tsx                 Navegación entre secciones
  BrandLogo.tsx              Logotipo de Nexova, en línea
  PipelineSummary.tsx        Estado del proceso en vivo
  Candidate*.tsx             Interfaz del tracker
  Incident*.tsx              Subida, resultado y descarga del análisis de incidencias
  Supplier*.tsx              Filtros, tabla, edición por fila y alta de proveedores
hooks/                       Lógica de datos reutilizable
  useIncidentAnalysis.ts     Estado del análisis: fichero, carga, error y resultado
  useSupplierFilters.ts      Filtros de proveedores leídos de la URL y validados
  useSuppliers.ts            Listado de proveedores: carga, error y refresco de una fila
lib/
  api.ts                     Cliente único de las dos APIs (tracker y services/api)
  company.ts                 Datos de empresa tomados de CONTEXT.md
  labels.ts                  Etiquetas de dominio en español
  format.ts                  Formato de fechas, importes, números y porcentajes
  suppliers.ts               Reglas del BRIEFING: moneda por país y aviso de renovación
types/candidate.ts           Contrato de la API del tracker en TypeScript
types/incident.ts            Contrato de la API de incidencias en TypeScript
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

**Sin librería de estado.** No hace falta: no hay estado global que compartir.

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
API, que usa el mismo paquete que el script (`packages/incident-analysis`). Si el front volviera a
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
