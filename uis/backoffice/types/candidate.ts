// Tipos del contrato de la API de Talent Tracker.
// Los nombres de campo son los que devuelve la API: no se renombran.

/** Estado de la candidatura en el proceso. */
export type Status = "received" | "in_progress" | "selected" | "discarded";

/** Etapa del pipeline de seleccion. */
export type Stage =
  | "pending"
  | "review"
  | "personal_interview"
  | "technical_interview"
  | "offer_presented";

/** Nota interna asociada a una candidatura. */
export interface Note {
  id: string;
  record_id: string;
  content: string;
  created_at: string;
}

/** Una candidatura. En la API se llama "record". */
export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  position: string;
  linkedin_url: string | null;
  cv_url: string | null;
  status: Status;
  stage: Stage;
  experience_years: number;
  notes_count: number;
  applied_at: string;
  updated_at: string;
  /** Solo viene en GET /records, no en GET /records/:id. */
  notes?: Note[];
}

/** Sobre de GET /records. */
export interface CandidateListResponse {
  total: number;
  page: number;
  limit: number;
  data: Candidate[];
}

/** Sobre de GET /records/:id/notes. */
export interface NotesResponse {
  data: Note[];
  meta: { total: number };
}

/** Cuerpo que aceptan POST /records y PUT /records/:id. */
export interface CandidateInput {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: number;
  linkedin_url: string | null;
  cv_url: string | null;
}
