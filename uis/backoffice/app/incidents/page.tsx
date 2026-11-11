import type { Metadata } from "next";
import IncidentAnalyzer from "@/components/IncidentAnalyzer";

export const metadata: Metadata = {
  title: "Análisis de incidencias · Backoffice · Nexova Solutions",
};

/**
 * Analisis de la exportacion CSV del helpdesk de soporte (Roberto Diaz,
 * Customer Support Lead). La pagina es un Server Component; la subida y el
 * resultado viven en IncidentAnalyzer, que es la parte interactiva.
 */
export default function IncidentsPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Análisis de incidencias
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-400">
          Sube la exportación del helpdesk para ver cuántos tickets son válidos,
          su reparto por categoría y estado, y la satisfacción de los tickets
          cerrados. El email de los clientes no aparece en ninguna parte del
          resultado.
        </p>
      </header>

      <IncidentAnalyzer />
    </div>
  );
}
