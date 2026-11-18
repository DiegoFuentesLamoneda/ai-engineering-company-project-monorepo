/** Fechas ISO de la API -> formato legible en espanol. */
export function formatearFecha(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "—";

  return fecha.toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

/** Fecha con hora, para las notas internas. */
export function formatearFechaHora(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "—";

  return fecha.toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Numero con separadores en espanol: 1000000 -> "1.000.000". */
export function formatearNumero(valor: number, decimales = 0): string {
  return valor.toLocaleString("es-ES", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  });
}

/** Porcentaje que ya llega calculado de la API: 29.2 -> "29,2 %". */
export function formatearPorcentaje(valor: number): string {
  return `${formatearNumero(valor, 1)} %`;
}
