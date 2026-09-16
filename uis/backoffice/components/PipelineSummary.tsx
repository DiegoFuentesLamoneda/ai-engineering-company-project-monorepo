"use client";

import Link from "next/link";
import { useCandidates } from "@/hooks/useCandidates";
import {
  STAGE_LABELS,
  STAGE_VALUES,
  STATUS_BADGE_STYLES,
  STATUS_LABELS,
  STATUS_VALUES,
} from "@/lib/labels";
import type { Candidate } from "@/types/candidate";

/**
 * Tamano de la muestra sobre la que se calcula el desglose. La API pagina, asi
 * que si hay mas candidaturas que esto el desglose es parcial y se avisa en
 * pantalla: un panel que ensena numeros parciales como si fueran totales
 * miente, y a partir de ahi nadie se fia de ninguno.
 */
const TAMANO_MUESTRA = 100;

function contarPor(
  candidates: Candidate[],
  campo: "status" | "stage",
  valor: string,
): number {
  return candidates.filter((c) => c[campo] === valor).length;
}

export default function PipelineSummary() {
  const { candidates, total, isLoading, error } = useCandidates({
    limit: TAMANO_MUESTRA,
  });

  if (isLoading) {
    return (
      <p className="rounded-lg border border-marca-800 bg-marca-900 px-4 py-8 text-center text-sm text-slate-400">
        Cargando el estado del proceso…
      </p>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se ha podido cargar el estado del proceso</p>
        <p className="mt-1">{error}</p>
      </div>
    );
  }

  const esParcial = total > candidates.length;
  const maximoPorEtapa = Math.max(
    1,
    ...STAGE_VALUES.map((etapa) => contarPor(candidates, "stage", etapa)),
  );

  return (
    <div className="space-y-6">
      {/* Totales por estado */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {STATUS_VALUES.map((estado) => (
          <Link
            key={estado}
            href={`/candidates?status=${estado}`}
            className="rounded-lg border border-marca-800 bg-marca-900 p-4 transition-colors hover:border-marca-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
          >
            <span
              className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_BADGE_STYLES[estado]}`}
            >
              {STATUS_LABELS[estado]}
            </span>
            <p className="mt-3 text-3xl font-semibold tabular-nums text-white">
              {contarPor(candidates, "status", estado)}
            </p>
          </Link>
        ))}
      </div>

      {/* Reparto por etapa del circuito */}
      <div className="rounded-lg border border-marca-800 bg-marca-900 p-5">
        <h3 className="text-sm font-semibold text-white">Reparto por etapa</h3>

        <ul className="mt-4 space-y-3">
          {STAGE_VALUES.map((etapa) => {
            const cuenta = contarPor(candidates, "stage", etapa);

            return (
              <li key={etapa} className="flex items-center gap-3 text-sm">
                <span className="w-44 shrink-0 text-slate-300">
                  {STAGE_LABELS[etapa]}
                </span>
                <span className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-marca-950">
                  <span
                    className="block h-full rounded-full bg-acento-500"
                    style={{ width: `${(cuenta / maximoPorEtapa) * 100}%` }}
                  />
                </span>
                <span className="w-8 shrink-0 text-right tabular-nums text-white">
                  {cuenta}
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      <p className="text-xs text-slate-400">
        {esParcial ? (
          <>
            Desglose calculado sobre las {candidates.length} candidaturas más
            recientes de un total de {total}.
          </>
        ) : (
          <>Desglose sobre las {total} candidaturas del proceso.</>
        )}
      </p>
    </div>
  );
}
