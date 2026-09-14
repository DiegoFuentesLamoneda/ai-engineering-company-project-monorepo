---
name: actualizar-banco-de-memoria
description: Deja memory-bank/ reflejando el estado real del repositorio antes del commit que cierra un trabajo. Úsala en el paso 3 del flujo de AGENTS.md, siempre que se termine un entregable, se tome una decisión de arquitectura o cambie el plan.
---

# Skill · Actualizar el banco de memoria

## Objetivo

**Uno solo:** que [`memory-bank/`](../../../memory-bank/) describa el repositorio tal y como queda después de este trabajo — ni antes, ni como se espera que quede algún día.

Un banco de memoria desfasado es peor que no tenerlo: el agente actúa con confianza sobre información falsa. Por eso esto no es un checklist aparte, sino el **paso 3 del flujo obligatorio** de [`AGENTS.md`](../../../AGENTS.md).

## Cuándo se usa

- Al cerrar un entregable, antes del commit final.
- Al tomar una decisión de arquitectura, aunque no haya código.
- Al mover, crear o eliminar una carpeta.
- Al añadir o quitar una dependencia.
- Al detectar deuda técnica o una ambigüedad del briefing.

**No se usa** para cambios que no alteran el estado del proyecto: una corrección de una errata, un ajuste de estilos, un renombrado interno.

## Inputs

| Input | Obligatorio | De dónde sale |
| --- | --- | --- |
| Descripción del trabajo cerrado | Sí | La tarea que se acaba de terminar |
| Archivos tocados | Sí | `git status --short` y `git diff --stat` |
| Hito en curso | Sí | [`progress.md`](../../../memory-bank/progress.md) y el apéndice de [`CONTEXT.md`](../../../CONTEXT.md) |
| Decisiones tomadas y su porqué | Si las hay | La conversación de trabajo |
| Fecha de hoy | Sí | Del sistema |

## Procedimiento

### 1. Reunir los hechos

```bash
git status --short
git diff --stat
git log --oneline -5
```

No se escribe nada de memoria: se mira lo que hay.

### 2. Decidir qué archivo hay que tocar

| Si el trabajo… | Actualiza |
| --- | --- |
| Cierra un entregable, cambia el plan o descubre deuda técnica | `progress.md` — **siempre** |
| Añade o quita una dependencia, mueve o crea una carpeta, fija una decisión de arquitectura, cambia un comando | `techContext.md` |
| Aporta vocabulario de dominio nuevo, cambia el encargo o revela una ambigüedad del briefing | `projectbrief.md` |
| Cambia los comandos, la estructura o el propósito de un proyecto | El `README.md` de esa carpeta |

Si ninguna fila aplica, la skill termina aquí: no se toca el banco de memoria por inercia.

### 3. Actualizar `progress.md`

- Mover lo terminado de ⬜ a ✅, o de "En curso" a "Entregado" con su rama y su PR.
- Poner la fecha de hoy en _Última actualización_.
- Añadir a **Deuda técnica** lo que se haya quedado a medias, con una frase de por qué.
- Revisar **Próximo**: si el plan ha cambiado, se cambia aquí.

### 4. Actualizar `techContext.md` si procede

- Toda decisión nueva se escribe **con su porqué**, no solo con su qué. El porqué es lo que impide que alguien la revierta por descuido dentro de tres meses.
- Las tablas de rutas, versiones y comandos reflejan la realidad después del cambio.
- Si algo pasa a ser un artefacto generado, entra en la lista de "no se edita a mano".

### 5. Actualizar `projectbrief.md` si procede

- El vocabulario nuevo va al glosario.
- Las ambigüedades del briefing se **anotan**, no se resuelven por cuenta propia.

### 6. Releer buscando contradicciones

Contra [`CONTEXT.md`](../../../CONTEXT.md) y contra los otros dos archivos del banco. Si algo choca, gana `CONTEXT.md`.

### 7. Commitear junto al cambio que lo motiva

El diff del banco de memoria va **en el mismo commit** que el trabajo que describe. En un commit aparte, se olvida.

## Criterios de aceptación

Se comprueban uno a uno. Si alguno falla, la skill no ha terminado.

- [ ] `progress.md` lleva la **fecha de hoy** en _Última actualización_.
- [ ] Todo lo marcado como entregado tiene su commit en `git log`. Nada se marca ✅ "por adelantado".
- [ ] Toda dependencia, carpeta o comando nuevo aparece en `techContext.md`.
- [ ] Toda decisión registrada incluye **su porqué**, no solo la decisión.
- [ ] **Ninguna ruta enlazada desde `memory-bank/` está rota.** Verificable:

```bash
cd memory-bank
grep -oE '\]\([^)]+\)' *.md \
  | sed -E 's/.*\]\(([^)#]+).*/\1/' \
  | grep -v '^http' | sort -u \
  | while read -r ruta; do [ -e "$ruta" ] || echo "ENLACE ROTO: $ruta"; done
```

  Sin salida = correcto.

- [ ] Ninguna afirmación del banco contradice a `CONTEXT.md`.
- [ ] El diff de `memory-bank/` entra en el mismo commit que el trabajo que describe.

## Qué NO hace esta skill

- No documenta **cómo** se ejecuta o se estructura un proyecto: eso va en el `README.md` de ese proyecto.
- No copia la especificación del hito: esa vive en `CONTEXT.md` y en `docs/contexts/`.
- No acumula histórico. El banco de memoria dice **cómo están las cosas ahora**; lo que pasó está en `git log`.
- No amplía el alcance del trabajo. Si al actualizar aparece un problema, se anota como deuda técnica y se sigue.
