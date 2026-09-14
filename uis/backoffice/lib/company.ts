/**
 * Datos de Nexova Solutions tomados de CONTEXT.md, el briefing de la empresa.
 *
 * Regla: si un dato no esta en CONTEXT.md, no esta aqui. No se inventan
 * cifras, nombres ni clientes — ver .agents/rules/contexto-de-empresa.md.
 */

export const COMPANY = {
  name: "Nexova Solutions",
  tagline: "Consultoría de recursos humanos y selección de talento",
  foundedIn: 2011,
  headcount: 120,
  offices: ["Valencia · sede central", "Miami · oficina de expansión"],
} as const;

export interface BusinessLine {
  name: string;
  description: string;
}

/** Las tres lineas de negocio de la empresa. */
export const BUSINESS_LINES: BusinessLine[] = [
  {
    name: "Headhunting",
    description: "Selección de mandos medios y perfiles directivos por encargo del cliente.",
  },
  {
    name: "Outsourcing de soporte",
    description: "Equipos de atención al cliente dedicados para empresas de tecnología, retail y finanzas.",
  },
  {
    name: "Formación corporativa",
    description: "Programas de liderazgo, comunicación y gestión de equipos para empresas cliente.",
  },
];

export interface Area {
  name: string;
  /** null cuando el briefing no lo fija de forma unívoca. */
  lead: string | null;
  team: string;
}

/** Areas de la empresa con su responsable y el tamaño de su equipo. */
export const AREAS: Area[] = [
  { name: "Operaciones de Selección", lead: "Javier Almeida", team: "40 consultores" },
  { name: "Soporte al Cliente", lead: "Roberto Díaz", team: "30 agentes" },
  { name: "Ventas y Desarrollo de Negocio", lead: null, team: "18 personas" },
  { name: "Formación Corporativa", lead: "Elena Vargas", team: "12 personas" },
  { name: "Tecnología e Infraestructura", lead: "Sergio Molina · CTO", team: "6 personas" },
  { name: "Recursos Humanos", lead: "Patricia Solís", team: "4 personas" },
  { name: "Dirección Ejecutiva", lead: "Laura Mendoza · CEO", team: "—" },
];

/** El proceso de seleccion que soporta hoy esta herramienta. */
export const ACTIVE_PROCESS = {
  position: "Asistente de Dirección",
  office: "Sede de Valencia",
  profile:
    "Experiencia en asistencia ejecutiva, gestión de agenda y viajes, inglés y español profesionales.",
  requestedBy: "Elena Vargas · Formación Corporativa",
} as const;
