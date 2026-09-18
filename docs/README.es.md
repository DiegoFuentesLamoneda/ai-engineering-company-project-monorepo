# Carpeta `docs`

Esta carpeta contiene la **documentación transversal** del monorepo: guías de arquitectura, decisiones técnicas, convenciones, procesos, y cualquier material compartido entre aplicaciones, pipelines, agentes y workflows.

- **Propósito principal**: tener un punto único para la documentación “global” del proyecto (no específica de una sola app/agente).
- **Recomendación**: organiza la documentación por temas (arquitectura, despliegue, datos, seguridad, observabilidad, etc.) y mantén enlaces desde los READMEs de cada componente hacia estas guías.

## Qué hay aquí

| Documento | Qué es |
| --- | --- |
| [`ARCHITECTURE_PROPOSAL.md`](./ARCHITECTURE_PROPOSAL.md) | Propuesta de arquitectura del backend: patrón elegido, estructura de `services/nexova-api/`, organización de routers, convivencia de frontend y backend, decisiones técnicas y riesgos. Hito 5 |
| [`contexts/`](./contexts/) | Contextos del syllabus sincronizados con [`scripts/sync_contexts.py`](../scripts/sync_contexts.py). **No se editan a mano** |
| `contexts-archive/` | Contextos de las otras empresas del track. **Ni se lee ni se busca** — ver [`AGENTS.md`](../AGENTS.md) |
