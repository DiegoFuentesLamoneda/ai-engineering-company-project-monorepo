---
description: Convenciones de la aplicación interna en Next.js — etiquetas de dominio, cliente único de API, estado en la URL y Tailwind por tokens.
globs: ["uis/backoffice/**"]
alwaysApply: false
---

# Backoffice — aplicación interna en Next.js

**Ámbito: por patrón de archivo.** Se carga al tocar cualquier archivo bajo `uis/backoffice/**`.

Stack fijado: Next.js 16 (App Router), React 19, TypeScript 5, Tailwind 4. Sin librería de gestión de estado.

## 1. Ningún valor crudo de la API llega a la pantalla

La API habla en identificadores (`in_progress`, `personal_interview`); la interfaz habla el idioma de Nexova ("En proceso", "Entrevista personal"). La traducción vive **solo** en [`lib/labels.ts`](../../uis/backoffice/lib/labels.ts).

```tsx
// ✅
<span>{STATUS_LABELS[candidate.status]}</span>

// ❌ el usuario acaba leyendo "in_progress"
<span>{candidate.status}</span>
```

Vale también para los desplegables de filtro: el `value` del `<option>` es el valor de la API, el texto visible es la etiqueta.

Se verifica con la skill [`verificar-etiquetas-de-dominio`](../skills/verificar-etiquetas-de-dominio/SKILL.md), y es criterio de aceptación del hito 3: *"los valores crudos de la API no deben aparecer nunca en la interfaz"*.

## 2. Todo `fetch` pasa por `lib/api.ts`

Un solo punto de entrada a la red. Ahí viven la URL base, las cabeceras, el manejo de los dos formatos de error que devuelve la API y `ApiError`. Un `fetch` suelto en un componente se salta todo eso.

Al añadir un endpoint: una función exportada en `lib/api.ts` que llame a `request<T>()`, nunca a `fetch` directamente.

Detalles del contrato que ya están resueltos y no hay que redescubrir:

- Los candidatos viven en `/records`, no en `/candidates`.
- `PUT` reemplaza el registro entero; `PATCH` solo toca `status` y `stage`.
- Las notas llegan envueltas en `{ data, meta }`; `getNotes` devuelve ya el array.
- Un `204` no trae cuerpo. No se le hace `.json()`.

## 3. El estado vive en la URL

Filtros, búsqueda y paginación van en la query string con `useSearchParams`. Así un consultor puede pasarle a otro el enlace de "candidaturas en entrevista técnica" y el botón "atrás" funciona solo.

> Todo componente que use `useSearchParams` necesita una frontera de `<Suspense>` por encima, o el prerenderizado falla en `npm run build`. Esto ya ha pasado una vez.

No se añaden Redux, Zustand ni context providers globales. Si algo parece necesitarlos, se pregunta antes.

## 4. Server Components por defecto

`"use client"` solo en los componentes que de verdad necesitan estado, efectos o eventos. Se pone en la hoja del árbol, no en el layout: marcar un layout como cliente arrastra toda la rama al navegador.

## 5. Tailwind con los tokens de marca

Paleta `marca-*` y `acento-*`, definida como tokens en `app/globals.css` (Tailwind 4 ya no usa `tailwind.config.js`). Fondo oscuro: la herramienta se mira ocho horas al día.

Nada de CSS a mano ni de colores sueltos tipo `bg-[#1a2b3c]`. Si falta un tono, se añade como token.

## 6. Accesibilidad

Es una herramienta de trabajo diario, no una landing:

- Todo `input` tiene su `<label>` asociado. El `placeholder` no es una etiqueta.
- Estados de foco visibles (`focus-visible:outline-*`). Se navega mucho con teclado.
- Los estados de carga y de error se muestran en pantalla, no solo en consola.
- Los errores por campo que devuelve la API se pintan junto a su campo.

## 7. Las notas internas no salen del detalle

Son anotaciones del consultor sobre una persona. Se muestran **solo** en el detalle de la candidatura, nunca en el listado ni en ninguna vista agregada.

## Cómo se verifica

Desde `uis/backoffice/`, antes de commitear:

```bash
npm run typecheck   # ni un error de tipos
npm run lint        # ESLint limpio
npm run build       # el build de producción pasa (aquí saltan los Suspense que faltan)
```

Y la skill [`verificar-etiquetas-de-dominio`](../skills/verificar-etiquetas-de-dominio/SKILL.md) sobre `uis/backoffice/`.
