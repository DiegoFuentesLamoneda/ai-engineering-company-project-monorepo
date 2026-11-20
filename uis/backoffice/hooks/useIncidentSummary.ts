"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getIncidentSummary } from "@/lib/api";
import type { IncidentSummary } from "@/types/incident-manager";

interface EstadoResumen {
  summary: IncidentSummary | null;
  isLoading: boolean;
  error: string | null;
  recargar: () => void;
}

/**
 * El resumen del gestor. Va aparte de la lista a propósito: si /summary falla,
 * falla solo el panel y la lista sigue funcionando.
 *
 * `revision` lo sube la página cada vez que se confirma un cambio de estado:
 * el resumen se vuelve a pedir y los totales no se quedan atrasados.
 */
export function useIncidentSummary(revision: number): EstadoResumen {
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setIsLoading(true);
      setError(null);
      try {
        const respuesta = await getIncidentSummary();
        if (!cancelado) setSummary(respuesta);
      } catch (e) {
        if (cancelado) return;
        setError(e instanceof ApiError ? e.message : "Error inesperado.");
        setSummary(null);
      } finally {
        if (!cancelado) setIsLoading(false);
      }
    }

    cargar();

    return () => {
      cancelado = true;
    };
  }, [revision, intento]);

  const recargar = useCallback(() => setIntento((n) => n + 1), []);

  return { summary, isLoading, error, recargar };
}
