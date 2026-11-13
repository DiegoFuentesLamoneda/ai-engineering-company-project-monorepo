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

/** Importe en su moneda: 329 EUR -> "329,00 €", 6500 USD -> "6500,00 US$". */
export function formatearMoneda(valor: number, moneda: string): string {
  return valor.toLocaleString("es-ES", { style: "currency", currency: moneda });
}

/** Fecha sin hora de la API ("2026-12-01") -> "01 dic 2026". */
export function formatearFechaCorta(fecha: string): string {
  const [anio, mes, dia] = fecha.split("-").map(Number);
  if (!anio || !mes || !dia) return "—";

  // En hora local: new Date("2026-12-01") seria medianoche UTC, el dia
  // anterior en Miami.
  return new Date(anio, mes - 1, dia).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}
