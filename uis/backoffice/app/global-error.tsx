"use client"; // Next exige que las páginas de error sean componentes de cliente.

import Link from "next/link";
import "./globals.css";

/**
 * Último recurso: el fallo está en el propio layout raíz, y app/error.tsx no
 * puede pintarse porque vive dentro de él. Sustituye al documento entero, así
 * que trae su propio <html>, <body>, estilos y título (aquí no vale
 * `metadata`).
 *
 * Mismo criterio que app/error.tsx: un texto fijo y legible, nunca
 * `error.message`.
 */
export default function GlobalError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full bg-marca-950 text-slate-100">
        <title>Error · Backoffice · Nexova Solutions</title>
        <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
          <div role="alert" className="rounded-lg border border-red-800 bg-red-950 p-6 text-sm text-red-100">
            <h1 className="text-lg font-semibold text-red-50">El backoffice no se ha podido cargar</h1>
            <p className="mt-2">
              Ha fallado algo al abrir la aplicación. Vuelve a intentarlo; si sigue pasando, avisa al
              equipo de soporte.
            </p>
            {error.digest && <p className="mt-2 text-xs text-red-300">Referencia: {error.digest}</p>}
            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => retry()}
                className="rounded-md border border-red-400 px-3 py-1.5 font-medium text-red-50 transition-colors hover:bg-red-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
              >
                Reintentar
              </button>
              <Link
                href="/"
                className="rounded-md px-3 py-1.5 font-medium text-red-100 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
              >
                Volver al panel
              </Link>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
