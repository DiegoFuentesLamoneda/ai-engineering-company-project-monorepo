"use client";

import IncidentResults from "@/components/IncidentResults";
import IncidentUpload from "@/components/IncidentUpload";
import { useIncidentAnalysis } from "@/hooks/useIncidentAnalysis";

/** Subida del CSV, estados de carga y error, y el resultado. */
export default function IncidentAnalyzer() {
  const { analysis, fileName, isLoading, error, analyze } = useIncidentAnalysis();

  return (
    <div className="space-y-8">
      <IncidentUpload onFile={analyze} disabled={isLoading} />

      {/* role="status" y role="alert": el lector de pantalla anuncia el cambio
          sin que la persona tenga que ir a buscarlo. */}
      {isLoading && (
        <p
          role="status"
          className="rounded-lg border border-marca-800 bg-marca-900 px-4 py-6 text-center text-sm text-slate-300"
        >
          Analizando <span className="break-all font-medium text-white">{fileName}</span>…
        </p>
      )}

      {!isLoading && error && (
        <div
          role="alert"
          className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100"
        >
          <p className="font-medium">No se ha podido analizar el fichero</p>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {!isLoading && analysis && fileName && (
        <IncidentResults analysis={analysis} fileName={fileName} />
      )}
    </div>
  );
}
