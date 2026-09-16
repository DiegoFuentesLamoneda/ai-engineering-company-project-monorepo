"use client";

import { useSearchParams } from "next/navigation";
import { STAGE_VALUES, STATUS_VALUES } from "@/lib/labels";
import type { Stage, Status } from "@/types/candidate";

export interface FiltrosActivos {
  status?: Status;
  stage?: Stage;
  search?: string;
}

/**
 * Lee los filtros desde la URL.
 * Nunca se confia en el valor crudo: la URL la puede editar cualquiera.
 */
export function useCandidateFilters(): FiltrosActivos {
  const searchParams = useSearchParams();

  const statusCrudo = searchParams.get("status");
  const stageCrudo = searchParams.get("stage");
  const search = searchParams.get("search") ?? "";

  return {
    status: STATUS_VALUES.includes(statusCrudo as Status)
      ? (statusCrudo as Status)
      : undefined,
    stage: STAGE_VALUES.includes(stageCrudo as Stage)
      ? (stageCrudo as Stage)
      : undefined,
    search: search.trim() || undefined,
  };
}
