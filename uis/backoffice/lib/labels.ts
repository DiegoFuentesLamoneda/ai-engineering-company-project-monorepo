import type { Stage, Status } from "@/types/candidate";
import type {
  IncidentCategory,
  IncidentRule,
  IncidentStatus,
  SatisfactionScore,
} from "@/types/incident";

/**
 * Etiquetas visibles en la interfaz.
 * Los valores crudos de la API nunca se muestran al usuario.
 */
export const STATUS_LABELS: Record<Status, string> = {
  received: "Recibida",
  in_progress: "En proceso",
  selected: "Seleccionada",
  discarded: "Descartada",
};

export const STAGE_LABELS: Record<Stage, string> = {
  pending: "Pendiente de revisión",
  review: "En revisión",
  personal_interview: "Entrevista personal",
  technical_interview: "Entrevista técnica",
  offer_presented: "Oferta presentada",
};

/**
 * Color del distintivo de cada estado. Vive junto a las etiquetas porque es
 * la misma decision de dominio: como se presenta un estado al usuario.
 */
export const STATUS_BADGE_STYLES: Record<Status, string> = {
  received: "bg-slate-700 text-slate-200",
  in_progress: "bg-marca-600 text-white",
  selected: "bg-emerald-700 text-emerald-50",
  discarded: "bg-red-900 text-red-100",
};

/** Orden en el que se muestran en los desplegables de filtro. */
export const STATUS_VALUES: Status[] = [
  "received",
  "in_progress",
  "selected",
  "discarded",
];

export const STAGE_VALUES: Stage[] = [
  "pending",
  "review",
  "personal_interview",
  "technical_interview",
  "offer_presented",
];

// --- Incidencias de soporte (docs/contexts/proyectos/incidents-file-analysis.es.md) ---

/** Las descripciones de la tabla "Categorías válidas" del briefing. */
export const INCIDENT_CATEGORY_LABELS: Record<IncidentCategory, string> = {
  TECHNICAL: "Problema técnico",
  BILLING: "Facturación",
  ACCESS: "Acceso, login o permisos",
  HR_QUERY: "Consulta de RR. HH.",
  COMPLAINT: "Queja formal",
};

export const INCIDENT_STATUS_LABELS: Record<IncidentStatus, string> = {
  OPEN: "Abierto",
  CLOSED: "Cerrado",
  DISCARDED: "Descartado",
};

/**
 * Las siete primeras son la tabla "Reglas de registros inválidos" del briefing.
 * Las tres últimas cubren los campos obligatorios que esa tabla no menciona.
 */
export const INCIDENT_RULE_LABELS: Record<IncidentRule, string> = {
  missing_client_company: "Falta la empresa cliente",
  invalid_category: "Categoría vacía o no válida",
  invalid_description: "Descripción vacía o de menos de 5 caracteres",
  invalid_agent_id: "Agente vacío o sin el formato AGT-XX",
  invalid_email: "Email del cliente vacío o no válido",
  closed_without_score: "Ticket cerrado sin puntuación",
  score_out_of_range: "Puntuación fuera de rango (1-5)",
  invalid_ticket_id: "Identificador vacío o sin el formato NXV-XXXXXX",
  invalid_date: "Fecha vacía o no válida",
  invalid_status: "Estado vacío o no válido",
};

export const SATISFACTION_SCORE_LABELS: Record<SatisfactionScore, string> = {
  1: "Muy insatisfecho",
  2: "Insatisfecho",
  3: "Neutral",
  4: "Satisfecho",
  5: "Muy satisfecho",
};
