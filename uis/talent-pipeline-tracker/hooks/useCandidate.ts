"use client";

import { useEffect, useState } from "react";
import { ApiError, getCandidate } from "@/lib/api";
import type { Candidate } from "@/types/candidate";

/**
 * Carga una candidatura por id.
 * Devuelve tambien setCandidate para que quien mute (PATCH, PUT) pueda
 * refrescar la vista con la respuesta del servidor, sin volver a pedirla.
 */
export function useCandidate(id: string) {
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setIsLoading(true);
      setError(null);

      try {
        const datos = await getCandidate(id);
        if (cancelado) return;
        setCandidate(datos);
      } catch (e) {
        if (cancelado) return;
        setError(e instanceof ApiError ? e.message : "Error inesperado.");
        setCandidate(null);
      } finally {
        if (!cancelado) setIsLoading(false);
      }
    }

    cargar();

    return () => {
      cancelado = true;
    };
  }, [id]);

  return { candidate, setCandidate, isLoading, error };
}
