"use client";

import { useState } from "react";
import { ApiError, downloadIncidentResults } from "@/lib/api";

/** Mismo nombre que el fichero que escribe scripts/analyze.py. */
const NOMBRE_FICHERO = "results.csv";

/**
 * Descarga el CSV de resultados (una metrica por fila) del ultimo analisis.
 *
 * La peticion va por fetch y no por un <a href> directo a la API para pasar
 * por lib/api.ts: asi un 404 o un servidor caido se ven como un mensaje en
 * pantalla, y no como una pestana nueva con un JSON de error.
 */
export default function IncidentDownloadButton() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function descargar() {
    setIsLoading(true);
    setError(null);

    try {
      const blob = await downloadIncidentResults();

      // El navegador solo descarga desde un enlace: se crea uno temporal que
      // apunta al blob en memoria, se pulsa y se libera.
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = NOMBRE_FICHERO;
      enlace.click();
      // Se libera en el siguiente ciclo, cuando la descarga ya ha arrancado.
      setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error inesperado.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <button
        type="button"
        onClick={descargar}
        disabled={isLoading}
        className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 disabled:cursor-wait disabled:opacity-60"
      >
        {isLoading ? "Preparando la descarga…" : "Descargar resultados (CSV)"}
      </button>

      {error && (
        <p role="alert" className="text-sm text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
