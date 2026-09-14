# AGENTS.md — cómo se trabaja en este repositorio

Protocolo para cualquier agente de código que opere aquí (Claude Code, Cursor, Codex, Windsurf…) y para cualquier persona que se incorpore.

Este archivo es la **fuente única**. [`CLAUDE.md`](./CLAUDE.md) lo importa; no se duplica contenido en él. Si un día cambiamos de herramienta, el contexto no se tira a la basura.

---

## 1. Qué es este repositorio

Monorepo del proyecto transversal de **AI Engineering** de 4Geeks Academy. Crece hito a hito durante 24 semanas construyendo **una sola empresa**, no ejercicios sueltos.

**Empresa activa: Nexova Solutions** — consultora B2B de recursos humanos y selección de talento. Valencia (España) + Miami (Florida), 120 empleados, tres líneas de negocio: headhunting, outsourcing de soporte al cliente y formación corporativa.

**Idioma de trabajo: español.** Documentación, comentarios, textos de interfaz y mensajes de commit en español. El código, los nombres de variables y las carpetas, en inglés.

---

## 2. Qué leer antes de tocar nada

En este orden, al empezar cada sesión:

| # | Archivo | Para qué |
| --- | --- | --- |
| 1 | [`memory-bank/projectbrief.md`](./memory-bank/projectbrief.md) | Qué es Nexova, quién pide qué y con qué palabras se nombra cada cosa |
| 2 | [`memory-bank/techContext.md`](./memory-bank/techContext.md) | Qué hay construido, con qué, qué decisiones ya están tomadas y qué no se toca |
| 3 | [`memory-bank/progress.md`](./memory-bank/progress.md) | Qué está entregado, qué está en curso y qué viene después |
| 4 | [`CONTEXT.md`](./CONTEXT.md) | Briefing de la empresa + **apéndice literal del hito en curso** |
| 5 | El `README.md` de la carpeta donde vas a escribir | Qué va ahí y cómo se ejecuta |

**`CONTEXT.md` manda.** Cuando un hito fija nombres de campo, valores de dominio o textos, se usan **literalmente**. Una implementación genérica que ignore el contexto no se acepta. Si el banco de memoria y `CONTEXT.md` se contradicen, gana `CONTEXT.md` y el banco de memoria se corrige en el acto.

> **`docs/contexts-archive/` no se lee ni se busca.** Contiene los contextos de las otras tres empresas del track (Brasaland, HealthCore, TrackFlow): 155 archivos que responden a casi cualquier búsqueda sobre el dominio y taparían los resultados de Nexova. Está en el [`.ignore`](./.ignore) de la raíz, pero la regla aplica aunque una herramienta no lo respete. Solo se consulta si la persona con la que trabajas lo pide explícitamente.

---

## 3. Dónde va cada cosa

Cada carpeta de primer nivel tiene una responsabilidad y su propio `README.md`. **Se lee antes de escribir código ahí.** Resumen en [`README.es.md`](./README.es.md).

`uis/` interfaces · `services/` API FastAPI central · `data/` datos y pipelines · `agents/` `skills/` `mcps/` IA · `workflows/` automatización · `packages/` `shared/` reutilización · `infra/` `scripts/` `internal/` operaciones · `docs/` documentación

Regla rápida: si tiene interfaz visual → `uis/`. Si expone una API o corre en segundo plano → `services/`. Si mueve o transforma datos → `data/`. Si el trabajo lo hace un modelo → `agents/`.

**No se dejan archivos de implementación en la raíz.**

### `.agents/` no es `/agents`

| Carpeta | Qué es |
| --- | --- |
| [`.agents/`](./.agents/) | **Configuración de las herramientas de desarrollo.** Reglas y skills que enseñan al agente de código cómo trabajar en este repositorio |
| [`agents/`](./agents/) · [`skills/`](./skills/) | **Producto.** Los agentes de IA y sus capacidades que Nexova usará en su negocio, a partir de hitos posteriores |

Confundirlas es el error clásico. Una configura la herramienta; la otra se vende.

### Qué no vive en este repositorio

Las notas de clase. Diego las lleva por su cuenta en Drive. Aquí solo va el proyecto de empresa.

---

## 4. Reglas de desarrollo

En [`.agents/rules/`](./.agents/rules/). Cada una declara su **ámbito de aplicación**, porque cargarlas todas siempre cuesta contexto y diluye la atención sobre lo que importa ahora:

| Regla | Ámbito |
| --- | --- |
| [`contexto-de-empresa.md`](./.agents/rules/contexto-de-empresa.md) | Siempre activa |
| [`idioma-y-documentacion.md`](./.agents/rules/idioma-y-documentacion.md) | Siempre activa |
| [`backoffice-nextjs.md`](./.agents/rules/backoffice-nextjs.md) | Archivos bajo `uis/backoffice/**` |
| [`web-publica.md`](./.agents/rules/web-publica.md) | Archivos bajo `uis/website/**` |
| [`commits-y-entrega.md`](./.agents/rules/commits-y-entrega.md) | A petición, al preparar un commit o una PR |

## 5. Skills disponibles

En [`.agents/skills/`](./.agents/skills/). Procedimientos con objetivo único, inputs definidos y **criterios de aceptación verificables**. Se invocan cuando la tarea encaja:

| Skill | Cuándo |
| --- | --- |
| [`actualizar-banco-de-memoria`](./.agents/skills/actualizar-banco-de-memoria/SKILL.md) | Al cerrar cualquier trabajo, antes del commit final (paso 3 del flujo) |
| [`verificar-etiquetas-de-dominio`](./.agents/skills/verificar-etiquetas-de-dominio/SKILL.md) | Al tocar cualquier interfaz que muestre datos de la API |

---

## 6. Flujo obligatorio antes de cada commit

**Los cinco pasos, en este orden, siempre.** Ningún agente escribe código en este repositorio sin pasar por aquí.

### Paso 1 — Leer el contexto

Los tres archivos de [`memory-bank/`](./memory-bank/), el apéndice del hito en curso en [`CONTEXT.md`](./CONTEXT.md) y el `README.md` de la carpeta que vas a tocar. Sin esto no se escribe la primera línea.

### Paso 2 — Verificar lo que has tocado

Desde la carpeta afectada. No hay runner en la raíz:

| Has tocado… | Ejecuta |
| --- | --- |
| `uis/backoffice/**` | `npm run typecheck` · `npm run lint` · `npm run build` |
| `uis/website/**` | `npm run build:css` y comprobar la página en el navegador |
| `uis/talent-lab/**` | `npm run build` |
| `packages/talent-core/**` | `npm run typecheck` · `npm test` |
| Cualquier interfaz que muestre datos de la API | La skill [`verificar-etiquetas-de-dominio`](./.agents/skills/verificar-etiquetas-de-dominio/SKILL.md) |

**En rojo no se commitea.** Si algo falla, se arregla o se para y se pregunta. No se commitea "para arreglarlo en el siguiente".

Las comprobaciones de `packages/talent-core/` y `uis/backoffice/` se repiten en CI sobre cada PR — ver [`.github/workflows/`](./.github/workflows/) —, pero se ejecutan antes en local: descubrir un fallo diez minutos después, en la PR, cuesta más que descubrirlo en el momento.

### Paso 3 — Actualizar el contexto

| Actualiza… | Cuando… |
| --- | --- |
| [`memory-bank/progress.md`](./memory-bank/progress.md) | **Siempre** que se cierra un trabajo o cambia el plan |
| [`memory-bank/techContext.md`](./memory-bank/techContext.md) | Cambia el stack, se mueve una carpeta o se toma una decisión de arquitectura |
| [`memory-bank/projectbrief.md`](./memory-bank/projectbrief.md) | Cambia el encargo o aparece vocabulario de dominio nuevo |
| El `README.md` de la carpeta | Cambian sus comandos, su estructura o lo que hace |

El procedimiento exacto está en la skill [`actualizar-banco-de-memoria`](./.agents/skills/actualizar-banco-de-memoria/SKILL.md).

### Paso 4 — Revisar el diff

```bash
git status --short
git diff --staged
```

Comprobar, una por una:

- **No entra nada generado ni pesado:** `node_modules/`, `.next/`, `packages/talent-core/dist/`, `*.tsbuildinfo`, `.env.local`.
- **No entran archivos ajenos al cambio.** Un commit, un cambio.
- Si se ha tocado `uis/website/src/input.css`, **`styles.css` está recompilado** y entra en el mismo commit.
- Los movimientos de archivos van en **su propio commit**, separados de los cambios de contenido. Un commit que mueve cuarenta archivos y además cambia código es imposible de revisar.

### Paso 5 — Commitear

En español, en imperativo, asunto de 72 caracteres o menos, sin punto final. El cuerpo explica **por qué**, no qué —el qué ya está en el diff—:

```
Mover el Talent Pipeline Tracker a uis/backoffice

La plantilla del monorepo reserva uis/backoffice para las aplicaciones
internas y uis/website para la web pública. Tener la herramienta en una
carpeta con nombre propio obligaba a explicar la excepción cada vez.
```

**Nunca se añaden firmas, coautorías ni atribuciones de IA** en commits ni en descripciones de PR. Los commits van a nombre de quien desarrolla.

---

## 7. Qué no se modifica sin confirmación explícita

Parar y preguntar antes de tocar cualquiera de estos:

| Ruta | Por qué |
| --- | --- |
| `CONTEXT.md` · `CONTEXT.es.md` | Es el briefing oficial de la empresa. Solo se actualiza su apéndice al cambiar de hito, y se copia **sin modificar** del contexto de origen |
| `docs/contexts/**` | Se sincroniza desde el syllabus con [`scripts/sync_contexts.py`](./scripts/sync_contexts.py). Editarlo a mano se pierde en la siguiente sincronización |
| `docs/contexts-archive/**` | Material de referencia de otras empresas. Ni se lee ni se edita |
| `.github/workflows/**` | Un error aquí rompe el despliegue a producción o la verificación de las PRs |
| `uis/website/styles.css` · `uis/talent-lab/styles.css` · `uis/talent-lab/dist/` | **Generados.** Se versionan para que los sitios estáticos funcionen al clonarlos, pero se editan recompilando, nunca a mano |
| `.env`, `.env.local` y cualquier archivo con credenciales | No se versionan ni se leen en voz alta |
| `package.json` · `package-lock.json` | Añadir una dependencia es una decisión de arquitectura, no un detalle de implementación |
| `uis/backoffice/AGENTS.md` | El bloque entre `BEGIN/END:nextjs-agent-rules` lo **regenera `next dev`**. Borrarlo solo lo hace reaparecer sucio en el diff |
| Cualquier carpeta de primer nivel nueva | La estructura del monorepo viene de la plantilla. Si algo no encaja en ninguna carpeta, se pregunta |

---

## 8. Cuándo detenerse y preguntar

Parar, exponer las opciones y esperar respuesta —no elegir por tu cuenta— cuando:

- **`CONTEXT.md` no define** un campo, un valor de dominio o un texto que hace falta. No se inventa vocabulario de negocio.
- El briefing es **ambiguo o se contradice** (por ejemplo, el responsable de Ventas aparece con dos nombres distintos).
- Hace falta **una dependencia nueva**, una carpeta de primer nivel nueva o cambiar la CI.
- El cambio afecta a **datos de personas**: candidaturas, notas internas, información de empleados.
- La tarea pide **borrar o reescribir** trabajo ya entregado en un hito anterior.
- Lo que se pide **contradice una decisión** ya registrada en [`techContext.md`](./memory-bank/techContext.md). Puede ser correcto cambiarla, pero se decide a la vista del porqué original, no por descuido.

---

## 9. Entrega

Una rama por hito, con nombre descriptivo en inglés (`feature/agent-memory-bank`). Al cerrar el hito: el flujo del punto 6 completo y una PR hacia `main` en español, explicando qué se entrega y qué decisiones se han tomado.

Las PRs de hitos anteriores se quedan abiertas para la evaluación del campus: por eso **cada rama nueva sale de la rama del hito anterior**, no de `main`.
