import type {
  Candidate,
  CandidateInput,
  CandidateListResponse,
  Note,
  NotesResponse,
  Stage,
  Status,
} from "@/types/candidate";
import type {
  Me,
  Message,
  Profile,
  ProfileUpdate,
  RegisterInput,
  Token,
  UserCreated,
} from "@/types/auth";
import type { IncidentAnalysis } from "@/types/incident";
import type {
  Incident,
  IncidentFilters,
  IncidentInput,
  IncidentManagerStatus,
  IncidentSummary,
} from "@/types/incident-manager";
import type {
  Supplier,
  SupplierFilters,
  SupplierInput,
  SupplierStatus,
} from "@/types/supplier";
import { clearToken, getToken, saveToken } from "@/lib/session";

/**
 * El backoffice habla con dos APIs:
 * - la del tracker (API mock de 4Geeks), para las candidaturas;
 * - la propia de Nexova (services/api): incidencias, proveedores y cuentas.
 * Cada una con su variable de entorno, y las dos por el mismo request().
 */
interface ApiTarget {
  baseUrl: string | undefined;
  /** Nombre de la variable, para el mensaje si falta. */
  variable: string;
  /**
   * Si las peticiones llevan el token de la sesion. Solo nuestra API: la del
   * tracker es una mock que comparten todos los alumnos del curso, y
   * mandarle el token seria regalarselo a un tercero.
   */
  auth: boolean;
}

// process.env.NEXT_PUBLIC_* se escribe literal: Next sustituye el texto
// exacto al compilar, y con un acceso dinamico llegaria vacio al navegador.
const TRACKER_API: ApiTarget = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
  variable: "NEXT_PUBLIC_API_URL",
  auth: false,
};

/** Rutas protegidas de la API propia: todas menos el login y el registro. */
const NEXOVA_API: ApiTarget = {
  baseUrl: process.env.NEXT_PUBLIC_NEXOVA_API_URL,
  variable: "NEXT_PUBLIC_NEXOVA_API_URL",
  auth: true,
};

/**
 * Login, registro y recuperacion de contraseña: la misma API, sin token. Un
 * 401 aqui es "email o contraseña incorrectos", no "la sesion ha caducado",
 * y no debe cerrarla.
 */
const NEXOVA_PUBLIC_API: ApiTarget = { ...NEXOVA_API, auth: false };

/** Mensaje de un 401 en una ruta protegida: se ha cerrado la sesion. */
export const SESSION_EXPIRED_MESSAGE =
  "Tu sesión ha caducado o no es válida. Vuelve a iniciar sesión.";

/**
 * Error de la API con el codigo HTTP y, si los hay, los errores por campo.
 * fieldCodes solo lo rellena el gestor de incidencias: un codigo estable por
 * campo ("missing", "too_long"…) para que el formulario escriba su propio
 * mensaje en vez de depender del texto de la API.
 */
export class ApiError extends Error {
  status: number;
  fieldErrors: Record<string, string>;
  fieldCodes: Record<string, string>;

  constructor(
    message: string,
    status: number,
    fieldErrors: Record<string, string> = {},
    fieldCodes: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.fieldCodes = fieldCodes;
  }
}

// Formatos de error que llegan:
// - tracker:          { error, details: { campo } }  y  { detail: [ { loc, msg } ] }
// - services/api:     { detail: "mensaje en espanol, listo para mostrar" }
// - gestor (400):     { detail, errors: [ { field, code, message } ] }
interface ErrorBody {
  error?: string;
  details?: Record<string, string>;
  detail?: string | Array<{ loc: Array<string | number>; msg: string }>;
  errors?: Array<{ field: string; code: string; message: string }>;
}

const MENSAJES_POR_ESTADO: Record<number, string> = {
  400: "La peticion no es valida.",
  401: "Email o contraseña incorrectos.",
  404: "No se ha encontrado el recurso.",
  409: "La operación no está permitida en el estado actual.",
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
  // Una regla que relaciona dos campos (moneda segun el pais) llega con
  // loc: ["body"]: no es de ningun campo, asi que va al mensaje general.
  let errorDelCuerpo: string | undefined;
  if (Array.isArray(body?.detail)) {
    for (const item of body.detail) {
      // Pydantic antepone "Value error, " a los mensajes de nuestras reglas.
      const msg = item.msg.replace(/^Value error, /, "");
      if (item.loc.length === 1 && item.loc[0] === "body") {
        errorDelCuerpo = msg;
        continue;
      }
      const campo = String(item.loc[item.loc.length - 1]);
      fieldErrors[campo] = msg;
    }
  }

  // Formato C (gestor de incidencias) -> { errors: [{ field, code, message }] }
  // "body" es el cuerpo entero (JSON roto): va al mensaje general.
  const fieldCodes: Record<string, string> = {};
  if (Array.isArray(body?.errors)) {
    for (const item of body.errors) {
      if (item.field === "body") {
        errorDelCuerpo = item.message;
        continue;
      }
      fieldErrors[item.field] = item.message;
      fieldCodes[item.field] = item.code;
    }
  }

  const mensaje =
    errorDelCuerpo ??
    body?.error ??
    (typeof body?.detail === "string" ? body.detail : undefined) ??
    MENSAJES_POR_ESTADO[res.status] ??
    `Error inesperado (${res.status}).`;

  return new ApiError(mensaje, res.status, fieldErrors, fieldCodes);
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

  const headers = new Headers(options.headers);

  // Con FormData (subida de ficheros) y URLSearchParams (formulario del
  // login) no se pone Content-Type: el navegador lo escribe solo, y en el
  // caso de FormData con el "boundary" que separa las partes. Si lo fijamos
  // a mano, se pierde y el servidor no entiende el cuerpo.
  const cuerpoDeFormulario =
    options.body instanceof FormData || options.body instanceof URLSearchParams;
  if (!cuerpoDeFormulario && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // El token se lee en cada peticion, no al cargar la pagina: si la sesion
  // se cierra en otra pestaña, la siguiente peticion ya sale sin el.
  if (api.auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${api.baseUrl}${path}`, { ...options, headers });
  } catch {
    // Sin red, servidor apagado o CORS: fetch si lanza en estos casos.
    throw new ApiError("No se ha podido conectar con el servidor.", 0);
  }

  // 401 en una ruta protegida: el token falta, ha caducado o la API ya no lo
  // acepta (cuenta desactivada o borrada). La sesion se cierra aqui, en un
  // solo sitio para todas las llamadas. clearToken() avisa a quien escucha
  // la sesion, y la proteccion de rutas lleva al usuario a /login.
  if (res.status === 401 && api.auth) {
    clearToken();
    throw new ApiError(SESSION_EXPIRED_MESSAGE, 401);
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

// --- Gestor de incidencias (services/api) ---

/**
 * Registra una incidencia. Nace "open": el estado no se envia. Un 400 trae
 * los errores por campo en fieldErrors y fieldCodes.
 */
export function createIncident(input: IncidentInput): Promise<Incident> {
  return request<Incident>(
    "/api/incidents",
    { method: "POST", body: JSON.stringify(input) },
    NEXOVA_API,
  );
}

/** La lista, la más reciente primero. Los filtros vacíos no viajan. */
export function getIncidents(filters: IncidentFilters = {}): Promise<Incident[]> {
  const params = new URLSearchParams();
  for (const [clave, valor] of Object.entries(filters)) {
    if (valor) params.set(clave, valor);
  }
  const query = params.toString();

  return request<Incident[]>(`/api/incidents${query ? `?${query}` : ""}`, {}, NEXOVA_API);
}

/**
 * Cambia el estado. La API aplica el ciclo de vida: un salto que no permite,
 * o un cambio que otra persona hizo antes, responde 409.
 */
export function updateIncidentStatus(id: string, status: IncidentManagerStatus): Promise<Incident> {
  return request<Incident>(
    `/api/incidents/${id}/status`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    NEXOVA_API,
  );
}

/** Totales de todas las incidencias, sin filtros: el panel de resumen. */
export function getIncidentSummary(): Promise<IncidentSummary> {
  return request<IncidentSummary>("/api/incidents/summary", {}, NEXOVA_API);
}

// --- Directorio de proveedores (services/api) ---
// Sin prefijo /api: son las rutas literales del enunciado.

/** El directorio, ya ordenado por nombre. Los filtros vacios no viajan. */
export function getSuppliers(filters: SupplierFilters = {}): Promise<Supplier[]> {
  const params = new URLSearchParams();
  if (filters.country) params.set("country", filters.country);
  if (filters.category) params.set("category", filters.category);
  const query = params.toString();

  return request<Supplier[]>(`/suppliers${query ? `?${query}` : ""}`, {}, NEXOVA_API);
}

export function createSupplier(input: SupplierInput): Promise<Supplier> {
  return request<Supplier>(
    "/suppliers",
    { method: "POST", body: JSON.stringify(input) },
    NEXOVA_API,
  );
}

/** Cambia la tarifa. La API renueva updated_at. */
export function updateSupplierRate(id: number, monthlyRate: number): Promise<Supplier> {
  return request<Supplier>(
    `/suppliers/${id}/rate`,
    { method: "PATCH", body: JSON.stringify({ monthly_rate: monthlyRate }) },
    NEXOVA_API,
  );
}

export function updateSupplierStatus(id: number, status: SupplierStatus): Promise<Supplier> {
  return request<Supplier>(
    `/suppliers/${id}/status`,
    { method: "PATCH", body: JSON.stringify({ status }) },
    NEXOVA_API,
  );
}

// --- Cuentas: login, registro y perfil (services/api) ---

/**
 * POST /auth/login y guarda el token. Si las credenciales no valen, lanza
 * un ApiError 401 y la sesion anterior, si la habia, no se toca.
 *
 * El cuerpo es un formulario, no JSON: es el formato estandar de OAuth2, el
 * mismo que usa el boton Authorize de /docs. Por eso el email va en el campo
 * "username".
 */
export async function login(email: string, password: string): Promise<Token> {
  const formulario = new URLSearchParams({ username: email, password });

  const token = await request<Token>(
    "/auth/login",
    { method: "POST", body: formulario },
    NEXOVA_PUBLIC_API,
  );
  saveToken(token.access_token);
  return token;
}

/**
 * Registro: POST /users con el perfil opcional y, si sale bien, login con
 * las mismas credenciales. Asi el registro deja la sesion abierta.
 *
 * Si falla el alta (email repetido, datos no validos), no se intenta el
 * login y el ApiError trae los errores por campo.
 *
 * Si el alta sale bien y el login no (la API se cae justo entre las dos
 * llamadas), la cuenta ya existe: el mensaje lo dice, para que la persona
 * entre por /login y no intente registrarse otra vez con el mismo email.
 */
export async function register(input: RegisterInput): Promise<UserCreated> {
  const cuenta = await request<UserCreated>(
    "/users",
    { method: "POST", body: JSON.stringify(input) },
    NEXOVA_PUBLIC_API,
  );
  try {
    await login(input.email, input.password);
  } catch (e) {
    throw new ApiError(
      "La cuenta se ha creado, pero no se ha podido iniciar sesión. Entra con tu email y contraseña.",
      e instanceof ApiError ? e.status : 0,
    );
  }
  return cuenta;
}

/**
 * POST /auth/forgot-password. La API responde siempre el mismo 200, tenga
 * cuenta el email o no, y envia el enlace despues de responder. Por eso aqui
 * no hay nada que distinguir: si no lanza, se muestra el mensaje fijo.
 */
export function forgotPassword(email: string): Promise<Message> {
  return request<Message>(
    "/auth/forgot-password",
    { method: "POST", body: JSON.stringify({ email }) },
    NEXOVA_PUBLIC_API,
  );
}

/**
 * POST /auth/reset-password con el token del enlace. Un 400 es un enlace
 * inventado, caducado o ya usado: la API da el mismo mensaje para los tres.
 * No inicia sesion: despues se entra por /login con la contraseña nueva.
 */
export function resetPassword(token: string, newPassword: string): Promise<Message> {
  return request<Message>(
    "/auth/reset-password",
    { method: "POST", body: JSON.stringify({ token, new_password: newPassword }) },
    NEXOVA_PUBLIC_API,
  );
}

/**
 * POST /auth/change-password, con la sesion iniciada, y guarda el token nuevo.
 *
 * Cambiar la contraseña invalida todos los tokens emitidos antes, tambien el
 * de esta sesion: sin guardar el que devuelve la API, la siguiente peticion
 * daria 401 y se cerraria la sesion de quien acaba de cambiarla. Las demas
 * sesiones (otro navegador, otro equipo) se quedan con el viejo y se cierran.
 *
 * Un 400 es "la actual no es correcta" o "la nueva es igual que la actual",
 * con el mensaje de la API. Si falla, el token de ahora no se toca.
 */
export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<Token> {
  const token = await request<Token>(
    "/auth/change-password",
    {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    },
    NEXOVA_API,
  );
  saveToken(token.access_token);
  return token;
}

/** Cierra la sesion. El JWT no tiene estado en la API: basta con olvidarlo. */
export function logout(): void {
  clearToken("logout");
}

/** GET /auth/me: email y rol de la cuenta, con su perfil. */
export function getMe(): Promise<Me> {
  return request<Me>("/auth/me", {}, NEXOVA_API);
}

/** PUT /profiles/me: solo cambian los campos enviados; uno a null se borra. */
export function updateMyProfile(changes: ProfileUpdate): Promise<Profile> {
  return request<Profile>(
    "/profiles/me",
    { method: "PUT", body: JSON.stringify(changes) },
    NEXOVA_API,
  );
}
