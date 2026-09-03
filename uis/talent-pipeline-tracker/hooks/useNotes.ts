"use client";

import { useEffect, useState } from "react";
import { ApiError, getNotes } from "@/lib/api";
import type { Note } from "@/types/candidate";

/**
 * Carga las notas de una candidatura.
 * Expone setNotes para que anadir o borrar actualice la lista en memoria
 * sin tener que volver a pedirla entera.
 */
export function useNotes(recordId: string) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setIsLoading(true);
      setError(null);

      try {
        const datos = await getNotes(recordId);
        if (cancelado) return;
        setNotes(datos);
      } catch (e) {
        if (cancelado) return;
        setError(e instanceof ApiError ? e.message : "Error inesperado.");
        setNotes([]);
      } finally {
        if (!cancelado) setIsLoading(false);
      }
    }

    cargar();

    return () => {
      cancelado = true;
    };
  }, [recordId]);

  return { notes, setNotes, isLoading, error };
}
