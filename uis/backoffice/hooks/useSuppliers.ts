"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getSuppliers } from "@/lib/api";
import type { Supplier, SupplierFilters } from "@/types/supplier";

interface EstadoProveedores {
  suppliers: Supplier[];
  isLoading: boolean;
  error: string | null;
  /** Sustituye una fila por la version que acaba de devolver la API. */
  reemplazar: (actualizado: Supplier) => void;
}

/**
 * Obtiene los proveedores que coinciden con los filtros: cargando, error,
 * datos y cancelacion, como useCandidates.
 */
export function useSuppliers(filters: SupplierFilters): EstadoProveedores {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Clave estable: el efecto solo se repite si cambia el contenido del filtro.
  const claveFiltros = JSON.stringify(filters);

  useEffect(() => {
    let cancelado = false;

    async function cargar() {
      setIsLoading(true);
      setError(null);

      try {
        const respuesta = await getSuppliers(JSON.parse(claveFiltros));
        if (cancelado) return;
        setSuppliers(respuesta);
      } catch (e) {
        if (cancelado) return;
        setError(e instanceof ApiError ? e.message : "Error inesperado.");
        setSuppliers([]);
      } finally {
        if (!cancelado) setIsLoading(false);
      }
    }

    cargar();

    return () => {
      // Descarta la respuesta si mientras tanto han cambiado los filtros.
      cancelado = true;
    };
  }, [claveFiltros]);

  // Los PATCH devuelven el proveedor completo: con eso basta para refrescar la
  // fila, sin pedir otra vez la lista. Ni la tarifa ni el estado cambian el
  // pais o las categorias, asi que la fila sigue cumpliendo el filtro.
  const reemplazar = useCallback((actualizado: Supplier) => {
    setSuppliers((anteriores) =>
      anteriores.map((s) => (s.id === actualizado.id ? actualizado : s)),
    );
  }, []);

  return { suppliers, isLoading, error, reemplazar };
}
