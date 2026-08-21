/**
 * Fábricas para los tests.
 *
 * Cada entidad tiene catorce o quince campos, y un test que los repite todos
 * esconde lo único que importa: el campo que se está probando. Estas fábricas
 * parten de una ficha válida y dejan sobrescribir solo lo relevante.
 *
 * Quedan fuera de `npm run build` — ver `tsconfig.build.json`.
 */

import type {
  Candidate,
  SelectionProcess,
  Vacancy,
} from "../types/models.js";

/** Candidato válido genérico; pasa `validateCandidate` sin errores. */
export function makeCandidate(overrides: Partial<Candidate> = {}): Candidate {
  return {
    id: "C-0000-0001",
    fullName: "Persona de Prueba",
    email: "persona.prueba@email.com",
    phone: "+34 600 000 000",
    yearsOfExperience: 5,
    skills: ["TypeScript"],
    englishLevel: "B2",
    seniority: "Semi-Senior",
    currentSalary: 3000,
    expectedSalary: 3500,
    availability: "Immediate",
    location: "Valencia, España",
    remoteOnly: false,
    status: "Active",
    ...overrides,
  };
}

/** Vacante válida genérica; es la del contexto del hito. */
export function makeVacancy(overrides: Partial<Vacancy> = {}): Vacancy {
  return {
    id: "V-0000-0001",
    title: "Senior Full-Stack Developer",
    companyName: "TechCorp Solutions",
    requiredSkills: ["TypeScript", "React", "Node.js"],
    preferredSkills: ["PostgreSQL", "Docker"],
    minYearsExperience: 4,
    maxYearsExperience: 8,
    requiredEnglishLevel: "B2",
    requiredSeniority: "Senior",
    salaryRangeMin: 5000,
    salaryRangeMax: 7000,
    isRemote: true,
    location: "Remote",
    status: "Open",
    ...overrides,
  };
}

/** Proceso de selección válido genérico, con fechas fijas. */
export function makeProcess(
  overrides: Partial<SelectionProcess> = {},
): SelectionProcess {
  return {
    id: "SP-0000-0001",
    candidateId: "C-0000-0001",
    vacancyId: "V-0000-0001",
    stage: "Screening",
    score: 50,
    notes: "",
    createdAt: new Date("2026-01-01"),
    updatedAt: new Date("2026-01-15"),
    ...overrides,
  };
}
