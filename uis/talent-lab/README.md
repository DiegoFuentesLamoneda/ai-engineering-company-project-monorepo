# Banco de pruebas de `talent-core`

Herramienta interna para ejercitar a mano las funciones de [`@repo/talent-core`](../../packages/talent-core/). Parte **opcional** del hito 2 — el entregable evaluable es la librería; esto es la forma de verla funcionar sin leer código.

No es el producto para los consultores: eso llega en el hito 3. Aquí no hay más diseño que el necesario para que cada función se pueda disparar y ver su resultado.

## Ejecutar

Un solo comando desde la **raíz del repositorio**, sin instalar nada:

```bash
npx http-server uis/talent-lab -p 3000 -a 0.0.0.0
```

Y se abre en <http://localhost:3000>. En Codespaces, expón el puerto 3000 como **Public** en la pestaña *Ports*.

Funciona al clonar porque `dist/` y `styles.css` se versionan. Para regenerarlos tras tocar la librería o el HTML:

```bash
npm install     # solo la primera vez
npm run build   # compila el paquete a dist/ y el CSS a styles.css
```

## Qué se puede probar

| Panel | Funciones que dispara |
| ------ | ---------------------- |
| Filtrar | `filterCandidatesBySkills`, `filterCandidatesBySeniority`, `filterCandidatesByAvailability` — encadenadas |
| Ordenar | `sortCandidatesBySalary`, `sortCandidatesByExperience`, en ambos sentidos |
| Buscar | `findCandidateById`, `findCandidateByEmail` (lineales) y `binarySearchCandidateBySalary` |
| Rankear | `calculateCandidateScore` y `rankCandidatesForVacancy` contra cualquiera de las 4 vacantes |
| Reportes | `countCandidatesByStatus`, `groupCandidatesBySeniority`, `findTopSkills`, `calculateAverageSalary`, `calculateVacancyFillRate` |
| Validar | `validateCandidate` sobre una ficha correcta y otra rota a propósito |

La vista de búsqueda binaria pinta la lista ordenada completa y resalta el índice encontrado, que es la forma más rápida de ver por qué el algoritmo necesita esa precondición. Con un salario que no exista —por ejemplo 3333— se ve el `-1`.

## Archivos

| Archivo                          | Contenido                                                        |
| -------------------------------- | ----------------------------------------------------------------- |
| [`index.html`](./index.html)     | Controles y panel de resultados                                   |
| [`app.js`](./app.js)             | Solo cableado: lee los controles, llama al paquete y pinta        |
| [`tsconfig.json`](./tsconfig.json) | Compila `packages/talent-core` dentro de `dist/`                |
| `dist/`                          | **Generado** — la librería traducida a JavaScript                 |
| `styles.css`                     | **Generado por Tailwind — no editar a mano**                      |
| [`src/input.css`](./src/input.css) | Entrada del compilador: los tokens de marca de `uis/website`     |

## Decisiones de implementación

**`app.js` no tiene lógica de negocio.** Ni una comparación, ni un cálculo, ni un orden. Todo lo resuelve el paquete. Es la demostración de por qué el hito separa la capa lógica: esta página, la API de `services/` y la interfaz real de los consultores consumirán exactamente las mismas funciones.

**Tailwind compilado, no por CDN.** Misma decisión y mismos tokens que [`uis/website`](../website/README.md): el Play CDN descarga un compilador de ~120 KB y genera el CSS en el navegador.

**`dist/` se versiona.** Igual que `styles.css` en el sitio público: la página es estática y debe arrancar al clonar, con un solo comando y sin pasos de build. La salida de `packages/talent-core/` sí está en el `.gitignore`, porque ahí nadie la sirve.

**La librería se compila desde aquí, no se copia.** El [`tsconfig.json`](./tsconfig.json) hereda del paquete y solo cambia el destino, de modo que `dist/` no puede quedar desfasado respecto al código fuente ni divergir de lo que produce `npm run build` en el paquete.
