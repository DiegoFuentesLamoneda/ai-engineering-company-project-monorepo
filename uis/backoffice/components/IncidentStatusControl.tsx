"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api";
import {
  MANAGER_STATUS_BADGE_STYLES,
  MANAGER_STATUS_LABELS,
  MANAGER_STATUS_TRANSITIONS,
} from "@/lib/labels";
import type { Incident, IncidentManagerStatus } from "@/types/incident-manager";

interface Props {
  incident: Incident;
  onCambiar: (incident: Incident, destino: IncidentManagerStatus) => Promise<void>;
}

/**
 * El 409 de la API nombra los estados con su valor crudo ("open"), y el 404
 * habla de IDs: aquí se dice lo mismo con palabras de la pantalla.
 */
function mensajeDeError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 409) {
      return "Alguien ha cambiado esta incidencia mientras tanto. Recarga la lista para ver su estado actual.";
    }
    if (e.status === 404) return "Esta incidencia ya no existe. Recarga la lista.";
    return e.message;
  }
  return "No se ha podido cambiar el estado.";
}

/**
 * El estado de una fila y, si el ciclo de vida lo permite, el desplegable
 * para pasarla al siguiente. Solo ofrece los cambios permitidos.
 */
export default function IncidentStatusControl({ incident, onCambiar }: Props) {
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const destinos = MANAGER_STATUS_TRANSITIONS[incident.status];
  const idSelect = `estado-${incident.id}`;

  async function cambiar(destino: IncidentManagerStatus) {
    if (guardando) return;
    setGuardando(true);
    setError(null);
    try {
      await onCambiar(incident, destino);
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="min-w-40">
      <span
        className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${MANAGER_STATUS_BADGE_STYLES[incident.status]}`}
      >
        {MANAGER_STATUS_LABELS[incident.status]}
      </span>

      {destinos.length > 0 ? (
        <div className="mt-2">
          <label htmlFor={idSelect} className="sr-only">
            Cambiar el estado de «{incident.title}»
          </label>
          <select
            id={idSelect}
            value=""
            disabled={guardando}
            aria-describedby={error ? `${idSelect}-error` : undefined}
            onChange={(evento) => cambiar(evento.target.value as IncidentManagerStatus)}
            className="w-full rounded-md border border-marca-700 bg-marca-950 px-2 py-1 text-xs text-slate-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 disabled:cursor-wait disabled:opacity-50"
          >
            <option value="">{guardando ? "Guardando…" : "Pasar a…"}</option>
            {destinos.map((destino) => (
              <option key={destino} value={destino}>
                {MANAGER_STATUS_LABELS[destino]}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <span className="mt-1 block text-xs text-slate-500">Estado final</span>
      )}

      {error && (
        <p id={`${idSelect}-error`} role="alert" className="mt-1 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
