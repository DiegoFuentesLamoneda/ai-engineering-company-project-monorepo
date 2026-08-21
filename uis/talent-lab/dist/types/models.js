/**
 * Entidades de dominio de Nexova Solutions.
 *
 * Los nombres de campo y los valores de las uniones se copian literalmente de
 * `docs/contexts/02-coding-fundamentals.es.md`. No se traducen ni se renombran:
 * el ATS, la API de `services/` y los hitos siguientes hablan este vocabulario.
 */
// ---------------------------------------------------------------------------
// Escalas ordenadas
//
// El contexto define las uniones sin orden, pero el scoring necesita comparar
// "cumple o excede" (inglés) y "un nivel arriba o abajo" (seniority). Estas
// constantes fijan ese orden en un único sitio; el índice es la escala.
// ---------------------------------------------------------------------------
/** Niveles de inglés de menor a mayor competencia. */
export const ENGLISH_LEVELS = [
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
    "Native",
];
/** Niveles profesionales de menor a mayor responsabilidad. */
export const SENIORITY_LEVELS = [
    "Junior",
    "Semi-Senior",
    "Senior",
    "Lead",
    "Executive",
];
/** Todos los estados posibles de un candidato, para reportes exhaustivos. */
export const CANDIDATE_STATUSES = [
    "Active",
    "In process",
    "Hired",
    "Inactive",
];
/** Todas las disponibilidades posibles, para poblar filtros y selectores. */
export const AVAILABILITY_STATUSES = [
    "Immediate",
    "2 weeks",
    "1 month",
    "Not available",
];
