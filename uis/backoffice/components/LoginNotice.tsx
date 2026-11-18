"use client";

import { useSyncExternalStore } from "react";

/** La URL no cambia mientras se está en /login: no hay nada que escuchar. */
const sinSuscripcion = () => () => {};

function leerMotivo(): string | null {
  return new URLSearchParams(window.location.search).get("reason");
}

/**
 * Aviso en /login cuando AuthGuard ha traído aquí a alguien porque su sesión
 * terminó sola (?reason=ended): sin él, verse de pronto en el login parece
 * un fallo.
 *
 * Lee la URL con useSyncExternalStore y no con useSearchParams: este último
 * obliga a envolver la página en <Suspense> y el formulario dejaría de salir
 * en el HTML. En el servidor no hay URL que leer y no se pinta nada.
 */
export default function LoginNotice() {
  const motivo = useSyncExternalStore(sinSuscripcion, leerMotivo, () => null);
  if (motivo !== "ended") return null;

  return (
    <p
      role="status"
      className="mb-5 rounded-md border border-acento-600/60 bg-acento-500/10 px-3 py-2 text-sm text-acento-300"
    >
      Tu sesión se ha cerrado: ha caducado o se ha cerrado en otra pestaña. Vuelve a entrar.
    </p>
  );
}
