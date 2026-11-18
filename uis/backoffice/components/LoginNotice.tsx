"use client";

import { useSyncExternalStore } from "react";

/** La URL no cambia mientras se está en /login: no hay nada que escuchar. */
const sinSuscripcion = () => () => {};

function leerMotivo(): string | null {
  return new URLSearchParams(window.location.search).get("reason");
}

const AVISO_CLASS = "mb-5 rounded-md border px-3 py-2 text-sm";

/**
 * Por qué se ha llegado a /login, según ?reason=:
 * - "ended": AuthGuard ha traído aquí a alguien porque su sesión terminó
 *   sola. Sin el aviso, verse de pronto en el login parece un fallo.
 * - "password-reset": se acaba de elegir una contraseña nueva con el enlace
 *   del email. El aviso confirma que ha funcionado y dice qué hacer ahora.
 */
const AVISOS: Record<string, { texto: string; tono: string }> = {
  ended: {
    texto: "Tu sesión se ha cerrado: ha caducado o se ha cerrado en otra pestaña. Vuelve a entrar.",
    tono: "border-acento-600/60 bg-acento-500/10 text-acento-300",
  },
  "password-reset": {
    texto: "Contraseña actualizada. Ya puedes iniciar sesión con la nueva.",
    tono: "border-emerald-800 bg-emerald-950 text-emerald-100",
  },
};

/**
 * Lee la URL con useSyncExternalStore y no con useSearchParams: este último
 * obliga a envolver la página en <Suspense> y el formulario dejaría de salir
 * en el HTML. En el servidor no hay URL que leer y no se pinta nada.
 */
export default function LoginNotice() {
  const motivo = useSyncExternalStore(sinSuscripcion, leerMotivo, () => null);
  const aviso = motivo ? AVISOS[motivo] : undefined;
  if (!aviso) return null;

  return (
    <p role="status" className={`${AVISO_CLASS} ${aviso.tono}`}>
      {aviso.texto}
    </p>
  );
}
