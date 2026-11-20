import Link from "next/link";

/**
 * 404 del backoffice: una URL que no existe o una pantalla que llama a
 * `notFound()`. Sin esto, Next enseña su página en inglés.
 *
 * Va en la raíz, fuera de (protected): una dirección mal escrita no tiene por
 * qué pedir sesión. El enlace lleva al panel, y si no hay sesión, la
 * protección de rutas lleva de ahí a /login.
 */
export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <div className="rounded-lg border border-marca-800 bg-marca-900 p-6 text-sm">
        <p className="text-xs uppercase tracking-wider text-acento-400">Error 404</p>
        <h1 className="mt-1 text-lg font-semibold text-white">Esta página no existe</h1>
        <p className="mt-2 text-slate-300">
          Puede que la dirección esté mal escrita o que la página se haya movido.
        </p>
        <Link
          href="/"
          className="mt-5 inline-block rounded-md bg-acento-500 px-3 py-1.5 font-medium text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Volver al panel
        </Link>
      </div>
    </main>
  );
}
