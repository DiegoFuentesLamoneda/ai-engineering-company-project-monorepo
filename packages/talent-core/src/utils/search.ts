/**
 * Búsquedas sobre la base de datos de talento.
 *
 * Dos estrategias, y la diferencia importa: la búsqueda lineal recorre el
 * array entero y sirve para cualquier orden (O(n)); la binaria descarta la
 * mitad en cada paso pero **exige** que el array llegue ya ordenado (O(log n)).
 * Aplicar la binaria a datos desordenados no da error: da resultados falsos.
 */

import type { Candidate } from "../types/models.js";

/**
 * Busca un candidato por su `id` recorriendo el array (búsqueda lineal).
 *
 * @param candidates Colección donde buscar, en cualquier orden.
 * @param id Identificador exacto (ej: "C-2024-0451").
 * @returns El candidato, o `null` si no está.
 */
export function findCandidateById(
  candidates: Candidate[],
  id: string,
): Candidate | null {
  throw new Error("Sin implementar: findCandidateById");
}

/**
 * Busca un candidato por su email recorriendo el array (búsqueda lineal).
 *
 * - La comparación es case-insensitive: nadie escribe su email igual dos veces.
 *
 * @param candidates Colección donde buscar, en cualquier orden.
 * @param email Email a localizar.
 * @returns El candidato, o `null` si no está.
 */
export function findCandidateByEmail(
  candidates: Candidate[],
  email: string,
): Candidate | null {
  throw new Error("Sin implementar: findCandidateByEmail");
}

/**
 * Busca el índice de un candidato por salario esperado (búsqueda binaria).
 *
 * - **Precondición:** `sortedCandidates` viene ordenado por `expectedSalary`
 *   ascendente. Ordénalo antes con `sortCandidatesBySalary(…, "asc")`.
 * - Si varios candidatos comparten salario, vale cualquier índice de ellos.
 * - Con el array vacío, o si el salario no está, devuelve `-1`.
 *
 * @param sortedCandidates Colección ordenada por salario esperado ascendente.
 * @param targetSalary Salario esperado a localizar.
 * @returns El índice dentro del array, o `-1` si no se encuentra.
 */
export function binarySearchCandidateBySalary(
  sortedCandidates: Candidate[],
  targetSalary: number,
): number {
  throw new Error("Sin implementar: binarySearchCandidateBySalary");
}
