/**
 * API pública de `@repo/talent-core`.
 *
 * Punto de entrada único del paquete: quien lo consume —el laboratorio web,
 * la API de `services/` en hitos posteriores— importa de aquí y no de rutas
 * internas, para que reorganizar `src/` no rompa a nadie.
 */
export * from "./types/models.js";
export * from "./utils/collections.js";
export * from "./utils/search.js";
export * from "./utils/transformations.js";
export * from "./utils/validations.js";
export * from "./data/samples.js";
