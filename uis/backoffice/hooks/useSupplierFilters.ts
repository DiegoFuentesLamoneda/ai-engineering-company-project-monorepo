"use client";

import { useSearchParams } from "next/navigation";
import { CATEGORY_VALUES, COUNTRY_VALUES } from "@/lib/labels";
import type { Category, Country, SupplierFilters } from "@/types/supplier";

/**
 * Lee los filtros del directorio desde la URL.
 * Nunca se confia en el valor crudo: la URL la puede editar cualquiera, y la
 * API responderia 422 a un pais o una categoria fuera del BRIEFING.
 */
export function useSupplierFilters(): SupplierFilters {
  const searchParams = useSearchParams();

  const paisCrudo = searchParams.get("country");
  const categoriaCruda = searchParams.get("category");

  return {
    country: COUNTRY_VALUES.includes(paisCrudo as Country) ? (paisCrudo as Country) : undefined,
    category: CATEGORY_VALUES.includes(categoriaCruda as Category)
      ? (categoriaCruda as Category)
      : undefined,
  };
}
