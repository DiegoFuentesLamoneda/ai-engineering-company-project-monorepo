import type { Country, Currency } from "@/types/supplier";

/**
 * Reglas del directorio de proveedores que necesita la interfaz.
 * Salen de las "Restricciones de negocio" del BRIEFING
 * (docs/contexts/proyectos/supplier-directory.es.md).
 */

/** Cada pais factura en su moneda. La API rechaza cualquier otra combinacion. */
export const CURRENCY_BY_COUNTRY: Record<Country, Currency> = {
  Spain: "EUR",
  USA: "USD",
};

/** Los proveedores que renuevan en este plazo se destacan en el listado. */
export const DIAS_AVISO_RENOVACION = 60;

const MS_POR_DIA = 24 * 60 * 60 * 1000;

/**
 * Dias que faltan hasta la renovacion (0 = hoy, negativo = ya paso).
 *
 * La fecha llega como "YYYY-MM-DD", sin hora. new Date("2026-12-01") la
 * leeria como medianoche en UTC, que en Miami es todavia el dia anterior:
 * por eso se monta en la hora local.
 */
export function diasHastaRenovacion(fecha: string, hoy: Date = new Date()): number | null {
  const [anio, mes, dia] = fecha.split("-").map(Number);
  if (!anio || !mes || !dia) return null;

  const renovacion = new Date(anio, mes - 1, dia);
  const inicioDeHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());

  // Math.round absorbe la hora de diferencia de los cambios de horario.
  return Math.round((renovacion.getTime() - inicioDeHoy.getTime()) / MS_POR_DIA);
}

/** Renueva hoy o en los proximos 60 dias. */
export function renuevaPronto(fecha: string | null, hoy: Date = new Date()): boolean {
  if (!fecha) return false;
  const dias = diasHastaRenovacion(fecha, hoy);
  return dias !== null && dias >= 0 && dias <= DIAS_AVISO_RENOVACION;
}
