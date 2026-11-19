"use client";

import { useCallback, useState } from "react";
import IncidentManagerFilters from "@/components/IncidentManagerFilters";
import IncidentManagerList from "@/components/IncidentManagerList";
import IncidentSummaryPanel from "@/components/IncidentSummaryPanel";

/**
 * Resumen, filtros y lista del gestor. Lo único que comparten es `revision`:
 * cuando la lista confirma un cambio de estado, el resumen se vuelve a pedir.
 * Cada parte carga sus datos por su cuenta, así que un fallo en una no tumba
 * a las demás.
 */
export default function IncidentManager() {
  const [revision, setRevision] = useState(0);
  const alCambiarEstado = useCallback(() => setRevision((n) => n + 1), []);

  return (
    <>
      <IncidentSummaryPanel revision={revision} />
      <IncidentManagerFilters />
      <IncidentManagerList onEstadoCambiado={alCambiarEstado} />
    </>
  );
}
