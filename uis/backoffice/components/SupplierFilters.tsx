"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CATEGORY_LABELS, CATEGORY_VALUES, COUNTRY_LABELS, COUNTRY_VALUES } from "@/lib/labels";

const CLASE_CAMPO =
  "rounded-md border border-marca-700 bg-marca-900 px-3 py-2 text-sm text-slate-100 " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400";

/**
 * Filtros por pais y categoria. Viven en la URL: "/suppliers?country=USA&
 * category=ats_software" responde a "¿que ATS tenemos en EE. UU.?" y se
 * puede pasar como enlace. router.replace cambia la URL sin recargar.
 */
export default function SupplierFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function actualizarFiltro(clave: "country" | "category", valor: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (valor) {
      params.set(clave, valor);
    } else {
      params.delete(clave);
    }
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  const hayFiltros = searchParams.has("country") || searchParams.has("category");

  return (
    <div className="mb-6 flex flex-wrap items-end gap-3">
      <div>
        <label htmlFor="filtro-pais" className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
          País
        </label>
        <select
          id="filtro-pais"
          value={searchParams.get("country") ?? ""}
          onChange={(evento) => actualizarFiltro("country", evento.target.value)}
          className={CLASE_CAMPO}
        >
          <option value="">Todos los países</option>
          {COUNTRY_VALUES.map((valor) => (
            <option key={valor} value={valor}>
              {COUNTRY_LABELS[valor]}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="filtro-categoria" className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
          Categoría
        </label>
        <select
          id="filtro-categoria"
          value={searchParams.get("category") ?? ""}
          onChange={(evento) => actualizarFiltro("category", evento.target.value)}
          className={CLASE_CAMPO}
        >
          <option value="">Todas las categorías</option>
          {CATEGORY_VALUES.map((valor) => (
            <option key={valor} value={valor}>
              {CATEGORY_LABELS[valor]}
            </option>
          ))}
        </select>
      </div>

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
