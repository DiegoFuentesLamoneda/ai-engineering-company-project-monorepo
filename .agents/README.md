# Carpeta `.agents`

Configuración de las **herramientas de desarrollo asistido** de este repositorio: las reglas y las skills que enseñan a un agente de código cómo trabajar aquí sin romper lo ya construido.

El protocolo general está en [`AGENTS.md`](../AGENTS.md). Esta carpeta guarda el detalle.

```
.agents/
├─ rules/    Convenciones que el agente respeta, cada una con su ámbito
└─ skills/   Procedimientos con inputs y criterios de aceptación verificables
```

## `.agents/` no es `/agents`

| Carpeta | Qué es |
| --- | --- |
| `.agents/` | **Herramienta.** Cómo trabaja el agente de código que nos ayuda a programar |
| [`agents/`](../agents/) · [`skills/`](../skills/) | **Producto.** Los agentes de IA que Nexova usará en su negocio, a partir de hitos posteriores |

## Reglas

Una regla es una convención que el agente debe respetar. Cada una **declara su ámbito** en el frontmatter, porque cargarlas todas en cada sesión cuesta contexto y diluye la atención sobre lo que importa ahora:

| Ámbito | Frontmatter | Cuándo se carga |
| --- | --- | --- |
| Siempre activa | `alwaysApply: true` | En toda sesión, sin excepción |
| Por patrón de archivo | `globs: [...]` | Solo al tocar archivos que encajan con el patrón |
| A petición | `alwaysApply: false` y sin `globs` | Cuando el agente la solicita porque la tarea lo pide |

| Regla | Ámbito |
| --- | --- |
| [`contexto-de-empresa.md`](./rules/contexto-de-empresa.md) | Siempre activa |
| [`idioma-y-documentacion.md`](./rules/idioma-y-documentacion.md) | Siempre activa |
| [`backoffice-nextjs.md`](./rules/backoffice-nextjs.md) | `uis/backoffice/**` |
| [`web-publica.md`](./rules/web-publica.md) | `uis/website/**` |
| [`commits-y-entrega.md`](./rules/commits-y-entrega.md) | A petición |

## Skills

Una skill es un **procedimiento**, no una convención: tiene un objetivo único, inputs definidos, una secuencia de pasos y criterios de aceptación que se pueden comprobar. Si el resultado no se puede verificar, no es una skill.

| Skill | Objetivo |
| --- | --- |
| [`actualizar-banco-de-memoria`](./skills/actualizar-banco-de-memoria/SKILL.md) | Dejar `memory-bank/` al día antes del commit que cierra un trabajo |
| [`verificar-etiquetas-de-dominio`](./skills/verificar-etiquetas-de-dominio/SKILL.md) | Garantizar que ningún valor crudo de la API llega a la interfaz |

## Formato

Las claves del frontmatter (`description`, `globs`, `alwaysApply`) van en inglés porque las leen las herramientas; el contenido, en español, como el resto de la documentación del repositorio.
