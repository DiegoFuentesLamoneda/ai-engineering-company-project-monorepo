"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { safeNextPath } from "@/lib/auth-routes";
import { useSession } from "@/lib/useSession";

/**
 * Guardia de /login y /register: con sesión no tiene sentido verlas, y se
 * manda a la página de ?next= o al panel.
 *
 * Es el único sitio que sale de estas pantallas. Los formularios solo
 * guardan el token; al cambiar la sesión, esta guardia navega. Así funciona
 * igual tras entrar aquí, al abrir /login ya con sesión o al entrar desde
 * otra pestaña.
 */
export default function GuestGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const sesion = useSession();

  useEffect(() => {
    if (sesion !== true) return;
    const next = new URLSearchParams(window.location.search).get("next");
    // replace y no push: con "atrás" no se vuelve al formulario.
    router.replace(safeNextPath(next, window.location.origin) ?? "/");
  }, [sesion, router]);

  if (sesion === true) {
    return (
      <p role="status" className="py-6 text-center text-sm text-slate-400">
        Entrando…
      </p>
    );
  }

  // Mientras no se sabe (null) se pinta el formulario: es lo que verá casi
  // siempre quien llega aquí, y así sale ya en el HTML.
  return children;
}
