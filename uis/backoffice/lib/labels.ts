import type { Stage, Status } from "@/types/candidate";

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
