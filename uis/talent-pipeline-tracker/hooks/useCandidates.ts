"use client";

import { useEffect, useState } from "react";
import { ApiError, getCandidates, type CandidateFilters } from "@/lib/api";
import type { Candidate } from "@/types/candidate";

interface EstadoCandidaturas {
  candidates: Candidate[];
  total: number;
  isLoading: boolean;
  error: string | null;
}

/**
 * Obtiene las candidaturas que coinciden con los filtros.
 * Encapsula los tres estados (cargando, error, datos) y la cancelacion.
 */
export function useCandidates(filters: CandidateFilters): EstadoCandidaturas {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Los objetos se comparan por referencia, asi que usamos una clave estable
  // para que el efecto solo se dispare cuando cambie el contenido del filtro.
  const claveFiltros = JSON.stringify(filters);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setIsLoading(true);
      setError(null);

      try {
        const respuesta = await getCandidates(JSON.parse(claveFiltros));
        if (cancelado) return;
        setCandidates(respuesta.data);
        setTotal(respuesta.total);
      } catch (e) {
        if (cancelado) return;
        setError(e instanceof ApiError ? e.message : "Error inesperado.");
        setCandidates([]);
        setTotal(0);
      } finally {
        if (!cancelado) setIsLoading(false);
      }
    }

    cargar();

    return () => {
      // Descarta la respuesta si mientras tanto han cambiado los filtros.
      cancelado = true;
    };
  }, [claveFiltros]);

  return { candidates, total, isLoading, error };
}
