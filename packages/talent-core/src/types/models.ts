/**
 * Entidades de dominio de Nexova Solutions.
 *
 * Los nombres de campo y los valores de las uniones se copian literalmente de
 * `docs/contexts/02-coding-fundamentals.es.md`. No se traducen ni se renombran:
 * el ATS, la API de `services/` y los hitos siguientes hablan este vocabulario.
 */

// ---------------------------------------------------------------------------
// Uniones de dominio
// ---------------------------------------------------------------------------

export type EnglishLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | "Native";

export type SeniorityLevel =
  | "Junior"
  | "Semi-Senior"
  | "Senior"
  | "Lead"
  | "Executive";

export type AvailabilityStatus =
  | "Immediate"
  | "2 weeks"
  | "1 month"
  | "Not available";

export type CandidateStatus = "Active" | "In process" | "Hired" | "Inactive";

export type VacancyStatus = "Open" | "In progress" | "Closed" | "On hold";

export type ProcessStage =
  | "Screening"
  | "Interview"
  | "Technical test"
  | "Final interview"
  | "Offer"
  | "Rejected"
  | "Hired";

// ---------------------------------------------------------------------------
// Entidades
// ---------------------------------------------------------------------------

/** Una persona en la base de datos de talento de Nexova. */
export interface Candidate {
  /** Identificador único (ej: "C-2024-0451") */
  id: string;
  /** Nombre completo */
  fullName: string;
  /** Email de contacto */
  email: string;
  /** Teléfono de contacto */
  phone: string;
  /** Años totales de experiencia profesional */
  yearsOfExperience: number;
  /** Array de habilidades (ej: ["TypeScript", "React", "Node.js"]) */
  skills: string[];
  /** Nivel de inglés */
  englishLevel: EnglishLevel;
  /** Nivel profesional */
  seniority: SeniorityLevel;
  /** Salario actual en USD */
  currentSalary: number;
  /** Salario esperado en USD */
  expectedSalary: number;
  /** Disponibilidad actual */
  availability: AvailabilityStatus;
  /** Ciudad y país (ej: "Valencia, España") */
  location: string;
  /** Solo acepta posiciones remotas */
  remoteOnly: boolean;
  /** Estado actual en la base de datos */
  status: CandidateStatus;
}

/** Una posición abierta que Nexova intenta cubrir para un cliente. */
export interface Vacancy {
  /** Identificador único (ej: "V-2024-0892") */
  id: string;
  /** Título del puesto (ej: "Senior Full-Stack Developer") */
  title: string;
  /** Nombre de la empresa cliente */
  companyName: string;
  /** Habilidades técnicas requeridas */
  requiredSkills: string[];
  /** Habilidades deseables */
  preferredSkills: string[];
  /** Experiencia mínima requerida */
  minYearsExperience: number;
  /** Experiencia máxima relevante */
  maxYearsExperience: number;
  /** Nivel mínimo de inglés */
  requiredEnglishLevel: EnglishLevel;
  /** Nivel de seniority requerido */
  requiredSeniority: SeniorityLevel;
  /** Salario mínimo ofrecido (USD) */
  salaryRangeMin: number;
  /** Salario máximo ofrecido (USD) */
  salaryRangeMax: number;
  /** Posición remota */
  isRemote: boolean;
  /** Ubicación de oficina si no es remota */
  location: string;
  /** Estado actual de la vacante */
  status: VacancyStatus;
}

/** Progreso de un candidato a través del proceso de selección de una vacante. */
export interface SelectionProcess {
  /** Identificador único (ej: "SP-2024-1523") */
  id: string;
  /** Referencia al candidato */
  candidateId: string;
  /** Referencia a la vacante */
  vacancyId: string;
  /** Etapa actual */
  stage: ProcessStage;
  /** Puntaje de match (0-100) */
  score: number;
  /** Notas del consultor */
  notes: string;
  /** Fecha de inicio del proceso */
  createdAt: Date;
  /** Fecha de última actualización */
  updatedAt: Date;
}

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
] as const satisfies readonly EnglishLevel[];

/** Niveles profesionales de menor a mayor responsabilidad. */
export const SENIORITY_LEVELS = [
  "Junior",
  "Semi-Senior",
  "Senior",
  "Lead",
  "Executive",
] as const satisfies readonly SeniorityLevel[];

/** Todos los estados posibles de un candidato, para reportes exhaustivos. */
export const CANDIDATE_STATUSES = [
  "Active",
  "In process",
  "Hired",
  "Inactive",
] as const satisfies readonly CandidateStatus[];

/** Todas las disponibilidades posibles, para poblar filtros y selectores. */
export const AVAILABILITY_STATUSES = [
  "Immediate",
  "2 weeks",
  "1 month",
  "Not available",
] as const satisfies readonly AvailabilityStatus[];

// ---------------------------------------------------------------------------
// Tipos auxiliares
//
// El contexto declara estas formas en línea dentro de las firmas. Se les da
// nombre aquí: son estructuralmente idénticas y el código se lee mejor.
// ---------------------------------------------------------------------------

/** Sentido de una ordenación. */
export type SortOrder = "asc" | "desc";

/** Resultado de una validación de negocio. */
export interface ValidationResult {
  /** `true` solo si no hay ningún error */
  valid: boolean;
  /** Mensajes de error; vacío cuando `valid` es `true` */
  errors: string[];
}

/** Un candidato junto a su puntuación contra una vacante concreta. */
export interface ScoredCandidate {
  candidate: Candidate;
  /** Puntuación de match entre 0 y 100 */
  score: number;
}

/** Frecuencia de una habilidad en un conjunto de candidatos. */
export interface SkillCount {
  skill: string;
  /** Cuántos candidatos declaran esa habilidad */
  count: number;
}
