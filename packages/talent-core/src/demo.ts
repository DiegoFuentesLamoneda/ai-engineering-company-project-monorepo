/**
 * Recorrido por consola de toda la API de `talent-core`.
 *
 * Ejecuta las 18 funciones sobre los datos de ejemplo y enseña el resultado.
 * Sirve como comprobación rápida a ojo de que el paquete hace lo que dice y
 * como documentación viva de cómo se usa cada función.
 *
 *     npm run demo
 */

import { sampleCandidates, sampleProcesses, sampleVacancies } from "./data/samples.js";
import {
  filterCandidatesByAvailability,
  filterCandidatesBySeniority,
  filterCandidatesBySkills,
  sortCandidatesByExperience,
  sortCandidatesBySalary,
} from "./utils/collections.js";
import {
  binarySearchCandidateBySalary,
  findCandidateByEmail,
  findCandidateById,
} from "./utils/search.js";
import {
  calculateAverageSalary,
  calculateCandidateScore,
  calculateVacancyFillRate,
  countCandidatesByStatus,
  findTopSkills,
  groupCandidatesBySeniority,
  rankCandidatesForVacancy,
} from "./utils/transformations.js";
import { validateCandidate, validateVacancy } from "./utils/validations.js";

function section(title: string): void {
  console.log(`\n${"─".repeat(72)}\n${title}\n${"─".repeat(72)}`);
}

/** Nombres, para no volcar fichas enteras en la consola. */
const names = (candidates: { fullName: string }[]): string =>
  candidates.map((c) => c.fullName).join(" · ") || "(ninguno)";

const vacancy = sampleVacancies[0];
if (vacancy === undefined) throw new Error("No hay vacantes de ejemplo");

console.log(
  `\nNexova · talent-core — ${sampleCandidates.length} candidatos, ` +
    `${sampleVacancies.length} vacantes, ${sampleProcesses.length} procesos`,
);

// ---------------------------------------------------------------------------
section("1 · Filtros");

console.log(
  "Con TypeScript y Node.js:      ",
  names(filterCandidatesBySkills(sampleCandidates, ["TypeScript", "Node.js"])),
);
console.log(
  "Senior:                        ",
  names(filterCandidatesBySeniority(sampleCandidates, "Senior")),
);
console.log(
  "Disponibles ya o en 2 semanas: ",
  names(filterCandidatesByAvailability(sampleCandidates, ["Immediate", "2 weeks"])),
);

// ---------------------------------------------------------------------------
section("2 · Ordenaciones");

console.table(
  sortCandidatesBySalary(sampleCandidates, "desc")
    .slice(0, 5)
    .map((c) => ({ Candidato: c.fullName, "Salario esperado": c.expectedSalary })),
);
console.table(
  sortCandidatesByExperience(sampleCandidates, "asc")
    .slice(0, 5)
    .map((c) => ({ Candidato: c.fullName, Años: c.yearsOfExperience })),
);

// ---------------------------------------------------------------------------
section("3 · Búsquedas");

console.log("Lineal por id C-2024-0453:     ", findCandidateById(sampleCandidates, "C-2024-0453")?.fullName);
console.log("Lineal por email (mayúsculas): ", findCandidateByEmail(sampleCandidates, "CAROLINA.SILVA@EMAIL.COM")?.fullName);
console.log("Lineal por id inexistente:     ", findCandidateById(sampleCandidates, "C-9999-9999"));

// La binaria exige el array ordenado por salario esperado ascendente.
const bySalary = sortCandidatesBySalary(sampleCandidates, "asc");
console.log("\nOrden para la búsqueda binaria:", bySalary.map((c) => c.expectedSalary).join(", "));
console.log("Índice del salario 6500:       ", binarySearchCandidateBySalary(bySalary, 6500));
console.log("Índice del salario 2000:       ", binarySearchCandidateBySalary(bySalary, 2000));
console.log("Índice de un salario que no está:", binarySearchCandidateBySalary(bySalary, 3333));

// ---------------------------------------------------------------------------
section(`4 · Scoring contra ${vacancy.id} — ${vacancy.title} (${vacancy.companyName})`);

console.log(
  `Pide ${vacancy.requiredSkills.join(", ")} · ${vacancy.minYearsExperience}-${vacancy.maxYearsExperience} años · ` +
    `${vacancy.requiredEnglishLevel} · ${vacancy.requiredSeniority} · ` +
    `${vacancy.salaryRangeMin}-${vacancy.salaryRangeMax} USD\n`,
);

const carolina = findCandidateById(sampleCandidates, "C-2024-0453");
if (carolina !== null) {
  console.log(
    `Puntuación de ${carolina.fullName}: ${calculateCandidateScore(carolina, vacancy)}\n`,
  );
}

console.table(
  rankCandidatesForVacancy(sampleCandidates, vacancy)
    .slice(0, 6)
    .map(({ candidate, score }, index) => ({
      "#": index + 1,
      Candidato: candidate.fullName,
      Puntuación: score,
      Seniority: candidate.seniority,
      Inglés: candidate.englishLevel,
      Pide: candidate.expectedSalary,
    })),
);

// ---------------------------------------------------------------------------
section("5 · Reportes");

console.log("Candidatos por estado:");
console.table(countCandidatesByStatus(sampleCandidates));

console.log("Candidatos por seniority:");
console.table(
  Object.entries(groupCandidatesBySeniority(sampleCandidates)).map(([nivel, lista]) => ({
    Nivel: nivel,
    Candidatos: lista.length,
    Quiénes: names(lista),
  })),
);

console.log("Habilidades más frecuentes:");
console.table(findTopSkills(sampleCandidates, 5));

console.log(`Salario esperado medio:     ${calculateAverageSalary(sampleCandidates)} USD`);
console.log(`Tasa de cobertura:          ${calculateVacancyFillRate(sampleProcesses)} %`);

// ---------------------------------------------------------------------------
section("6 · Validaciones");

const primero = sampleCandidates[0];
if (primero === undefined) throw new Error("No hay candidatos de ejemplo");

console.log(`Candidato correcto (${primero.fullName}):`, validateCandidate(primero));

console.log("\nFicha rota a propósito:");
console.log(
  validateCandidate({
    ...primero,
    yearsOfExperience: 80,
    currentSalary: 0,
    skills: [],
    email: "esto-no-es-un-email",
    phone: "   ",
  }),
);

console.log("\nVacante con el rango salarial invertido:");
console.log(validateVacancy({ ...vacancy, salaryRangeMin: 9000, salaryRangeMax: 4000 }));

console.log("");
