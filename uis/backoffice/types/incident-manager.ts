/**
 * Contrato del gestor de incidencias centralizado (services/api, /api/incidents),
 * en TypeScript. Son Incident, IncidentCreate e IncidentSummary de
 * services/api/app/domains/incidents/schemas.py: si cambian allí, se cambian aquí.
 *
 * Los valores son los del briefing (docs/contexts/proyectos/centralized-incident-manager.es.md).
 * Su texto en pantalla sale de lib/labels.ts.
 *
 * Estado y categoría llevan el prefijo IncidentManager porque types/incident.ts
 * ya tiene IncidentStatus e IncidentCategory: son los del CSV del analizador
 * (OPEN, TECHNICAL…), otro vocabulario.
 */

export type IncidentManagerStatus = "open" | "in_progress" | "resolved" | "discarded";

export type IncidentManagerCategory =
  | "technical_failure"
  | "process_error"
  | "client_complaint"
  | "candidate_issue"
  | "staff_issue"
  | "sla_breach"
  | "data_quality"
  | "other";

export type IncidentOrigin = "customer" | "branch" | "internal";

export type Branch = "central" | "valencia_operations" | "miami_office" | "remote";

/** Lo que se envía al registrar una incidencia. El estado no: nace "open". */
export interface IncidentInput {
  title: string;
  description: string;
  category: IncidentManagerCategory;
  origin: IncidentOrigin;
  branch: Branch;
}

export interface Incident extends IncidentInput {
  /** UUID. */
  id: string;
  status: IncidentManagerStatus;
  /** ISO 8601 con zona horaria. */
  created_at: string;
  updated_at: string;
}

/** Filtros de GET /api/incidents. Todos opcionales y combinables. */
export interface IncidentFilters {
  status?: IncidentManagerStatus;
  origin?: IncidentOrigin;
  branch?: Branch;
  category?: IncidentManagerCategory;
}

export interface IncidentSummary {
  total: number;
  /** Todos los valores, en el orden del briefing, también los que están a 0. */
  by_status: Record<IncidentManagerStatus, number>;
  by_category: Record<IncidentManagerCategory, number>;
  by_origin: Record<IncidentOrigin, number>;
  by_branch: Record<Branch, number>;
}

/** Código estable de cada error del 400 del gestor. */
export type FieldErrorCode =
  | "missing"
  | "blank"
  | "too_long"
  | "invalid_choice"
  | "not_text"
  | "not_allowed"
  | "invalid_id"
  | "invalid_body"
  | "invalid";
