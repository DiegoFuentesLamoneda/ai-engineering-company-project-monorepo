/**
 * Operaciones sobre colecciones de candidatos: filtrar y ordenar.
 *
 * Todas las funciones de este archivo son puras: reciben un array, devuelven
 * uno nuevo y **nunca** modifican el que reciben. Ojo con `Array.prototype.sort`,
 * que ordena in situ — hay que copiar antes.
 */

import type {
  AvailabilityStatus,
  Candidate,
  SeniorityLevel,
  SortOrder,
} from "../types/models.js";

/**
 * Lleva una habilidad a su forma comparable.
 *
 * El contexto exige que el matching de habilidades sea case-insensitive, y
 * los datos reales llegan del ATS con mayúsculas inconsistentes y espacios de
 * más. Esta es la única definición de "misma habilidad" del paquete: la
 * reutilizan `search.ts` y `transformations.ts` para no discrepar entre sí.
 */
export function normalizeSkill(skill: string): string {
  return skill.trim().toLowerCase();
}

/**
 * Candidatos que tienen **todas** las habilidades requeridas.
 *
 * - El matching es case-insensitive (usa `normalizeSkill`).
 * - Con `requiredSkills` vacío no hay nada que exigir: devuelve todos.
 *
 * @param candidates Colección a filtrar; no se modifica.
 * @param requiredSkills Habilidades que el candidato debe tener todas.
 * @returns Un array nuevo con los candidatos que cumplen.
 */
export function filterCandidatesBySkills(
  candidates: Candidate[],
  requiredSkills: string[],
): Candidate[] {
  const required = requiredSkills.map(normalizeSkill);

  return candidates.filter((candidate) => {
    const owned = candidate.skills.map(normalizeSkill);
    return required.every((skill) => owned.includes(skill));
  });
}

/**
 * Candidatos con el nivel de seniority indicado.
 *
 * @param candidates Colección a filtrar; no se modifica.
 * @param seniority Nivel exacto que se busca.
 * @returns Un array nuevo con los candidatos de ese nivel.
 */
export function filterCandidatesBySeniority(
  candidates: Candidate[],
  seniority: SeniorityLevel,
): Candidate[] {
  return candidates.filter((candidate) => candidate.seniority === seniority);
}

/**
 * Candidatos cuya disponibilidad coincide con **alguno** de los estados dados.
 *
 * - Con `availability` vacío no hay ningún estado aceptable: devuelve vacío.
 *
 * @param candidates Colección a filtrar; no se modifica.
 * @param availability Estados de disponibilidad aceptables.
 * @returns Un array nuevo con los candidatos que encajan.
 */
export function filterCandidatesByAvailability(
  candidates: Candidate[],
  availability: AvailabilityStatus[],
): Candidate[] {
  return candidates.filter((candidate) => availability.includes(candidate.availability));
}

/**
 * Candidatos ordenados por salario esperado (`expectedSalary`).
 *
 * @param candidates Colección a ordenar; **no se modifica**.
 * @param order `"asc"` de menor a mayor, `"desc"` de mayor a menor.
 * @returns Un array nuevo ordenado.
 */
export function sortCandidatesBySalary(
  candidates: Candidate[],
  order: SortOrder,
): Candidate[] {
  return candidates.slice().sort((a, b) => {
    if (order === "asc") {
      return a.expectedSalary - b.expectedSalary;
    } else {
      return b.expectedSalary - a.expectedSalary;
    }
  });
}

/**
 * Candidatos ordenados por años de experiencia (`yearsOfExperience`).
 *
 * @param candidates Colección a ordenar; **no se modifica**.
 * @param order `"asc"` de menor a mayor, `"desc"` de mayor a menor.
 * @returns Un array nuevo ordenado.
 */
export function sortCandidatesByExperience(
  candidates: Candidate[],
  order: SortOrder,
): Candidate[] {
  return candidates.slice().sort((a, b) => {
    if (order === "asc") {
      return a.yearsOfExperience - b.yearsOfExperience;
    } else {
      return b.yearsOfExperience - a.yearsOfExperience;
    }
  });
}
