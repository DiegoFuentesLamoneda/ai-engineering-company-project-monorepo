---
description: CONTEXT.md es la fuente de verdad del dominio. No se inventan datos de negocio ni se busca en el archivo de otras empresas.
alwaysApply: true
---

# Contexto de empresa

**Ámbito: siempre activa.** Aplica a todo el repositorio, en toda sesión.

## La regla

[`CONTEXT.md`](../../CONTEXT.md) es la fuente única de verdad sobre Nexova Solutions. Cuando fija un nombre de campo, un valor de dominio o un texto, **se usa literalmente**. Una implementación genérica que ignore el contexto no se acepta.

Si el banco de memoria y `CONTEXT.md` se contradicen, gana `CONTEXT.md` y el banco de memoria está desfasado: se corrige en el mismo commit.

## No se inventan datos de negocio

Nombres de personas, cifras, clientes, precios, SLAs, puestos, sedes. Si hace falta un dato que `CONTEXT.md` no da, **se para y se pregunta**. Un dato inventado en una demo se convierte en un dato inventado en una reunión con el cliente.

Lo mismo con el vocabulario: se dice *candidatura*, no "solicitud"; *etapa*, no "fase"; *consultor*, no "recruiter". El glosario completo está en [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md).

## Ambigüedades conocidas

`CONTEXT.md` nombra a **Megan Clarke** y a **Marcos Ibáñez** como responsable de Ventas en dos secciones distintas. Sin resolver. Si un entregable necesita ese nombre, se pregunta antes de elegir uno.

Toda ambigüedad nueva que se detecte se anota en `projectbrief.md`, en lugar de resolverla por cuenta propia.

## `docs/contexts-archive/` no se lee

Contiene los contextos de las otras tres empresas del track (Brasaland, HealthCore, TrackFlow): 155 archivos que responden a casi cualquier búsqueda sobre el dominio y taparían los resultados de Nexova. Está en el [`.ignore`](../../.ignore) de la raíz, pero la regla aplica aunque la herramienta que uses no lo respete.

Solo se consulta si la persona con la que trabajas lo pide explícitamente.

## Lo que hay que leer, y en qué orden

1. [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md) — negocio
2. [`memory-bank/techContext.md`](../../memory-bank/techContext.md) — stack y decisiones
3. [`memory-bank/progress.md`](../../memory-bank/progress.md) — estado
4. [`CONTEXT.md`](../../CONTEXT.md) — apéndice del hito en curso

## Cómo se verifica

Antes de dar por terminado un cambio que muestre o manipule datos de negocio:

- Cada valor de dominio que aparece en el código existe en `CONTEXT.md`. Los estados son exactamente `received`, `in_progress`, `selected`, `discarded`; las etapas, `pending`, `review`, `personal_interview`, `technical_interview`, `offer_presented`.
- Ningún nombre propio, cifra o cliente aparece en el código sin estar en `CONTEXT.md`.
- Ningún archivo de `docs/contexts-archive/` ha entrado en el contexto de trabajo.
