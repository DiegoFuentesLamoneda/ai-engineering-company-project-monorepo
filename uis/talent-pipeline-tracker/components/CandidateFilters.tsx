"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { STAGE_LABELS, STAGE_VALUES, STATUS_LABELS, STATUS_VALUES } from "@/lib/labels";

const CLASE_CAMPO =
  "rounded-md border border-marca-700 bg-marca-900 px-3 py-2 text-sm text-slate-100 " +
  "placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400";

export default function CandidateFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // El input necesita estado propio: se escribe en cada tecla,
  // pero la URL solo se actualiza cuando el usuario deja de teclear.
  const [texto, setTexto] = useState(searchParams.get("search") ?? "");

  useEffect(() => {
    const enLaUrl = searchParams.get("search") ?? "";
    if (texto.trim() === enLaUrl) return;

    const temporizador = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      if (texto.trim()) {
        params.set("search", texto.trim());
      } else {
        params.delete("search");
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }, 300);

    // Cada tecla cancela el temporizador anterior: eso es el debounce.
    return () => clearTimeout(temporizador);
  }, [texto, searchParams, router, pathname]);

  function actualizarFiltro(clave: string, valor: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (valor) {
      params.set(clave, valor);
    } else {
      params.delete(clave);
    }
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }

  function limpiarFiltros() {
    setTexto("");
    router.replace(pathname, { scroll: false });
  }

  const hayFiltros = searchParams.toString().length > 0;

  return (
    <div className="mb-6 flex flex-wrap items-center gap-3">
      <input
        type="search"
        value={texto}
        onChange={(evento) => setTexto(evento.target.value)}
        placeholder="Buscar por nombre o email…"
        aria-label="Buscar candidaturas"
        className={`${CLASE_CAMPO} min-w-64 flex-1`}
      />

      <select
        value={searchParams.get("status") ?? ""}
        onChange={(evento) => actualizarFiltro("status", evento.target.value)}
        aria-label="Filtrar por estado"
        className={CLASE_CAMPO}
      >
        <option value="">Todos los estados</option>
        {STATUS_VALUES.map((valor) => (
          <option key={valor} value={valor}>
            {STATUS_LABELS[valor]}
          </option>
        ))}
      </select>

      <select
        value={searchParams.get("stage") ?? ""}
        onChange={(evento) => actualizarFiltro("stage", evento.target.value)}
        aria-label="Filtrar por etapa"
        className={CLASE_CAMPO}
      >
        <option value="">Todas las etapas</option>
        {STAGE_VALUES.map((valor) => (
          <option key={valor} value={valor}>
            {STAGE_LABELS[valor]}
          </option>
        ))}
      </select>

      {hayFiltros && (
        <button
          type="button"
          onClick={limpiarFiltros}
          className="rounded-md px-3 py-2 text-sm font-medium text-acento-400 underline underline-offset-4 hover:text-acento-300"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
