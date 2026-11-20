"use client";

import Link from "next/link";
import { useIncidentSummary } from "@/hooks/useIncidentSummary";
import {
  BRANCH_LABELS,
  BRANCH_VALUES,
  MANAGER_CATEGORY_LABELS,
  MANAGER_CATEGORY_VALUES,
  MANAGER_STATUS_BADGE_STYLES,
  MANAGER_STATUS_LABELS,
  MANAGER_STATUS_VALUES,
  ORIGIN_LABELS,
  ORIGIN_VALUES,
  SLA_BREACH_CATEGORY,
} from "@/lib/labels";

const CLASE_TARJETA =
  "rounded-lg border bg-marca-900 p-4 transition-colors focus-visible:outline-2 " +
  "focus-visible:outline-offset-2 focus-visible:outline-acento-400";

interface RepartoProps {
  titulo: string;
  valores: readonly string[];
  textos: Record<string, string>;
  cuentas: Record<string, number>;
  /** Un valor que se pinta en rojo: las críticas en el reparto por categoría. */
  destacado?: string;
}

/** Una lista de barras, en el orden del briefing, con todos los valores aunque estén a 0. */
function Reparto({ titulo, valores, textos, cuentas, destacado }: RepartoProps) {
  const maximo = Math.max(1, ...valores.map((v) => cuentas[v] ?? 0));

  return (
    <div className="rounded-lg border border-marca-800 bg-marca-900 p-4">
      <h3 className="text-sm font-semibold text-white">{titulo}</h3>
      <ul className="mt-3 space-y-2">
        {valores.map((valor) => {
          const cuenta = cuentas[valor] ?? 0;
          const esDestacado = valor === destacado;
          return (
            <li key={valor} className="flex items-center gap-3 text-xs">
              <span className={`w-40 shrink-0 ${esDestacado ? "text-red-200" : "text-slate-300"}`}>
                {textos[valor] ?? valor}
              </span>
              <span className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-marca-950">
                <span
                  className={`block h-full rounded-full ${esDestacado ? "bg-red-500" : "bg-acento-500"}`}
                  style={{ width: `${(cuenta / maximo) * 100}%` }}
                />
              </span>
              <span className="w-6 shrink-0 text-right tabular-nums text-white">{cuenta}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

interface Props {
  /** Sube con cada cambio de estado confirmado: el resumen se vuelve a pedir. */
  revision: number;
}

/**
 * Los totales del gestor: cuántas hay en cada estado, cuántas son críticas y
 * cómo se reparten por sede, origen y categoría. Son de todas las incidencias,
 * no de los filtros activos.
 */
export default function IncidentSummaryPanel({ revision }: Props) {
  const { summary, isLoading, error, recargar } = useIncidentSummary(revision);

  // Si /summary falla, el aviso ocupa una línea y la lista sigue debajo.
  if (error) {
    return (
      <section
        aria-label="Resumen de incidencias"
        className="mb-8 flex flex-wrap items-center gap-3 rounded-lg border border-amber-800 bg-amber-950/60 px-4 py-3 text-sm text-amber-100"
      >
        <p>No se ha podido cargar el resumen. La lista de abajo sigue disponible.</p>
        <button
          type="button"
          onClick={recargar}
          className="rounded-md border border-amber-500 px-3 py-1 text-xs font-medium hover:bg-amber-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Reintentar
        </button>
      </section>
    );
  }

  // Solo la primera carga muestra el aviso: al refrescar se ven los números anteriores.
  if (!summary) {
    return (
      <p role="status" className="mb-8 text-sm text-slate-400">
        {isLoading ? "Cargando el resumen…" : null}
      </p>
    );
  }

  // Si a la respuesta le falta un reparto, sus cifras salen a 0 en vez de romper el panel.
  const total = summary.total ?? 0;
  const porEstado = summary.by_status ?? {};
  const porCategoria = summary.by_category ?? {};
  const criticas = porCategoria[SLA_BREACH_CATEGORY] ?? 0;

  return (
    <section aria-labelledby="titulo-resumen" className="mb-8 space-y-4">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="titulo-resumen" className="text-lg font-semibold text-white">
          Resumen
        </h2>
        <p className="text-xs text-slate-400">
          {total} {total === 1 ? "incidencia" : "incidencias"} en total, sin
          filtros
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {MANAGER_STATUS_VALUES.map((estado) => (
          <Link
            key={estado}
            href={`/incidents?status=${estado}`}
            scroll={false}
            className={`${CLASE_TARJETA} border-marca-800 hover:border-marca-600`}
          >
            <span
              className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${MANAGER_STATUS_BADGE_STYLES[estado]}`}
            >
              {MANAGER_STATUS_LABELS[estado]}
            </span>
            <p className="mt-3 text-3xl font-semibold tabular-nums text-white">
              {porEstado[estado] ?? 0}
            </p>
          </Link>
        ))}

        <Link
          href={`/incidents?category=${SLA_BREACH_CATEGORY}`}
          scroll={false}
          className={`${CLASE_TARJETA} border-red-700 hover:border-red-500`}
        >
          <span className="text-xs font-medium text-red-200">Incumplimientos de SLA</span>
          <p className="mt-3 text-3xl font-semibold tabular-nums text-white">{criticas}</p>
          <span className="text-xs text-slate-400">de cualquier estado</span>
        </Link>
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        <Reparto
          titulo="Por sede"
          valores={BRANCH_VALUES}
          textos={BRANCH_LABELS}
          cuentas={summary.by_branch ?? {}}
        />
        <Reparto
          titulo="Por quién la reporta"
          valores={ORIGIN_VALUES}
          textos={ORIGIN_LABELS}
          cuentas={summary.by_origin ?? {}}
        />
        <Reparto
          titulo="Por categoría"
          valores={MANAGER_CATEGORY_VALUES}
          textos={MANAGER_CATEGORY_LABELS}
          cuentas={porCategoria}
          destacado={SLA_BREACH_CATEGORY}
        />
      </div>
    </section>
  );
}
