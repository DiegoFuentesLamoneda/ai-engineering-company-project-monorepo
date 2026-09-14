---
name: verificar-etiquetas-de-dominio
description: Comprueba que ningún valor crudo de la API (in_progress, personal_interview…) llega a la interfaz y que el mapa de etiquetas cubre todos los valores de CONTEXT.md. Úsala antes de commitear cualquier cambio en una interfaz que muestre datos de la API.
---

# Skill · Verificar las etiquetas de dominio

## Objetivo

**Uno solo:** que ningún valor crudo de la API aparezca en la pantalla y que cada valor definido en [`CONTEXT.md`](../../../CONTEXT.md) tenga su etiqueta en español.

Es un criterio de aceptación literal del hito 3: *"los valores crudos de la API (`in_progress`, `personal_interview`, etc.) no deben aparecer nunca en la interfaz"*. Y es una regla binaria —o aparece o no aparece—, así que se comprueba con comandos, no con opinión.

Si Elena abre la herramienta y lee `personal_interview`, su conclusión es que el producto está a medio hacer. El vocabulario técnico filtrado a la interfaz es la señal más barata de producto inmaduro.

## Cuándo se usa

Antes de commitear cualquier cambio en una interfaz que muestre datos de la API: un componente nuevo, una columna añadida a un listado, un filtro, un formulario, una tarjeta de resumen.

## Inputs

| Input | Obligatorio | Valor por defecto |
| --- | --- | --- |
| Carpeta a revisar | Sí | `uis/backoffice` |
| Valores crudos del dominio | Sí | Los de `CONTEXT.md` (ver tabla) |
| Archivos donde **sí** pueden aparecer | Sí | `types/`, `lib/labels.ts`, `lib/api.ts` |
| Mapa de etiquetas | Sí | `lib/labels.ts` |

### Valores del dominio

Salen de `CONTEXT.md` y son la lista completa. Si la API devuelve alguno que no esté aquí, **se para y se pregunta**: el contexto manda.

| `status` | Etiqueta | `stage` | Etiqueta |
| --- | --- | --- | --- |
| `received` | Recibida | `pending` | Pendiente de revisión |
| `in_progress` | En proceso | `review` | En revisión |
| `selected` | Seleccionada | `personal_interview` | Entrevista personal |
| `discarded` | Descartada | `technical_interview` | Entrevista técnica |
| | | `offer_presented` | Oferta presentada |

### Dónde sí puede aparecer un valor crudo

No toda aparición es un error. Son legítimas:

- Las **definiciones de tipo** (`type Status = "received" | ...`).
- El **mapa de etiquetas** en `lib/labels.ts`: es justo su trabajo.
- El **cliente de API** en `lib/api.ts`: habla con el servidor, no con la persona.
- El atributo `value` de un `<option>`, siempre que el **texto visible** sea la etiqueta.
- Las **claves** de un objeto o un `Record<Status, …>`.

Es un error cuando el valor crudo se **renderiza como texto**.

## Procedimiento

### 1. Comprobar que el mapa está completo

Abrir `lib/labels.ts` y confirmar que `STATUS_LABELS` y `STAGE_LABELS` tienen **una entrada por cada valor** de la tabla de arriba, con la etiqueta exacta. Ni de más ni de menos.

> Si los mapas están tipados como `Record<Status, string>`, `npm run typecheck` ya detecta los que falten. Los que sobran, y las etiquetas mal escritas, no: eso se mira a ojo contra `CONTEXT.md`.

### 2. Buscar valores crudos fuera de los archivos permitidos

```bash
grep -rnE '"(received|in_progress|selected|discarded|pending|review|personal_interview|technical_interview|offer_presented)"' \
  uis/backoffice --include='*.ts' --include='*.tsx' \
  | grep -vE '(types/|lib/labels\.ts|lib/api\.ts)'
```

### 3. Buscar el error más habitual: interpolar el valor directamente en el JSX

```bash
grep -rnE '\{[a-zA-Z_$][a-zA-Z0-9_$]*\.(status|stage)\}' uis/backoffice --include='*.tsx'
```

Este es el que de verdad rompe la interfaz. Cualquier resultado hay que justificarlo o corregirlo.

### 4. Revisar cada hallazgo

Para cada línea devuelta, decidir si encaja en la lista de apariciones legítimas. Si no, sustituir por `STATUS_LABELS[…]` o `STAGE_LABELS[…]`.

### 5. Comprobarlo en pantalla

Levantar la aplicación (`npm run dev`) y recorrer el listado, el detalle, los filtros y los formularios. **Ningún texto visible contiene un guion bajo ni está en inglés.**

## Criterios de aceptación

- [ ] `STATUS_LABELS` tiene las **4** entradas y `STAGE_LABELS` las **5**, con las etiquetas exactas de `CONTEXT.md`.
- [ ] El comando del paso 2 **no devuelve ninguna línea**, o cada línea devuelta está justificada por la lista de apariciones legítimas.
- [ ] El comando del paso 3 **no devuelve ninguna línea**.
- [ ] En los desplegables de filtro, el `value` es el valor de la API y el texto visible es la etiqueta.
- [ ] Recorriendo la aplicación en el navegador, ningún texto visible contiene un guion bajo ni está en inglés.
- [ ] `npm run typecheck` pasa (garantiza que los mapas cubren el tipo completo).

## Qué NO hace esta skill

- No revisa ortografía ni redacción de los textos de interfaz.
- No valida que los datos de la API sean correctos: solo cómo se muestran.
- No traduce la aplicación a otro idioma. Cuando llegue el inglés para la oficina de Miami, se duplicará el mapa, y esta skill seguirá verificando exactamente lo mismo.
