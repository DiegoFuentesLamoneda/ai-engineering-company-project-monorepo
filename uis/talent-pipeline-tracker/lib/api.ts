import type {
  Candidate,
  CandidateInput,
  CandidateListResponse,
  Note,
  NotesResponse,
  Stage,
  Status,
} from "@/types/candidate";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

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

// La API devuelve dos formatos de error distintos, ambos con codigo 422.
interface ErrorBody {
  error?: string;
  details?: Record<string, string>;
  detail?: Array<{ loc: Array<string | number>; msg: string }>;
}

const MENSAJES_POR_ESTADO: Record<number, string> = {
  400: "La peticion no es valida.",
  404: "No se ha encontrado el recurso.",
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
    MENSAJES_POR_ESTADO[res.status] ??
    `Error inesperado (${res.status}).`;

  return new ApiError(mensaje, res.status, fieldErrors);
}

/** Punto unico por el que pasan todas las peticiones a la API. */
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!BASE_URL) {
    throw new ApiError("Falta la variable NEXT_PUBLIC_API_URL en .env.local", 0);
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    // Sin red, DNS caido o CORS: fetch si lanza en estos casos.
    throw new ApiError("No se ha podido conectar con el servidor.", 0);
  }

  if (!res.ok) {
    throw await construirError(res);
  }

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
