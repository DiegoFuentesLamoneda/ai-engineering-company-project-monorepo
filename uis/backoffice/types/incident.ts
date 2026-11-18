/**
 * Contrato de POST /api/incidents/analyze (services/api), en TypeScript.
 * Es AnalysisResponse de services/api/app/domains/incidents/schemas.py:
 * si cambia alli, se cambia aqui.
 *
 * Los valores son codigos del briefing (TECHNICAL, CLOSED, invalid_email…).
 * Su texto en pantalla sale de lib/labels.ts.
 */

export type IncidentCategory = "TECHNICAL" | "BILLING" | "ACCESS" | "HR_QUERY" | "COMPLAINT";

export type IncidentStatus = "OPEN" | "CLOSED" | "DISCARDED";

export type IncidentRule =
  | "missing_client_company"
  | "invalid_category"
  | "invalid_description"
  | "invalid_agent_id"
  | "invalid_email"
  | "closed_without_score"
  | "score_out_of_range"
  | "invalid_ticket_id"
  | "invalid_date"
  | "invalid_status";

export type SatisfactionScore = 1 | 2 | 3 | 4 | 5;

export interface RuleCount {
  rule: IncidentRule;
  /** Etiqueta en ingles del briefing. La interfaz usa RULE_LABELS. */
  label: string;
  count: number;
}

export interface CategoryCount {
  category: IncidentCategory;
  count: number;
  /** Sobre los registros validos, con un decimal. */
  percentage: number;
}

export interface StatusCount {
  status: IncidentStatus;
  count: number;
  percentage: number;
}

export interface ScoreCount {
  score: SatisfactionScore;
  label: string;
  count: number;
}

export interface Satisfaction {
  /** Tickets validos en estado CLOSED. */
  closed_records: number;
  /** De esos, los que tienen puntuacion. */
  scored_records: number;
  /** null si ningun ticket cerrado tiene puntuacion. */
  average_score: number | null;
  distribution: ScoreCount[];
}

export interface InvalidSample {
  /** Linea del fichero, contando la cabecera como la 1. */
  line: number;
  /** "" si el identificador falta o no tiene el formato NXV-XXXXXX. */
  ticket_id: string;
  rules: IncidentRule[];
}

export interface IncidentAnalysis {
  total_records: number;
  valid_records: number;
  invalid_records: number;
  invalid_by_rule: RuleCount[];
  by_category: CategoryCount[];
  by_status: StatusCount[];
  satisfaction: Satisfaction;
  /** Hasta 50 filas invalidas de muestra. Nunca incluye el email del cliente. */
  invalid_samples: InvalidSample[];
}
