# Proyecto transversal — AI Engineering (4Geeks Academy)

Monorepo que crece hito a hito durante 24 semanas construyendo **una sola empresa**.

- **Empresa activa: Nexova Solutions** — consultora B2B de RR. HH. y selección de talento. Valencia (España) + Miami (Florida), 120 empleados, tres líneas de negocio: headhunting, outsourcing de soporte al cliente y formación corporativa.
- **Idioma de trabajo: español.** Documentación, commits y comunicación en español; el código y los nombres de carpeta, en inglés.

## Contexto de empresa

| Necesitas                                | Ve a                                                            |
| ---------------------------------------- | --------------------------------------------------------------- |
| Datos de la empresa, dominio, hito activo | [`CONTEXT.es.md`](./CONTEXT.es.md) — fuente única de verdad      |
| La spec de un hito concreto              | [`docs/contexts/`](./docs/contexts/) — un archivo por hito       |
| Documentos de dominio (corpus RAG)       | [`docs/contexts/knowledge-base/`](./docs/contexts/knowledge-base/) |

**`CONTEXT.es.md` manda.** Cuando un hito fija nombres de campo, valores de dominio o textos, se recogen en su apéndice, y la implementación debe usarlos literalmente. Una implementación genérica que ignore el contexto no se acepta.

### docs/contexts-archive/ — no buscar aquí

Contiene los contextos de las **otras tres** empresas del track (Brasaland, HealthCore, TrackFlow), guardados solo como referencia de otros sectores. Son 155 archivos que responden a casi cualquier búsqueda sobre el dominio y taparían los resultados de Nexova.

**No lo incluyas en búsquedas, exploraciones ni lecturas de contexto salvo petición explícita del usuario.** Está en el [`.ignore`](./.ignore) de la raíz, pero la regla aplica igual aunque una herramienta no lo respete.

## Dónde va cada cosa

Cada carpeta de primer nivel tiene una responsabilidad y su propio `README.md`; léelo antes de escribir código ahí. Resumen en [`README.es.md`](./README.es.md).

`uis/` interfaces · `services/` API FastAPI central · `data/` datos y pipelines · `agents/` `skills/` `mcps/` IA · `workflows/` automatización · `packages/` `shared/` reutilización · `infra/` `scripts/` `internal/` operaciones · `docs/` documentación

No dejes archivos de implementación en la raíz.

Las notas de clase **no van en este repo**: Diego las lleva por su cuenta en Drive. Este repositorio es solo el proyecto de empresa.
