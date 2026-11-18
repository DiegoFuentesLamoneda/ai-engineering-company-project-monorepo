/**
 * Las redirecciones entre las vistas protegidas y /login.
 *
 * Al mandar a alguien a /login se guarda en ?next= la página en la que
 * estaba, para devolverle ahí después de entrar. Ese parámetro viene en la
 * URL, así que cualquiera puede escribirlo: un enlace a
 * /login?next=https://otra-web.com haría que, tras un login de verdad, el
 * backoffice llevara a la persona a una web ajena (una "open redirect", útil
 * para el phishing). Por eso solo se aceptan rutas de este mismo sitio.
 */

export const LOGIN_PATH = "/login";

export const FORGOT_PASSWORD_PATH = "/forgot-password";

/** Páginas a las que no tiene sentido volver con sesión. */
const AUTH_PATHS = [LOGIN_PATH, "/register", FORGOT_PASSWORD_PATH, "/reset-password"];

/**
 * La ruta de ?next= si es segura, o null.
 *
 * No basta con mirar que empiece por "/": el navegador entiende "//otra.com"
 * y "/\otra.com" como otra web. En lugar de enumerar trucos, se deja que
 * el propio navegador resuelva la URL y se comprueba que el origen no cambia.
 */
export function safeNextPath(valor: string | null, origin: string): string | null {
  if (!valor || !valor.startsWith("/")) return null;

  let url: URL;
  try {
    url = new URL(valor, origin);
  } catch {
    return null;
  }

  if (url.origin !== origin) return null;
  if (AUTH_PATHS.includes(url.pathname)) return null;
  return url.pathname + url.search + url.hash;
}

/**
 * La URL de /login para quien se ha quedado sin sesión en `desde`.
 * `caducada` añade el aviso de que la sesión terminó sin pedirlo.
 */
export function loginUrl(desde: string, origin: string, caducada: boolean): string {
  const params = new URLSearchParams();
  const next = safeNextPath(desde, origin);
  // Volver al panel ya es lo que pasa sin next: no hace falta ensuciar la URL.
  if (next && next !== "/") params.set("next", next);
  if (caducada) params.set("reason", "ended");

  const consulta = params.toString();
  return consulta ? `${LOGIN_PATH}?${consulta}` : LOGIN_PATH;
}
