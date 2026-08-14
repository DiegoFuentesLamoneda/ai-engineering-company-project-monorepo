# Contextos de Nexova Solutions

Todo el material de contexto de la **empresa activa** de este proyecto transversal: el briefing, la especificación de cada hito, la base de conocimiento de dominio y los datos de partida.

Cada archivo viene del [syllabus de 4Geeks](https://github.com/4GeeksAcademy/ai-engineering-syllabus/tree/main/content/contexts) y se descarga con [`scripts/sync_contexts.py`](../../scripts/sync_contexts.py).

## Dónde buscar según lo que necesites

| Nivel                     | Ubicación                                        | Contenido                                                            |
| ------------------------- | ------------------------------------------------ | -------------------------------------------------------------------- |
| **Fuente de verdad**      | [`CONTEXT.md`](../../CONTEXT.md) (raíz del repo) | Briefing de Nexova + apéndice del hito en curso                       |
| **Trabajo diario**        | esta carpeta                                     | Los 13 contextos de hito, la base de conocimiento y los datos         |
| **Referencia ocasional**  | [`docs/contexts-archive/`](../contexts-archive/) | Las otras tres empresas del track (Brasaland, HealthCore, TrackFlow)  |

## Hitos

Cada hito tiene versión española (`.es.md`) e inglesa (`.en.md`).

| #      | Archivo                                                              | Hito                                             | Estado       |
| ------ | -------------------------------------------------------------------- | ------------------------------------------------ | ------------ |
| —      | [`00-briefing`](./00-briefing.es.md)                                  | Briefing de empresa                              | ✅ base      |
| 1      | [`01-web-fundamentals`](./01-web-fundamentals.es.md)                  | Sitio Web Público                                | 🔨 en curso  |
| 2      | [`02-coding-fundamentals`](./02-coding-fundamentals.es.md)            | Fundamentos de Programación                      | ⬜ pendiente |
| 3      | [`03-frontend-development`](./03-frontend-development.es.md)          | Talent Pipeline Tracker                          | ⬜ pendiente |
| 5      | [`05-backend-development`](./05-backend-development.es.md)            | Gestión de Inventario Backend                    | ⬜ pendiente |
| 6 · 1  | [`06a-telemetry`](./06a-telemetry.es.md)                              | Telemetría: plan, captura, almacenamiento, reporte | ⬜ pendiente |
| 6 · 2  | [`06b-data-pipelines`](./06b-data-pipelines.es.md)                    | Pipeline de desempeño de negocio                 | ⬜ pendiente |
| 7      | [`07-training-rag`](./07-training-rag.es.md)                          | RAG y base de conocimiento                       | ⬜ pendiente |
| 8 · 1  | [`08a-agent-memory`](./08a-agent-memory.es.md)                        | Memoria y auto-mejora de agentes                 | ⬜ pendiente |
| 8 · 2  | [`08b-agent-harnessing`](./08b-agent-harnessing.es.md)                | Harness y guardrails de agentes                  | ⬜ pendiente |
| 9      | [`09-agentic-workflows`](./09-agentic-workflows.es.md)                | Flujos de trabajo agénticos (partes 1, 2 y 3)    | ⬜ pendiente |
| 10 · 1 | [`10a-realtime-notification`](./10a-realtime-notification.es.md)      | Tiempo real: notificaciones                      | ⬜ pendiente |
| 10 · 2 | [`10b-realtime-communication`](./10b-realtime-communication.es.md)    | Tiempo real: comunicación                        | ⬜ pendiente |

> El hito 4 no existe en el syllabus; la numeración salta del 3 al 5. Se respeta el hueco para que coincida con la del curso.

## [`knowledge-base/`](./knowledge-base/) — documentos de dominio

Cuatro documentos internos de Nexova. **Son el corpus del hito 7 (RAG)** y la base de conocimiento del chatbot de soporte, no material de lectura.

| Documento                                                     | Contenido                                    |
| ------------------------------------------------------------- | -------------------------------------------- |
| [`service-lines`](./knowledge-base/service-lines.es.md)        | Detalle de las tres líneas de negocio        |
| [`pricing-model`](./knowledge-base/pricing-model.es.md)        | Modelo de precios y honorarios               |
| [`hiring-process-sla`](./knowledge-base/hiring-process-sla.es.md) | SLAs del proceso de selección             |
| [`objection-handling`](./knowledge-base/objection-handling.es.md) | Manejo de objeciones comerciales          |

## [`proyectos/`](./proyectos/) — contextos sin número de hito

Seis contextos que el syllabus publica fuera de la secuencia numerada. Algunos declaran su hito en la cabecera del propio archivo (por ejemplo, `supplier-directory` dice pertenecer al 09).

`centralized-incident-manager` · `cybersecurity-analysis` · `incidents-file-analysis` · `openclaw-onboarding-agent` · `sales-forecasting` · `supplier-directory`

## [`assets/`](./assets/) — datos de partida

| Archivo             | Usado por                                    |
| ------------------- | -------------------------------------------- |
| `sales.csv`         | `proyectos/sales-forecasting`                |
| `incidents.csv`     | `proyectos/incidents-file-analysis`          |
| `rfp-request-*.pdf` | `09-agentic-workflows` (3 solicitudes RFP)   |

Cuando un hito consuma de verdad estos datos, se copian a [`data/raw/`](../../data/raw/), que es su sitio según la guía del monorepo. Aquí viven solo como material de origen.

## Convenciones

- **El nombre del archivo es el hito.** No se repite `CONTEXT-nexova` en cada archivo, porque toda esta carpeta es Nexova.
- **Idioma siempre explícito:** `.es.md` / `.en.md`. En el origen el inglés unas veces es `.en.md` y otras `.md`; aquí se normaliza.
- **Sufijo `a`/`b` en los hitos partidos en dos**, para conservar el orden en que se cursan cuando no coincide con el alfabético (en el 8, la memoria es la Parte 1 y el harness la Parte 2).
- **`07-training-rag`** corrige el typo `07-trainning-rag` del origen.

## Volver a sincronizar

```bash
python scripts/sync_contexts.py --dry-run   # ver el plan sin escribir
python scripts/sync_contexts.py             # descargar y colocar
python scripts/sync_contexts.py --only nexova
```

El script no borra nada y no toca los README escritos a mano. Si el syllabus publica un hito nuevo que aún no está en su tabla de mapeo, avisa por consola y lo coloca con el nombre de la carpeta de origen.
