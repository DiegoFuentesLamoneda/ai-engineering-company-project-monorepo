# Carpeta `memory-bank`

El **contexto activo del proyecto**: lo que cualquier agente de código —y cualquier persona que entre nueva— tiene que saber antes de escribir una línea en este repositorio.

No es documentación de archivo. Es el estado vigente de la empresa, del stack y del desarrollo, mantenido al día para que cada sesión no empiece desde cero y repita los mismos errores.

## Los archivos

| Archivo | Qué contiene | Cuándo se actualiza |
| --- | --- | --- |
| [`projectbrief.md`](./projectbrief.md) | **Contexto de negocio.** Qué es Nexova, quién decide, qué problema resolvemos, vocabulario de dominio y restricciones | Cuando cambia el encargo o aparece vocabulario de dominio nuevo |
| [`techContext.md`](./techContext.md) | **Contexto técnico.** Qué hay construido, con qué, decisiones de arquitectura tomadas y límites que no se cruzan | En el mismo commit que añade una dependencia, mueve una carpeta o toma una decisión de arquitectura |
| [`progress.md`](./progress.md) | **Estado del desarrollo.** Hitos entregados, trabajo en curso, próximos pasos y deuda técnica | En el commit que cierra un trabajo o cambia el plan |

## Orden de lectura

1. `projectbrief.md` — para qué existe esto
2. `techContext.md` — con qué está hecho y qué no se toca
3. `progress.md` — por dónde va

Después, [`CONTEXT.md`](../CONTEXT.md) para la especificación literal del hito en curso. Si el banco de memoria y `CONTEXT.md` se contradicen, **manda `CONTEXT.md`** y el banco de memoria está desfasado: se corrige en el acto.

## Por qué se mantiene al día

Un banco de memoria que no se actualiza deja de ser útil en cuestión de días, y entonces es peor que no tenerlo: el agente actúa con confianza sobre información falsa. Por eso actualizarlo no es un checklist aparte sino **el paso 3 del flujo obligatorio antes de cada commit** definido en [`AGENTS.md`](../AGENTS.md).

## Qué no va aquí

- **Especificaciones de hito** → [`docs/contexts/`](../docs/contexts/), y su apéndice vigente en [`CONTEXT.md`](../CONTEXT.md)
- **Cómo se ejecuta o se estructura un proyecto concreto** → el `README.md` de ese proyecto
- **Reglas de comportamiento del agente** → [`AGENTS.md`](../AGENTS.md) y [`.agents/`](../.agents/)
