/**
 * La sesión del backoffice: el JWT que devuelve POST /auth/login.
 *
 * Es el único archivo que toca localStorage. El resto de la aplicación
 * pregunta aquí si hay sesión, nunca lee la clave a mano.
 *
 * Por qué localStorage: lo fija el ticket AUTH-02. Tiene un coste conocido:
 * cualquier script que se ejecute en la página puede leerlo, así que un XSS
 * se llevaría el token. Lo acotan la caducidad corta del token (30 minutos,
 * la decide la API) y que solo viaja a nuestra API, nunca a la del tracker.
 *
 * "Sesión válida" significa: hay token y su fecha de caducidad no ha pasado.
 * Aquí no se comprueba la firma: el navegador no tiene el secreto, ni debe
 * tenerlo. La firma la comprueba la API en cada petición, y si no vale
 * responde 401 y lib/api.ts cierra la sesión.
 */

const TOKEN_KEY = "nexova.backoffice.token";

/** Nombre del evento con el que esta pestaña avisa de que la sesión cambió. */
const SESSION_EVENT = "nexova:session";

/**
 * localStorage solo existe en el navegador. Durante el renderizado en el
 * servidor no hay ni window, y a veces el navegador lo bloquea (modo privado
 * estricto, cookies desactivadas) y acceder lanza un error.
 */
function storage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return storage()?.getItem(TOKEN_KEY) ?? null;
}

/**
 * Por qué terminó la última sesión en esta pestaña:
 * - "logout": la persona pulsó "Cerrar sesión". Se vuelve a /login sin más.
 * - "ended": caducó, la API la rechazó (401) o se cerró en otra pestaña. Se
 *   vuelve a /login con un aviso y con la página en la que estaba.
 */
export type SessionEndReason = "logout" | "ended";

let ultimoCierre: SessionEndReason | null = null;

export function lastSessionEnd(): SessionEndReason | null {
  return ultimoCierre;
}

export function saveToken(token: string): void {
  try {
    storage()?.setItem(TOKEN_KEY, token);
  } catch {
    // Almacenamiento lleno o bloqueado: sin guardar el token no hay sesión,
    // y quien llama (el login) enseña su propio mensaje.
    throw new Error("No se ha podido guardar la sesión en este navegador.");
  }
  ultimoCierre = null;
  notifyChange();
}

export function clearToken(reason: SessionEndReason = "ended"): void {
  try {
    storage()?.removeItem(TOKEN_KEY);
  } catch {
    // Si el navegador bloquea el almacenamiento, el aviso a la pestaña sigue
    // haciendo falta: la sesión se da por cerrada igualmente.
  }
  ultimoCierre = reason;
  notifyChange();
}

/**
 * Lee la caducidad (exp) de un JWT sin verificarlo.
 *
 * Un JWT son tres trozos separados por puntos: cabecera, contenido y firma.
 * Los dos primeros son JSON en base64url, legibles por cualquiera: un JWT
 * está firmado, no cifrado. Devuelve null si el token no tiene esa forma.
 */
function readExpiry(token: string): number | null {
  const partes = token.split(".");
  if (partes.length !== 3) return null;

  try {
    // base64url usa - y _ en lugar de + y /, y no lleva el relleno "=" que
    // exige atob(). Se deshace antes de decodificar.
    const base64 = partes[1].replace(/-/g, "+").replace(/_/g, "/");
    const relleno = "=".repeat((4 - (base64.length % 4)) % 4);
    const contenido: unknown = JSON.parse(atob(base64 + relleno));

    if (
      typeof contenido === "object" &&
      contenido !== null &&
      "exp" in contenido &&
      typeof contenido.exp === "number"
    ) {
      return contenido.exp;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Milisegundos que le quedan a la sesión, o null si no hay sesión válida
 * (sin token, token mal formado o ya caducado).
 */
export function sessionTimeLeft(now: number = Date.now()): number | null {
  const token = getToken();
  if (!token) return null;

  const exp = readExpiry(token);
  if (exp === null) return null;

  // exp viene en segundos desde 1970 (estándar JWT); Date.now(), en milisegundos.
  const restante = exp * 1000 - now;
  return restante > 0 ? restante : null;
}

export function hasValidSession(): boolean {
  return sessionTimeLeft() !== null;
}

function notifyChange(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(SESSION_EVENT));
  }
}

/**
 * Avisa cuando la sesión cambia, en esta pestaña o en otra.
 *
 * - En esta pestaña, saveToken() y clearToken() lanzan SESSION_EVENT.
 * - En otra pestaña, el navegador lanza "storage" al cambiar localStorage.
 *   Así, cerrar sesión en una pestaña la cierra en todas.
 *
 * Devuelve la función que deja de escuchar. Tiene la forma que espera
 * useSyncExternalStore de React.
 */
export function subscribeToSession(onChange: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key !== TOKEN_KEY && event.key !== null) return;
    // Para esta pestaña, un cierre en otra pestaña es una sesión que terminó
    // sin que aquí se pidiera ("ended"); un login en otra, una sesión nueva.
    ultimoCierre = event.newValue ? null : "ended";
    onChange();
  };

  window.addEventListener(SESSION_EVENT, onChange);
  window.addEventListener("storage", onStorage);

  return () => {
    window.removeEventListener(SESSION_EVENT, onChange);
    window.removeEventListener("storage", onStorage);
  };
}
