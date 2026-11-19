"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  BRANCH_LABELS,
  BRANCH_VALUES,
  MANAGER_CATEGORY_LABELS,
  MANAGER_CATEGORY_VALUES,
  MANAGER_STATUS_LABELS,
  MANAGER_STATUS_VALUES,
  ORIGIN_LABELS,
  ORIGIN_VALUES,
  SLA_BREACH_CATEGORY,
} from "@/lib/labels";
import type { IncidentFilters } from "@/types/incident-manager";

type Clave = keyof IncidentFilters;

const CLASE_CAMPO =
  "rounded-md border border-marca-700 bg-marca-900 px-3 py-2 text-sm text-slate-100 " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400";

const CLASE_ETIQUETA = "mb-1 block text-xs uppercase tracking-wide text-slate-400";

interface Filtro {
  clave: Clave;
  etiqueta: string;
  todas: string;
  valores: readonly string[];
  textos: Record<string, string>;
}

const FILTROS: Filtro[] = [
  {
    clave: "status",
    etiqueta: "Estado",
    todas: "Todos los estados",
    valores: MANAGER_STATUS_VALUES,
    textos: MANAGER_STATUS_LABELS,
  },
  {
    clave: "origin",
    etiqueta: "Quién la reporta",
    todas: "Todos los orígenes",
    valores: ORIGIN_VALUES,
    textos: ORIGIN_LABELS,
  },
  {
    clave: "branch",
    etiqueta: "Sede",
    todas: "Todas las sedes",
    valores: BRANCH_VALUES,
    textos: BRANCH_LABELS,
  },
  {
    clave: "category",
    etiqueta: "Categoría",
    todas: "Todas las categorías",
    valores: MANAGER_CATEGORY_VALUES,
    textos: MANAGER_CATEGORY_LABELS,
  },
];

/**
 * Filtros por estado, origen, sede y categoría. Viven en la URL:
 * "/incidents?branch=miami_office&status=open" responde a «¿qué tiene Miami
 * sin empezar?» y se puede pasar como enlace. router.replace no recarga.
 */
export default function IncidentManagerFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function actualizar(clave: Clave, valor: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (valor) params.set(clave, valor);
    else params.delete(clave);
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  const hayFiltros = FILTROS.some((f) => searchParams.has(f.clave));
  const soloSla = searchParams.get("category") === SLA_BREACH_CATEGORY;

  return (
    <div className="mb-6 flex flex-wrap items-end gap-3">
      {FILTROS.map((filtro) => (
        <div key={filtro.clave}>
          <label htmlFor={`filtro-${filtro.clave}`} className={CLASE_ETIQUETA}>
            {filtro.etiqueta}
          </label>
          <select
            id={`filtro-${filtro.clave}`}
            value={searchParams.get(filtro.clave) ?? ""}
            onChange={(evento) => actualizar(filtro.clave, evento.target.value)}
            className={CLASE_CAMPO}
          >
            <option value="">{filtro.todas}</option>
            {filtro.valores.map((valor) => (
              <option key={valor} value={valor}>
                {filtro.textos[valor]}
              </option>
            ))}
          </select>
        </div>
      ))}

      {/* El briefing pide que las críticas se filtren sin buscarlas: un clic. */}
      <button
        type="button"
        aria-pressed={soloSla}
        onClick={() => actualizar("category", soloSla ? "" : SLA_BREACH_CATEGORY)}
        className={`rounded-md border px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 ${
          soloSla
            ? "border-red-500 bg-red-950 text-red-100"
            : "border-marca-700 text-slate-200 hover:border-red-500 hover:text-white"
        }`}
      >
        Solo incumplimientos de SLA
      </button>

      {hayFiltros && (
        <button
          type="button"
          onClick={() => router.replace(pathname, { scroll: false })}
          className="rounded-md px-3 py-2 text-sm font-medium text-acento-400 underline underline-offset-4 hover:text-acento-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
