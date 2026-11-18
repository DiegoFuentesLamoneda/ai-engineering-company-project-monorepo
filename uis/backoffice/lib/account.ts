/**
 * Las reglas de las cuentas y los perfiles de services/api, copiadas aquí
 * para avisar antes de enviar. La API las vuelve a comprobar siempre: esto
 * solo ahorra un viaje y da el mensaje en español junto al campo.
 *
 * Origen: services/api/app/domains/users/schemas.py y profiles/schemas.py.
 * Si cambian allí, cambian aquí.
 */

import type { Profile } from "@/types/auth";

const PATRON_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PATRON_TELEFONO = /^\+?[0-9 ()\-]{6,20}$/;

export const MIN_PASSWORD_LENGTH = 8;
/** bcrypt solo usa los primeros 72 bytes; la API rechaza las más largas. */
const MAX_PASSWORD_BYTES = 72;
const MAX_NAME_LENGTH = 100;
const MAX_ADDRESS_LENGTH = 200;

/** Devuelve el error del campo, o undefined si es válido. */
export function checkEmail(email: string): string | undefined {
  const valor = email.trim();
  if (!valor) return "Escribe tu email.";
  if (!PATRON_EMAIL.test(valor)) return "El formato del email no es válido.";
  return undefined;
}

export function checkNewPassword(password: string): string | undefined {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `La contraseña necesita al menos ${MIN_PASSWORD_LENGTH} caracteres.`;
  }
  // En bytes, no en caracteres: una tilde o un emoji ocupan más de uno.
  if (new TextEncoder().encode(password).length > MAX_PASSWORD_BYTES) {
    return "La contraseña es demasiado larga.";
  }
  return undefined;
}

/** Los datos del perfil son opcionales: vacío es válido (se envía null). */
export function checkName(name: string): string | undefined {
  if (name.trim().length > MAX_NAME_LENGTH) {
    return `El nombre no puede pasar de ${MAX_NAME_LENGTH} caracteres.`;
  }
  return undefined;
}

export function checkPhone(phone: string): string | undefined {
  const valor = phone.trim();
  if (valor && !PATRON_TELEFONO.test(valor)) {
    return "Escribe solo números, espacios, guiones o paréntesis, con el prefijo si quieres (+34, +1).";
  }
  return undefined;
}

export function checkAddress(address: string): string | undefined {
  if (address.trim().length > MAX_ADDRESS_LENGTH) {
    return `La dirección no puede pasar de ${MAX_ADDRESS_LENGTH} caracteres.`;
  }
  return undefined;
}

/**
 * Los mensajes de Pydantic llegan en inglés ("String should have at least 8
 * characters"). Si la API rechaza uno de estos campos, se muestra este texto
 * en su lugar.
 */
export const API_FIELD_MESSAGES: Record<string, string> = {
  email: "La API ha rechazado el email: el formato no es válido.",
  password: `La API ha rechazado la contraseña: necesita al menos ${MIN_PASSWORD_LENGTH} caracteres y no puede ser demasiado larga.`,
  name: "La API ha rechazado el nombre.",
  phone: "La API ha rechazado el teléfono: usa solo números, espacios, guiones o paréntesis.",
  address: "La API ha rechazado la dirección.",
};

/** Un texto vacío viaja como null: "sin dato", no una cadena vacía. */
export function textOrNull(valor: string): string | null {
  const limpio = valor.trim();
  return limpio ? limpio : null;
}

/** Evento con el que el perfil avisa de que ha cambiado, con el perfil nuevo. */
const PROFILE_EVENT = "nexova:profile";

/**
 * Avisa de que el perfil se ha guardado. Lo escucha el menú de sesión, que
 * muestra el nombre: así se actualiza sin volver a pedir GET /auth/me y sin
 * un estado global para algo que solo comparten dos componentes.
 */
export function notifyProfileChange(profile: Profile): void {
  window.dispatchEvent(new CustomEvent<Profile>(PROFILE_EVENT, { detail: profile }));
}

/** Escucha los cambios del perfil. Devuelve la función que deja de escuchar. */
export function subscribeToProfile(onChange: (profile: Profile) => void): () => void {
  const listener = (event: Event) => onChange((event as CustomEvent<Profile>).detail);
  window.addEventListener(PROFILE_EVENT, listener);
  return () => window.removeEventListener(PROFILE_EVENT, listener);
}
