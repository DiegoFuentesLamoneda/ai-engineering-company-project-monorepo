"use client";

import { useSearchParams } from "next/navigation";
import {
  BRANCH_VALUES,
  MANAGER_CATEGORY_VALUES,
  MANAGER_STATUS_VALUES,
  ORIGIN_VALUES,
} from "@/lib/labels";
import type { IncidentFilters } from "@/types/incident-manager";

/** El valor de la URL si es uno de los permitidos; si no, ningún filtro. */
function valido<T extends string>(crudo: string | null, permitidos: readonly T[]): T | undefined {
  return permitidos.includes(crudo as T) ? (crudo as T) : undefined;
}

/**
 * Lee los filtros del gestor desde la URL. Nunca se confía en el valor crudo:
 * la URL la puede editar cualquiera, y la API respondería 400 a un estado o
 * una sede fuera del briefing.
 */
export function useIncidentFilters(): IncidentFilters {
  const searchParams = useSearchParams();

  return {
    status: valido(searchParams.get("status"), MANAGER_STATUS_VALUES),
    origin: valido(searchParams.get("origin"), ORIGIN_VALUES),
    branch: valido(searchParams.get("branch"), BRANCH_VALUES),
    category: valido(searchParams.get("category"), MANAGER_CATEGORY_VALUES),
  };
}
