import type {
  Candidate,
  CandidateInput,
  CandidateListResponse,
  Note,
  NotesResponse,
  Stage,
  Status,
} from "@/types/candidate";
import type { IncidentAnalysis } from "@/types/incident";

/**
 * El backoffice habla con dos APIs:
 * - la del tracker (API mock de 4Geeks), para las candidaturas;
 * - la propia de Nexova (services/api), para el analisis de incidencias.
 * Cada una con su variable de entorno, y las dos por el mismo request().
 */
interface ApiTarget {
  baseUrl: string | undefined;
  /** Nombre de la variable, para el mensaje si falta. */
  variable: string;
}

// process.env.NEXT_PUBLIC_* se escribe literal: Next sustituye el texto
// exacto al compilar, y con un acceso dinamico llegaria vacio al navegador.
const TRACKER_API: ApiTarget = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
  variable: "NEXT_PUBLIC_API_URL",
};

const NEXOVA_API: ApiTarget = {
  baseUrl: process.env.NEXT_PUBLIC_NEXOVA_API_URL,
  variable: "NEXT_PUBLIC_NEXOVA_API_URL",
};

/** Error de la API con el codigo HTTP y, si los hay, los errores por campo. */
export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string>;

  constructor(message: string, status: number, fieldErrors: Record<string, string> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

// Formatos de error que llegan:
// - tracker:          { error, details: { campo } }  y  { detail: [ { loc, msg } ] }
// - services/api:     { detail: "mensaje en espanol, listo para mostrar" }
interface ErrorBody {
  error?: string;
  details?: Record<string, string>;
  detail?: string | Array<{ loc: Array<string | number>; msg: string }>;
}

const MENSAJES_POR_ESTADO: Record<number, string> = {
  400: "La peticion no es valida.",
  404: "No se ha encontrado el recurso.",
  413: "El fichero es demasiado grande.",
  415: "El tipo de fichero no es valido.",
  422: "Hay datos que no son validos.",
  500: "Error del servidor. Intentalo de nuevo.",
};

/** Traduce cualquiera de los dos formatos de error a un ApiError. */
async function construirError(res: Response): Promise<ApiError> {
  let body: ErrorBody | null = null;
  try {
    body = (await res.json()) as ErrorBody;
  } catch {
    // 204 o respuesta sin JSON: nos quedamos con el mensaje por defecto.
  }

  const fieldErrors: Record<string, string> = {};

  // Formato A -> { error: "...", details: { status: "..." } }
  if (body?.details) {
    Object.assign(fieldErrors, body.details);
  }

  // Formato B (FastAPI) -> { detail: [{ loc: ["body", "email"], msg: "..." }] }
  if (Array.isArray(body?.detail)) {
    for (const item of body.detail) {
      const campo = String(item.loc[item.loc.length - 1]);
      fieldErrors[campo] = item.msg;
    }
  }

  const mensaje =
    body?.error ??
    (typeof body?.detail === "string" ? body.detail : undefined) ??
    MENSAJES_POR_ESTADO[res.status] ??
    `Error inesperado (${res.status}).`;

  return new ApiError(mensaje, res.status, fieldErrors);
}

/**
 * Punto unico por el que pasan todas las peticiones. Devuelve la respuesta
 * ya comprobada (2xx); si no, lanza un ApiError.
 */
async function send(
  api: ApiTarget,
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  if (!api.baseUrl) {
    throw new ApiError(`Falta la variable ${api.variable} en .env.local`, 0);
  }

  // Con FormData no se pone Content-Type: el navegador escribe
  // "multipart/form-data; boundary=…" con el separador que ha generado.
  // Si lo fijamos a mano, el boundary se pierde y el servidor no lo entiende.
  const headers =
    options.body instanceof FormData
      ? options.headers
      : { "Content-Type": "application/json", ...options.headers };

  let res: Response;
  try {
    res = await fetch(`${api.baseUrl}${path}`, { ...options, headers });
  } catch {
    // Sin red, servidor apagado o CORS: fetch si lanza en estos casos.
    throw new ApiError("No se ha podido conectar con el servidor.", 0);
  }

  if (!res.ok) {
    throw await construirError(res);
  }

  return res;
}

/** send() + el cuerpo JSON. */
async function request<T>(
  path: string,
  options: RequestInit = {},
  api: ApiTarget = TRACKER_API,
): Promise<T> {
  const res = await send(api, path, options);

  // 204 No Content: no hay cuerpo que parsear.
  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export interface CandidateFilters {
  status?: Status;
  stage?: Stage;
  search?: string;
  page?: number;
  limit?: number;
}

/** Monta la query string omitiendo los filtros vacios. */
function construirQuery(filters: CandidateFilters): string {
  const params = new URLSearchParams();

  for (const [clave, valor] of Object.entries(filters)) {
    if (valor !== undefined && valor !== null && valor !== "") {
      params.set(clave, String(valor));
    }
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

// --- Candidaturas ---

export function getCandidates(filters: CandidateFilters = {}): Promise<CandidateListResponse> {
  return request<CandidateListResponse>(`/records${construirQuery(filters)}`);
}

export function getCandidate(id: string): Promise<Candidate> {
  return request<Candidate>(`/records/${id}`);
}

export function createCandidate(input: CandidateInput): Promise<Candidate> {
  return request<Candidate>("/records", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** PUT: reemplaza el registro, exige el objeto completo. */
export function updateCandidate(id: string, input: CandidateInput): Promise<Candidate> {
  return request<Candidate>(`/records/${id}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

/** PATCH: solo estado y etapa. */
export function patchCandidate(
  id: string,
  cambios: { status?: Status; stage?: Stage },
): Promise<Candidate> {
  return request<Candidate>(`/records/${id}`, {
    method: "PATCH",
    body: JSON.stringify(cambios),
  });
}

export function deleteCandidate(id: string): Promise<void> {
  return request<void>(`/records/${id}`, { method: "DELETE" });
}

// --- Notas ---

/** Desenvuelve el sobre { data, meta } y devuelve solo el array. */
export async function getNotes(recordId: string): Promise<Note[]> {
  const respuesta = await request<NotesResponse>(`/records/${recordId}/notes`);
  return respuesta.data;
}

export function createNote(recordId: string, content: string): Promise<Note> {
  return request<Note>(`/records/${recordId}/notes`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function deleteNote(recordId: string, noteId: string): Promise<void> {
  return request<void>(`/records/${recordId}/notes/${noteId}`, { method: "DELETE" });
}

// --- Incidencias de soporte (services/api) ---

/** Sube el CSV del helpdesk y devuelve su analisis. */
export function analyzeIncidents(file: File): Promise<IncidentAnalysis> {
  const datos = new FormData();
  datos.append("file", file);

  return request<IncidentAnalysis>(
    "/api/incidents/analyze",
    { method: "POST", body: datos },
    NEXOVA_API,
  );
}

/** El ultimo analisis como CSV (una metrica por fila), listo para descargar. */
export async function downloadIncidentResults(): Promise<Blob> {
  const res = await send(NEXOVA_API, "/api/incidents/results/export");
  return res.blob();
}
