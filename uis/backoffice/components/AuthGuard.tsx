"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { LOGIN_PATH, loginUrl } from "@/lib/auth-routes";
import { clearToken, getToken, lastSessionEnd, sessionTimeLeft } from "@/lib/session";
import { useSession } from "@/lib/useSession";

/** El máximo que admite setTimeout (unos 24 días); más, y dispara al momento. */
const MAX_TIMEOUT = 2 ** 31 - 1;

/**
 * Guardia de las vistas protegidas: sin sesión válida no se pinta nada y se
 * manda a /login.
 *
 * Es una comprobación en el navegador, y basta porque aquí ninguna página
 * pide datos desde el servidor: todo lo que se ve llega de la API, y la API
 * exige el token en cada petición. La guardia no protege los datos (eso lo
 * hace la API), evita enseñar pantallas vacías a quien no ha entrado.
 *
 * - Al quedarse sin sesión, vuelve a /login. Si la cerró la persona, sin
 *   más; si terminó sola (caducó, 401, otra pestaña), con un aviso y con la
 *   página actual en ?next= para devolverla ahí después.
 * - Con sesión, programa su cierre para el momento en que caduca el token:
 *   así no hace falta esperar a que una petición falle para notarlo.
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const sesion = useSession();
  // ¿Hubo sesión mientras esta vista estaba abierta? Si se pierde, terminó sola.
  const habiaSesion = useRef(false);

  useEffect(() => {
    if (sesion === null) return;

    if (sesion) {
      habiaSesion.current = true;
      const restante = sessionTimeLeft();
      if (restante === null) return;
      const temporizador = window.setTimeout(() => clearToken(), Math.min(restante, MAX_TIMEOUT));
      return () => window.clearTimeout(temporizador);
    }

    if (lastSessionEnd() === "logout") {
      router.replace(LOGIN_PATH);
      return;
    }

    // Un token guardado que ya no vale (caducado o mal formado) también es
    // una sesión que terminó, aunque se abriera la página con él.
    const caducada = habiaSesion.current || lastSessionEnd() === "ended" || getToken() !== null;
    const aqui = window.location.pathname + window.location.search;
    // replace y no push: "atrás" desde /login no debe volver a esta página.
    router.replace(loginUrl(aqui, window.location.origin, caducada));
  }, [sesion, router]);

  if (sesion !== true) {
    return (
      <p role="status" className="py-24 text-center text-sm text-slate-400">
        Comprobando la sesión…
      </p>
    );
  }

  return children;
}
