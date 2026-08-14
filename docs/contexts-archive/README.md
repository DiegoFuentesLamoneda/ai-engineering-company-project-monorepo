# Archivo — contextos de las otras empresas

Material de referencia de las **tres empresas que este proyecto no usa**. Se guarda para poder consultar cómo se plantea un mismo hito en otro sector: el hito de RAG no se parece en una clínica y en una empresa de última milla, y comparar es la forma rápida de ver qué parte del planteamiento es del dominio y qué parte es del hito.

> ⚠️ **Esto no es contexto de trabajo.** La empresa activa es Nexova y su material está en [`docs/contexts/`](../contexts/).

| Empresa                              | Sector                                        | País                  |
| ------------------------------------ | --------------------------------------------- | --------------------- |
| [`brasaland/`](./brasaland/)         | Restaurantes a la parrilla                    | Colombia + Florida    |
| [`healthcore/`](./healthcore/)       | Red de clínicas ambulatorias                  | EE. UU. + Reino Unido |
| [`trackflow/`](./trackflow/)         | Última milla y almacén                        | México + España       |

Cada carpeta sigue exactamente la misma convención de nombres que `docs/contexts/`, así que el mismo hito se encuentra en el mismo archivo en las cuatro empresas:

```
docs/contexts/01-web-fundamentals.es.md                      <- Nexova
docs/contexts-archive/healthcore/01-web-fundamentals.es.md   <- el mismo hito, en una clínica
```

`_upstream-README.{es,en}.md` son los README originales del syllabus, guardados tal cual.

## Excluido de las búsquedas

Esta carpeta está listada en el [`.ignore`](../../.ignore) de la raíz, así que **las búsquedas amplias la saltan**. No está en `.gitignore`: los archivos sí se versionan y se suben, solo que no aparecen al buscar. Es deliberado — son 155 archivos que contestarían a casi cualquier búsqueda sobre el dominio y taparían los resultados de Nexova.

Buscar dentro no necesita ningún flag: basta con apuntar a la carpeta, porque ripgrep no aplica las reglas de ignore a la ruta que le das explícitamente.

```bash
rg "patrón" .                        # no encuentra nada de aquí
rg "patrón" docs/contexts-archive/   # sí lo encuentra
```

Y si trabajas con Claude Code, basta con pedirlo de forma explícita ("busca en el archivo de otras empresas...").

## Actualizar

```bash
python scripts/sync_contexts.py --only healthcore
```

Sin `--only` sincroniza las cuatro empresas de golpe.
