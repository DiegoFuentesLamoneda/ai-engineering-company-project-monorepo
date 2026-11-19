"use client";

import Link from "next/link";
import IncidentStatusControl from "@/components/IncidentStatusControl";
import { useIncidentFilters } from "@/hooks/useIncidentFilters";
import { useIncidents } from "@/hooks/useIncidents";
import { formatearFechaHora } from "@/lib/format";
import {
  BRANCH_LABELS,
  MANAGER_CATEGORY_LABELS,
  ORIGIN_LABELS,
  SLA_BREACH_CATEGORY,
} from "@/lib/labels";

const CLASE_CABECERA = "sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium";

export default function IncidentManagerList() {
  const filtros = useIncidentFilters();
  const { incidents, isLoading, error, recargar, cambiarEstado } = useIncidents(filtros);
  const hayFiltros = Object.values(filtros).some(Boolean);

  if (isLoading) {
    return (
      <p role="status" className="py-12 text-center text-sm text-slate-400">
        Cargando incidencias…
      </p>
    );
  }

  if (error) {
    return (
      <div role="alert" className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se han podido cargar las incidencias</p>
        <p className="mt-1">{error}</p>
        <button
          type="button"
          onClick={recargar}
          className="mt-3 rounded-md border border-red-400 px-3 py-1.5 text-sm font-medium text-red-50 transition-colors hover:bg-red-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (incidents.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-marca-700 py-12 text-center text-sm text-slate-400">
        {hayFiltros ? (
          <>
            <p>Ninguna incidencia coincide con los filtros.</p>
            <Link
              href="/incidents"
              scroll={false}
              className="mt-3 inline-block text-acento-400 underline underline-offset-4 hover:text-acento-300"
            >
              Limpiar filtros
            </Link>
          </>
        ) : (
          <>
            <p>Todavía no hay incidencias registradas.</p>
            <Link
              href="/incidents/new"
              className="mt-3 inline-block text-acento-400 underline underline-offset-4 hover:text-acento-300"
            >
              Registrar la primera
            </Link>
          </>
        )}
      </div>
    );
  }

  const criticas = incidents.filter((i) => i.category === SLA_BREACH_CATEGORY).length;

  return (
    <>
      <p className="mb-3 text-sm text-slate-400">
        {incidents.length} {incidents.length === 1 ? "incidencia" : "incidencias"}, la más reciente
        primero
        {criticas > 0 && (
          <span className="text-red-300">
            {" "}
            · {criticas} por incumplimiento de SLA
          </span>
        )}
      </p>

      {/* Como en proveedores: en escritorio solo hace scroll la tabla. */}
      <div className="overflow-x-auto rounded-lg border border-marca-800 bg-marca-900 shadow-sm md:max-h-[calc(100vh-22rem)] md:overflow-y-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="text-left text-slate-200">
            <tr>
              <th className={CLASE_CABECERA}>Incidencia</th>
              <th className={CLASE_CABECERA}>Categoría</th>
              <th className={CLASE_CABECERA}>Quién la reporta</th>
              <th className={CLASE_CABECERA}>Sede</th>
              <th className={CLASE_CABECERA}>Registrada</th>
              <th className={CLASE_CABECERA}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => {
              const critica = incident.category === SLA_BREACH_CATEGORY;
              return (
                <tr
                  key={incident.id}
                  className="border-t border-marca-800 align-top text-slate-200 hover:bg-marca-800"
                >
                  <td className="max-w-md px-4 py-3">
                    <span className="font-medium text-white">{incident.title}</span>
                    <span className="mt-0.5 line-clamp-2 block text-xs text-slate-400">
                      {incident.description}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        critica
                          ? "inline-block rounded border border-red-500 bg-red-950 px-1.5 py-0.5 text-xs font-medium text-red-100"
                          : undefined
                      }
                    >
                      {MANAGER_CATEGORY_LABELS[incident.category]}
                    </span>
                  </td>
                  <td className="px-4 py-3">{ORIGIN_LABELS[incident.origin]}</td>
                  <td className="px-4 py-3">{BRANCH_LABELS[incident.branch]}</td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-400">
                    {formatearFechaHora(incident.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <IncidentStatusControl incident={incident} onCambiar={cambiarEstado} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
