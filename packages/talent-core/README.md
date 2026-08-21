# `@repo/talent-core`

Entregable del **hito 2 — Fundamentos de Programación**. Librería TypeScript con la lógica de scoring de candidatos y matching de vacantes de Nexova: filtros, búsquedas, puntuación, ranking, reportes y validaciones de negocio.

Sin dependencias de runtime y sin estado: todo son funciones puras sobre los datos que reciben. La consumirán el laboratorio de pruebas, la API de [`services/`](../../services/) y la interfaz de los consultores en hitos posteriores.

Especificación de referencia: [`CONTEXT.md`](../../CONTEXT.md) (apéndice del hito) y su original en [`docs/contexts/02-coding-fundamentals.es.md`](../../docs/contexts/02-coding-fundamentals.es.md).

## Comandos

```bash
npm install        # solo la primera vez

npm run typecheck  # tsc --noEmit — ni un error de tipos
npm test           # 103 pruebas con el runner de Node
npm run test:watch # las mismas, relanzadas al guardar
npm run demo       # recorrido por consola de toda la API
npm run build      # compila a dist/ como ESM cargable en el navegador
```

Para probarlo a mano hay un banco de pruebas web en [`uis/talent-lab/`](../../uis/talent-lab/), que dispara las 18 funciones desde botones. Se sirve con un solo comando desde la raíz del repositorio:

```bash
npx http-server uis/talent-lab -p 3000 -a 0.0.0.0
```

## Estructura

| Archivo                                                | Contenido                                                           |
| ------------------------------------------------------ | ------------------------------------------------------------------- |
| [`src/types/models.ts`](./src/types/models.ts)         | Interfaces, uniones del dominio y escalas ordenadas                 |
| [`src/utils/collections.ts`](./src/utils/collections.ts) | Filtros y ordenaciones                                              |
| [`src/utils/search.ts`](./src/utils/search.ts)         | Búsqueda lineal y binaria                                           |
| [`src/utils/transformations.ts`](./src/utils/transformations.ts) | Scoring, ranking, agrupaciones y reportes                  |
| [`src/utils/validations.ts`](./src/utils/validations.ts) | Reglas de negocio previas al procesamiento                          |
| [`src/data/samples.ts`](./src/data/samples.ts)         | 12 candidatos, 4 vacantes y 12 procesos de ejemplo                  |
| [`src/index.ts`](./src/index.ts)                       | API pública — importa siempre desde aquí                            |
| `src/testing/`                                          | Fábricas de datos para las pruebas; fuera de `dist/`                |

## API

### Entidades

`Candidate`, `Vacancy` y `SelectionProcess`, con las uniones `EnglishLevel`, `SeniorityLevel`, `AvailabilityStatus`, `CandidateStatus`, `VacancyStatus` y `ProcessStage`. Nombres de campo y valores **literales** del contexto: el ATS y la API hablan este vocabulario y traducirlo aquí obligaría a traducirlo en toda la cadena.

Las escalas `ENGLISH_LEVELS` y `SENIORITY_LEVELS` fijan el orden de esos niveles en un único sitio; el scoring compara por su índice.

### Colecciones

| Función                                                    | Qué hace                                              |
| ---------------------------------------------------------- | ----------------------------------------------------- |
| `filterCandidatesBySkills(candidates, requiredSkills)`     | Quienes tienen **todas** las habilidades pedidas      |
| `filterCandidatesBySeniority(candidates, seniority)`       | Quienes están en ese nivel                            |
| `filterCandidatesByAvailability(candidates, availability)` | Quienes encajan con **alguno** de esos estados        |
| `sortCandidatesBySalary(candidates, order)`                | Ordenados por `expectedSalary`                        |
| `sortCandidatesByExperience(candidates, order)`            | Ordenados por `yearsOfExperience`                     |
| `normalizeSkill(skill)`                                    | La definición única de "misma habilidad" del paquete  |

### Búsquedas

| Función                                                       | Estrategia | Devuelve                    |
| ------------------------------------------------------------- | ---------- | --------------------------- |
| `findCandidateById(candidates, id)`                           | Lineal     | El candidato o `null`       |
| `findCandidateByEmail(candidates, email)`                     | Lineal     | El candidato o `null`       |
| `binarySearchCandidateBySalary(sortedCandidates, targetSalary)` | Binaria  | El índice o `-1`            |

La binaria **exige** el array ya ordenado por `expectedSalary` ascendente. Sobre datos desordenados no falla: devuelve resultados falsos, que es peor.

### Scoring y reportes

| Función                                          | Qué hace                                                    |
| ------------------------------------------------ | ----------------------------------------------------------- |
| `calculateCandidateScore(candidate, vacancy)`    | Encaje de 0 a 100                                           |
| `rankCandidatesForVacancy(candidates, vacancy)`  | `{ candidate, score }` de mejor a peor                      |
| `groupCandidatesBySeniority(candidates)`         | Los cinco niveles como claves, siempre                      |
| `countCandidatesByStatus(candidates)`            | Los cuatro estados como claves, siempre                     |
| `calculateAverageSalary(candidates)`             | Media de `expectedSalary`, 2 decimales                      |
| `findTopSkills(candidates, topN)`                | Las N habilidades más frecuentes                            |
| `calculateVacancyFillRate(processes)`            | Porcentaje de procesos en `"Hired"`, 2 decimales            |

### Validaciones

`validateCandidate` y `validateVacancy` devuelven `{ valid, errors }` con **todos** los errores acumulados, no solo el primero: el consultor necesita ver de una vez todo lo que le falta a la ficha. `isValidEmail` es la comprobación básica que pide el contexto.

## Cómo puntúa

Cinco bloques que suman exactamente 100:

| Bloque       | Máx | Cómo se reparte                                                                   |
| ------------ | --- | --------------------------------------------------------------------------------- |
| Habilidades  | 40  | 40 todas las requeridas · 20 al menos la mitad · +10 por preferida (hasta 20)     |
| Experiencia  | 20  | 20 dentro del rango · 10 si se sale 1-2 años · 0 más allá                         |
| Seniority    | 15  | 15 exacto · 7 un nivel arriba o abajo · 0 más lejos                               |
| Inglés       | 15  | 15 si iguala o supera el nivel pedido · 0 si no llega                             |
| Salario      | 10  | 10 si no pasa del máximo · 5 hasta un 20 % por encima · 0 más allá                |

Carolina Silva contra la vacante del enunciado saca 100; María González, 92; Juan Pérez, 20.

## Decisiones de implementación

**El bloque de habilidades se capa a 40.** El enunciado titula el bloque "40 puntos máx" pero luego reparte hasta 40 por las requeridas más 20 por las preferidas: 60, que llevaría el total a 120 sobre 100. Se aplica `min(40, requeridas + preferidas)`, que respeta el titular y deja el máximo global en 100 exacto. La alternativa —sumar hasta 120 y recortar el total a 100— haría que muchos candidatos buenos saturaran en 100 y el ranking perdería resolución justo donde más se necesita.

**Los tramos de habilidades requeridas no se acumulan.** Tener todas vale 40, no 40 + 20: el segundo tramo describe el caso de tenerlas a medias.

**Pedir menos del mínimo no penaliza.** El enunciado solo contempla salarios *por encima* del rango. Un candidato que pide menos del mínimo no es un problema para el cliente, así que puntúa igual que uno dentro del rango.

**Los `Record` de los reportes son totales.** `groupCandidatesBySeniority` y `countCandidatesByStatus` devuelven siempre todas las claves, con `[]` o `0` las vacías. Un reporte con claves ausentes obliga a comprobar `undefined` en cada punto de consumo.

**Los desempates son deterministas.** `findTopSkills` desempata alfabéticamente por la habilidad normalizada; `rankCandidatesForVacancy` conserva el orden de entrada. Sin esto, dos ejecuciones con los mismos datos podrían dar reportes distintos.

**El matching de habilidades es case-insensitive en todo el paquete.** `normalizeSkill` es la única definición de "misma habilidad", y la comparten los filtros, el scoring y los reportes. Los datos reales llegan del ATS con mayúsculas inconsistentes.

**Los mensajes de error van en español y citan el campo en inglés.** Los leen los consultores, pero `yearsOfExperience` es el nombre real del campo y buscarlo en el código tiene que ser inmediato.

**Los datos de ejemplo son deterministas.** Fechas fijas, nada de `new Date()` ni de aleatoriedad, para poder comparar la salida entre ejecuciones.

## Desviaciones respecto al enunciado

| Enunciado                                                    | En el paquete                                        | Motivo                                                                       |
| ------------------------------------------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------- |
| Bloque de habilidades: "40 máx", pero reparte hasta 60       | Capado a 40                                          | El original sumaría 120 sobre 100                                            |
| Salario: solo define qué pasa por encima del rango           | Por debajo del mínimo puntúa 10                      | Pedir menos no perjudica al cliente                                          |
| Teléfonos de los tres candidatos de ejemplo con prefijo `+56` | Se mantienen literales; los añadidos usan `+34` / `+1` | Nexova opera en España y EE. UU., pero los datos del enunciado no se tocan |
| Firmas con la forma del retorno en línea                     | Interfaces con nombre (`ScoredCandidate`, …)         | Estructuralmente idénticas y el código se lee mejor                          |
| La versión inglesa del contexto sitúa el rol en el "TrackFlow Tech Team" | "Nexova AI Team", como en la versión española | TrackFlow es otra empresa del track; es un descuido del original |

Se mantienen **literales** los nombres de las 18 funciones y de sus parámetros, todos los campos de las tres entidades, los valores de las seis uniones, las reglas de validación, los tres candidatos y la vacante de ejemplo.

## Pruebas

**103 pruebas** con el runner de Node (`node:test`), sin framework externo. Un archivo por utilidad, junto al código que prueban.

Además de los casos normales, cubren lo que suele romperse: colecciones vacías, elementos no encontrados, `topN` a cero o negativo, búsqueda binaria sobre 0 y 1 elementos y con salarios repetidos, ambos extremos de cada tramo del scoring —incluido el 20 % exacto por encima del máximo salarial— y la comprobación de que ni los filtros ni las ordenaciones modifican el array que reciben.

Las fábricas de [`src/testing/factories.ts`](./src/testing/factories.ts) construyen entidades válidas y dejan sobrescribir solo el campo que se está probando: un test que repite los quince campos esconde lo único que importa.

## Rigor de tipos

El [`tsconfig.json`](./tsconfig.json) va más allá de `strict`. Dos opciones que cambian cómo se escribe el código:

- **`noUncheckedIndexedAccess`** — `array[i]` es `T | undefined`. Obliga a tratar el caso del índice fuera de rango, que es exactamente donde se rompen las búsquedas binarias.
- **`verbatimModuleSyntax`** — los tipos se importan con `import type`. Deja explícito qué desaparece al compilar.

Los imports relativos llevan extensión `.js` porque el paquete es ESM real: así la salida de `tsc` se carga tal cual en el navegador, sin bundler.
