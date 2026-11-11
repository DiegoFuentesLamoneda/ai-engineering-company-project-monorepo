"use client";

import { useState } from "react";
import { ApiError, updateSupplierRate } from "@/lib/api";
import { formatearFechaHora, formatearMoneda } from "@/lib/format";
import type { Supplier } from "@/types/supplier";

const CLASE_BOTON =
  "rounded-md px-2 py-1 text-xs font-medium focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400 disabled:cursor-not-allowed disabled:opacity-40";

interface Props {
  supplier: Supplier;
  onActualizado: (supplier: Supplier) => void;
}

/**
 * Tarifa mensual de una fila: se lee y, con "Cambiar", se edita en el sitio.
 * Debajo, la fecha del ultimo cambio: es el dato con el que Patricia
 * justifica las variaciones de presupuesto.
 */
export default function SupplierRateEditor({ supplier, onActualizado }: Props) {
  const [editando, setEditando] = useState(false);
  const [valor, setValor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  const idInput = `tarifa-${supplier.id}`;

  function empezar() {
    setValor(String(supplier.monthly_rate));
    setError(null);
    setEditando(true);
  }

  function cancelar() {
    setEditando(false);
    setError(null);
  }

  async function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    if (guardando) return;

    // Misma regla que la API (> 0), comprobada antes de enviar.
    const tarifa = Number(valor.replace(",", "."));
    if (valor.trim() === "" || !Number.isFinite(tarifa) || tarifa <= 0) {
      setError("Introduce un importe mayor que cero.");
      return;
    }

    setGuardando(true);
    setError(null);
    try {
      onActualizado(await updateSupplierRate(supplier.id, tarifa));
      setEditando(false);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 422
          ? "La API ha rechazado el importe: tiene que ser mayor que cero."
          : e instanceof ApiError
            ? e.message
            : "No se ha podido guardar la tarifa.",
      );
    } finally {
      setGuardando(false);
    }
  }

  if (!editando) {
    return (
      <div>
        <div className="flex items-center gap-2">
          <span className="font-medium tabular-nums text-slate-100">
            {formatearMoneda(supplier.monthly_rate, supplier.currency)}
          </span>
          <button
            type="button"
            onClick={empezar}
            aria-label={`Cambiar la tarifa de ${supplier.name}`}
            className={`${CLASE_BOTON} text-acento-400 underline underline-offset-4 hover:text-acento-300`}
          >
            Cambiar
          </button>
        </div>
        <span className="block text-xs text-slate-500">
          Desde el {formatearFechaHora(supplier.updated_at)}
        </span>
      </div>
    );
  }

  return (
    <form onSubmit={guardar} noValidate className="min-w-48">
      <label htmlFor={idInput} className="sr-only">
        Nueva tarifa mensual de {supplier.name} en {supplier.currency}
      </label>
      <div className="flex items-center gap-1.5">
        <input
          id={idInput}
          type="number"
          inputMode="decimal"
          min="0.01"
          step="0.01"
          value={valor}
          autoFocus
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${idInput}-error` : undefined}
          onChange={(evento) => setValor(evento.target.value)}
          onKeyDown={(evento) => {
            if (evento.key === "Escape") cancelar();
          }}
          className="w-24 rounded-md border border-marca-700 bg-marca-950 px-2 py-1 text-sm text-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        />
        <span className="text-xs text-slate-400">{supplier.currency}</span>
        <button
          type="submit"
          disabled={guardando}
          className={`${CLASE_BOTON} bg-acento-500 text-marca-950 hover:bg-acento-400`}
        >
          {guardando ? "…" : "Guardar"}
        </button>
        <button
          type="button"
          onClick={cancelar}
          className={`${CLASE_BOTON} text-slate-300 hover:text-white`}
        >
          Cancelar
        </button>
      </div>
      {error && (
        <p id={`${idInput}-error`} role="alert" className="mt-1 text-xs text-red-300">
          {error}
        </p>
      )}
    </form>
  );
}
