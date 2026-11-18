import { useSyncExternalStore } from "react";
import { hasValidSession, subscribeToSession } from "@/lib/session";

/**
 * ¿Hay sesión válida? Se actualiza sola al iniciar o cerrar sesión, aquí o
 * en otra pestaña.
 *
 * Devuelve null mientras no se sabe: en el servidor no hay localStorage, y
 * durante la hidratación React usa el valor del servidor para que el HTML
 * coincida. Sin ese null, el primer render en el navegador diría "no hay
 * sesión" a alguien que sí la tiene y lo mandaría a /login.
 */
export function useSession(): boolean | null {
  return useSyncExternalStore(subscribeToSession, hasValidSession, () => null);
}
