"use client"; // Next exige que las páginas de error sean componentes de cliente.

import Link from "next/link";

/**
 * Lo que se ve cuando una pantalla falla al pintarse: un dato con una forma
 * que no se esperaba, un fallo en un componente. Sustituye a la página, pero
 * no al layout raíz, así que el tema y las tipografías siguen.
 *
 * No enseña `error.message`: en un fallo del navegador es el texto técnico
 * («Cannot read properties of undefined…»). El `digest` solo existe en los
 * fallos del servidor y no revela nada: es la referencia para buscarlo en
 * sus registros.
 */
export default function ErrorPage({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <div role="alert" className="rounded-lg border border-red-800 bg-red-950 p-6 text-sm text-red-100">
        <h1 className="text-lg font-semibold text-red-50">Esta pantalla no se ha podido cargar</h1>
        <p className="mt-2">
          Ha fallado algo al mostrarla. Vuelve a intentarlo; si sigue pasando, vuelve al panel.
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
  );
}
