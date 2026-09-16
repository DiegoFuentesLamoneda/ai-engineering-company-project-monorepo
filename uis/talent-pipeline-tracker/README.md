# Talent Pipeline Tracker

Herramienta interna del equipo de **People & Talent de Nexova** para el seguimiento de
candidaturas. Sustituye la hoja de cálculo compartida con la que se estaba gestionando el
proceso de selección de **Asistente de Dirección** (sede de Valencia).

Hito 3 del proyecto transversal de AI Engineering · 4Geeks Academy.

---

## Qué hace

- **Listado** de candidaturas con nombre, puesto, estado y etapa.
- **Filtros** por estado y por etapa, y **búsqueda** por nombre o email, sin recargar la página.
- **Detalle** de cada candidatura con todos sus datos.
- **Cambio de estado y etapa** desde el detalle (`PATCH`).
- **Notas internas**: listar, añadir y eliminar.
- **Alta** de nuevas candidaturas (`POST`) y **edición** de las existentes (`PUT`).

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
  page.tsx                   Listado
  candidates/new/            Alta
  candidates/[id]/           Detalle
  candidates/[id]/edit/      Edición
components/                  Componentes de interfaz
hooks/                       Lógica de datos reutilizable
lib/
  api.ts                     Cliente único de la API
  labels.ts                  Etiquetas de dominio en español
  format.ts                  Formato de fechas
types/candidate.ts           Contrato de la API en TypeScript
```

Las páginas son Server Components; `"use client"` se aplica solo en los componentes que
necesitan interacción, para reducir el JavaScript enviado al navegador.

---

## Contrato de la API

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
`calc(100vh-17rem)`. Es un número mágico: si crece la cabecera hay que ajustarlo. La solución
robusta sería una cadena de contenedores flex con `min-h-0`.
