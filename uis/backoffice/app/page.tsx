import Link from "next/link";
import PipelineSummary from "@/components/PipelineSummary";
import { ACTIVE_PROCESS, AREAS, BUSINESS_LINES, COMPANY } from "@/lib/company";

/**
 * Vista de entrada del backoffice: el estado del proceso de seleccion activo
 * y los datos de la empresa que el equipo necesita tener a mano. Los datos de
 * empresa salen de CONTEXT.md a traves de lib/company.ts; los del pipeline,
 * de la API en vivo.
 */
export default function PanelPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Panel de operaciones
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          {COMPANY.tagline} · Desde {COMPANY.foundedIn} · {COMPANY.headcount}{" "}
          empleados
        </p>
      </header>

      {/* Proceso activo */}
      <section
        aria-labelledby="proceso-activo"
        className="mb-10 rounded-lg border border-marca-800 bg-marca-900 p-5"
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-wider text-acento-400">
              Proceso activo
            </p>
            <h2
              id="proceso-activo"
              className="mt-1 text-xl font-semibold text-white"
            >
              {ACTIVE_PROCESS.position}
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              {ACTIVE_PROCESS.office} · Solicitado por {ACTIVE_PROCESS.requestedBy}
            </p>
          </div>

          <Link
            href="/candidates"
            className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
          >
            Ver candidaturas
          </Link>
        </div>

        <p className="mt-4 max-w-3xl text-sm text-slate-300">
          <span className="text-slate-400">Perfil buscado: </span>
          {ACTIVE_PROCESS.profile}
        </p>
      </section>

      {/* Estado del pipeline, en vivo */}
      <section aria-labelledby="estado-proceso" className="mb-10">
        <h2
          id="estado-proceso"
          className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400"
        >
          Estado del proceso
        </h2>

        {/* El panel se prerenderiza y PipelineSummary pide los datos a la API
            desde el cliente, con sus propios estados de carga y de error. */}
        <PipelineSummary />
      </section>

      {/* Lineas de negocio */}
      <section aria-labelledby="lineas-negocio" className="mb-10">
        <h2
          id="lineas-negocio"
          className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400"
        >
          Líneas de negocio
        </h2>

        <div className="grid gap-3 md:grid-cols-3">
          {BUSINESS_LINES.map((linea) => (
            <article
              key={linea.name}
              className="rounded-lg border border-marca-800 bg-marca-900 p-4"
            >
              <h3 className="font-semibold text-white">{linea.name}</h3>
              <p className="mt-2 text-sm text-slate-400">{linea.description}</p>
            </article>
          ))}
        </div>
      </section>

      {/* Areas y responsables */}
      <section aria-labelledby="areas">
        <h2
          id="areas"
          className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400"
        >
          Áreas y responsables
        </h2>

        <div className="overflow-x-auto rounded-lg border border-marca-800 bg-marca-900">
          <table className="w-full border-collapse text-sm">
            <thead className="text-left text-slate-200">
              <tr>
                <th className="bg-marca-800 px-4 py-3 font-medium">Área</th>
                <th className="bg-marca-800 px-4 py-3 font-medium">Responsable</th>
                <th className="bg-marca-800 px-4 py-3 font-medium">Equipo</th>
              </tr>
            </thead>
            <tbody>
              {AREAS.map((area) => (
                <tr key={area.name} className="border-t border-marca-800">
                  <td className="px-4 py-3 text-white">{area.name}</td>
                  <td className="px-4 py-3 text-slate-300">{area.lead ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{area.team}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-3 text-xs text-slate-400">
          El briefing de la empresa no fija de forma unívoca el responsable de
          Ventas y Desarrollo de Negocio, así que se deja sin asignar en lugar
          de elegir uno.
        </p>
      </section>
    </div>
  );
}
