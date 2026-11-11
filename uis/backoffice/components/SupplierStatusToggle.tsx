"use client";

import { useState } from "react";
import { ApiError, updateSupplierStatus } from "@/lib/api";
import { SUPPLIER_STATUS_BADGE_STYLES, SUPPLIER_STATUS_LABELS } from "@/lib/labels";
import type { Supplier } from "@/types/supplier";

interface Props {
  supplier: Supplier;
  onActualizado: (supplier: Supplier) => void;
}

/**
 * Estado de una fila y el boton para cambiarlo. Suspender no borra: el
 * proveedor sigue en el directorio para conservar el historial (BRIEFING).
 */
export default function SupplierStatusToggle({ supplier, onActualizado }: Props) {
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activo = supplier.status === "active";
  const accion = activo ? "Suspender" : "Reactivar";

  async function cambiar() {
    if (guardando) return;
    setGuardando(true);
    setError(null);
    try {
      onActualizado(await updateSupplierStatus(supplier.id, activo ? "suspended" : "active"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se ha podido cambiar el estado.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2">
        <span
          className={`inline-block rounded-full px-2.5 py-1 text-xs font-medium ${SUPPLIER_STATUS_BADGE_STYLES[supplier.status]}`}
        >
          {SUPPLIER_STATUS_LABELS[supplier.status]}
        </span>
        <button
          type="button"
          onClick={cambiar}
          disabled={guardando}
          aria-label={`${accion} ${supplier.name}`}
          className="rounded-md border border-marca-600 px-2 py-1 text-xs font-medium text-slate-200 transition-colors hover:border-acento-400 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {guardando ? "…" : accion}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-1 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
