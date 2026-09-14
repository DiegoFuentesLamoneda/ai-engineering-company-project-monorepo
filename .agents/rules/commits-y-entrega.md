---
description: Convención de commits, ramas y pull requests de este repositorio. Se solicita al preparar un commit o cerrar un hito.
alwaysApply: false
---

# Commits y entrega

**Ámbito: a petición.** No se carga sola: el agente la solicita cuando va a preparar un commit, una rama o una pull request.

El flujo obligatorio previo (verificar, actualizar el banco de memoria, revisar el diff) está en [`AGENTS.md`](../../AGENTS.md), punto 6. Esta regla cubre solo el formato.

## Mensajes de commit

En **español**, en **imperativo**, asunto de 72 caracteres o menos y sin punto final. El cuerpo explica **por qué**, separado del asunto por una línea en blanco.

```
Mover el Talent Pipeline Tracker a uis/backoffice

La plantilla del monorepo reserva uis/backoffice para las aplicaciones
internas y uis/website para la web pública. Tenerlo en una carpeta con
nombre propio obligaba a explicar la excepción cada vez.
```

Así es como está escrito todo el historial de este repositorio: *"Añadir el Talent Pipeline Tracker del hito 3"*, *"Implementar el scoring, el ranking y los reportes de selección"*, *"Verificar talent-core en CI y actualizar el contexto al hito 2"*.

| ✅ | ❌ |
| --- | --- |
| `Añadir el panel de entrada del backoffice` | `cambios` |
| `Corregir el error 422 al crear una candidatura` | `fix bug` |
| `Documentar la API, el scoring y las decisiones de talent-core` | `Se han añadido varios archivos y se ha actualizado el README` |

**Nunca se añaden firmas, coautorías ni atribuciones de IA** — ni `Co-Authored-By`, ni pies de página en las PRs. Los commits van a nombre de quien desarrolla.

## Un commit, un cambio

- Los **movimientos de archivos** van en su propio commit, con `git mv` para conservar el historial, separados de los cambios de contenido. Un commit que mueve cuarenta archivos y además cambia código es imposible de revisar, y una PR imposible de revisar se aprueba sin mirar.
- Un artefacto generado entra con el cambio que lo genera (`src/input.css` y su `styles.css` recompilado, en el mismo commit).
- Si al preparar el commit aparecen cambios de otra cosa, se dejan fuera y se commitean aparte.

## Ramas

`feature/<nombre-en-inglés>`, una por hito: `feature/domain-models`, `feature/talent-pipeline-tracker`, `feature/agent-memory-bank`.

**Cada rama sale de la rama del hito anterior, no de `main`.** Las PRs de hitos previos siguen abiertas para la evaluación del campus, así que `main` va por detrás. Ramificar desde `main` dejaría fuera el trabajo sobre el que se construye.

## Pull requests

En español, con este contenido:

1. **Qué se entrega** — la lista de lo construido, enlazada a los archivos.
2. **Decisiones tomadas** — las que no se leen en el diff, con su porqué.
3. **Cómo probarlo** — comandos exactos, desde qué carpeta, y qué se debería ver.
4. **Capturas** — de toda interfaz que cambie. Quien evalúa no va a levantar el proyecto.

Sin pies de página generados ni plantillas vacías.

## Lo que no se hace nunca

- `git push --force` sobre `main` o sobre una rama con PR abierta.
- Saltarse los hooks con `--no-verify`. Si el hook de secretos salta, es que hay algo que mirar.
- Commitear con la verificación en rojo "para arreglarlo en el siguiente".
- Commitear `node_modules/`, `.next/`, `dist/` no versionado, `*.tsbuildinfo` o `.env.local`.
- Fusionar la propia PR sin que la haya visto quien evalúa.

## Cómo se verifica

Antes de dar por buena la entrega:

```bash
git status --short          # limpio, sin archivos sueltos
git diff --staged           # solo lo que corresponde a este commit
git log --oneline -5        # los mensajes siguen la convención
```
