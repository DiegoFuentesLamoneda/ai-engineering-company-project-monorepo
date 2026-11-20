"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getIncidents, updateIncidentStatus } from "@/lib/api";
import type {
  Incident,
  IncidentFilters,
  IncidentManagerStatus,
} from "@/types/incident-manager";

interface EstadoIncidencias {
  incidents: Incident[];
  isLoading: boolean;
  error: string | null;
  /** Vuelve a pedir la lista: el botón «Reintentar». */
  recargar: () => void;
  /**
   * Cambia el estado de una fila al momento y lo confirma con la API. Si la
   * API lo rechaza, la fila vuelve a como estaba y el error se relanza.
   */
  cambiarEstado: (incident: Incident, destino: IncidentManagerStatus) => Promise<void>;
}

/** Las incidencias que cumplen los filtros: cargando, error, datos y cancelación. */
export function useIncidents(filters: IncidentFilters): EstadoIncidencias {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Cada «Reintentar» suma uno y vuelve a lanzar el efecto con los mismos filtros.
  const [intento, setIntento] = useState(0);

  // Clave estable: el efecto solo se repite si cambia el contenido del filtro.
  const claveFiltros = JSON.stringify(filters);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setIsLoading(true);
      setError(null);

      try {
        const respuesta = await getIncidents(JSON.parse(claveFiltros));
        if (cancelado) return;
        setIncidents(respuesta ?? []);
      } catch (e) {
        if (cancelado) return;
        setError(e instanceof ApiError ? e.message : "Error inesperado.");
        setIncidents([]);
      } finally {
        if (!cancelado) setIsLoading(false);
      }
    }

    cargar();

    return () => {
      // Descarta la respuesta si mientras tanto han cambiado los filtros.
      cancelado = true;
    };
  }, [claveFiltros, intento]);

  const recargar = useCallback(() => setIntento((n) => n + 1), []);

  const cambiarEstado = useCallback(
    async (incident: Incident, destino: IncidentManagerStatus) => {
      const sustituir = (nueva: Incident) =>
        setIncidents((anteriores) => anteriores.map((i) => (i.id === nueva.id ? nueva : i)));

      // Optimista: la fila cambia ya, sin esperar a la red.
      sustituir({ ...incident, status: destino });
      try {
        // La respuesta trae el updated_at nuevo: es la versión buena.
        sustituir(await updateIncidentStatus(incident.id, destino));
      } catch (e) {
        // Rechazado: la fila vuelve exactamente a como estaba.
        sustituir(incident);
        throw e;
      }
    },
    [],
  );

  return { incidents, isLoading, error, recargar, cambiarEstado };
}
