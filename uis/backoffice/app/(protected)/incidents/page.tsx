import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import IncidentManager from "@/components/IncidentManager";

export const metadata: Metadata = {
  title: "Incidencias · Backoffice · Nexova Solutions",
};

/**
 * El gestor de incidencias centralizado: lo que antes llegaba por correo,
 * por el Excel de cada oficina o por teléfono, en una sola lista.
 */
export default function IncidentsPage() {
  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">Incidencias</h1>
          <p className="mt-1 max-w-3xl text-sm text-slate-400">
            Las incidencias de clientes, oficinas y detección interna, en un solo sitio
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/incidents/analyze"
            className="rounded-md px-3 py-2 text-sm text-slate-300 underline underline-offset-4 hover:text-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
          >
            Analizar un CSV del helpdesk
          </Link>
          <Link
            href="/incidents/new"
            className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
          >
            Nueva incidencia
          </Link>
        </div>
      </header>

      {/* useSearchParams necesita una frontera de Suspense para poder prerenderizar. */}
      <Suspense fallback={<p className="text-sm text-slate-400">Cargando…</p>}>
        <IncidentManager />
      </Suspense>
    </div>
  );
}
