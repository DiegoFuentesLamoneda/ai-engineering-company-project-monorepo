"use client";

import { useRef, useState } from "react";
import { ApiError, analyzeIncidents } from "@/lib/api";
import type { IncidentAnalysis } from "@/types/incident";

/**
 * Sube un CSV a la API y guarda su analisis.
 *
 * No vive en la URL, como los filtros del tracker: un fichero no cabe en una
 * direccion. Si se recarga la pagina, se vuelve a subir.
 */
export function useIncidentAnalysis() {
  const [analysis, setAnalysis] = useState<IncidentAnalysis | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Si se suelta un segundo fichero antes de que termine el primero, solo
  // cuenta la ultima respuesta: la anterior puede llegar despues y pisarla.
  const ultimaPeticion = useRef(0);

  async function analyze(file: File) {
    const peticion = ++ultimaPeticion.current;

    setIsLoading(true);
    setError(null);
    setFileName(file.name);

    try {
      const datos = await analyzeIncidents(file);
      if (peticion !== ultimaPeticion.current) return;
      setAnalysis(datos);
    } catch (e) {
      if (peticion !== ultimaPeticion.current) return;
      setError(e instanceof ApiError ? e.message : "Error inesperado.");
      // Un analisis fallido no deja en pantalla el anterior: se veria como si
      // fuera el del fichero nuevo.
      setAnalysis(null);
    } finally {
      if (peticion === ultimaPeticion.current) setIsLoading(false);
    }
  }

  return { analysis, fileName, isLoading, error, analyze };
}
