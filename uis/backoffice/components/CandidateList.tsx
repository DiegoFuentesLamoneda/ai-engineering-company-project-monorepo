"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { STAGE_LABELS, STATUS_BADGE_STYLES, STATUS_LABELS } from "@/lib/labels";
import { useCandidateFilters } from "@/hooks/useCandidateFilters";
import { useCandidates } from "@/hooks/useCandidates";

export default function CandidateList() {
  const filtros = useCandidateFilters();
  // Arrastramos los filtros activos al detalle para poder volver al mismo sitio.
  const consulta = useSearchParams().toString();
  const { candidates, total, isLoading, error } = useCandidates({
    ...filtros,
    limit: 100,
  });

  if (isLoading) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        Cargando candidaturas…
      </p>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se han podido cargar las candidaturas</p>
        <p className="mt-1">{error}</p>
      </div>
    );
  }

  if (candidates.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        No hay candidaturas que coincidan con los filtros.
      </p>
    );
  }

  return (
    <>
      <p className="mb-3 text-sm text-slate-400">
        {candidates.length} de {total} candidaturas
      </p>

      {/* En pantallas grandes solo hace scroll la tabla: los filtros y la
          cabecera de columnas quedan siempre a la vista. En movil se
          desactiva, porque el scroll anidado ahi estorba mas que ayuda. */}
      <div className="overflow-x-auto rounded-lg border border-marca-800 bg-marca-900 shadow-sm md:max-h-[calc(100vh-20rem)] md:overflow-y-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="text-left text-slate-200">
            <tr>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Candidato</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Puesto</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Estado</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Etapa</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate) => (
              <tr key={candidate.id} className="border-t border-marca-800 hover:bg-marca-800">
                <td className="px-4 py-3">
                  <Link
                    href={
                      consulta
                        ? `/candidates/${candidate.id}?${consulta}`
                        : `/candidates/${candidate.id}`
                    }
                    className="font-medium text-acento-400 underline underline-offset-4 hover:text-acento-300"
                  >
                    {candidate.full_name}
                  </Link>
                  <span className="block text-xs text-slate-400">
                    {candidate.email}
                  </span>
                </td>
                <td className="px-4 py-3">{candidate.position}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_BADGE_STYLES[candidate.status]}`}
                  >
                    {STATUS_LABELS[candidate.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">
                  {STAGE_LABELS[candidate.stage]}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
