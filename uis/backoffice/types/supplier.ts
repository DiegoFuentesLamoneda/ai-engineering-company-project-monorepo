/**
 * Contrato del directorio de proveedores (services/api, rutas /suppliers),
 * en TypeScript. Es services/api/app/domains/suppliers/schemas.py: si cambia
 * alli, se cambia aqui.
 *
 * Los valores son literales del BRIEFING (Spain, job_boards, suspended…).
 * Su texto en pantalla sale de lib/labels.ts.
 */

export type Country = "Spain" | "USA";

export type Currency = "EUR" | "USD";

export type Category =
  | "job_boards"
  | "ats_software"
  | "assessment_tools"
  | "training_platforms"
  | "payroll_and_hr_software"
  | "video_interview"
  | "background_check"
  | "office_and_facilities"
  | "it_and_software_licenses";

export type SupplierStatus = "active" | "suspended";

/** Cuerpo de POST /suppliers. Sin id ni updated_at: los pone el sistema. */
export interface SupplierInput {
  name: string;
  country: Country;
  categories: Category[];
  monthly_rate: number;
  currency: Currency;
  status: SupplierStatus;
  /** YYYY-MM-DD. */
  contract_renewal_date: string | null;
  contact_email: string | null;
  notes: string | null;
}

/** Un proveedor tal y como lo devuelve la API. */
export interface Supplier extends SupplierInput {
  id: number;
  /** ISO 8601 en UTC. Fecha del ultimo cambio de tarifa. */
  updated_at: string;
}

/** Filtros de GET /suppliers. Los dos son opcionales y se combinan. */
export interface SupplierFilters {
  country?: Country;
  category?: Category;
}
