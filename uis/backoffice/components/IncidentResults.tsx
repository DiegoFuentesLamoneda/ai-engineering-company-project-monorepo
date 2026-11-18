import IncidentDownloadButton from "@/components/IncidentDownloadButton";
import { formatearNumero, formatearPorcentaje } from "@/lib/format";
import {
  INCIDENT_CATEGORY_LABELS,
  INCIDENT_RULE_LABELS,
  INCIDENT_STATUS_LABELS,
  SATISFACTION_SCORE_LABELS,
} from "@/lib/labels";
import type { IncidentAnalysis } from "@/types/incident";

interface Props {
  analysis: IncidentAnalysis;
  fileName: string;
}

/**
 * El analisis de un CSV, tal y como lo devuelve la API. Aqui no se calcula
 * nada: totales, porcentajes y media vienen hechos de packages/incident-analysis,
 * los mismos que imprime el script. Este componente solo los presenta.
 */
export default function IncidentResults({ analysis, fileName }: Props) {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Resultado del análisis</h2>
          <p className="mt-1 break-all text-sm text-slate-400">{fileName}</p>
        </div>
        <IncidentDownloadButton />
      </div>

      <Totals analysis={analysis} />
      <InvalidRecords analysis={analysis} />

      <div className="grid gap-6 lg:grid-cols-2">
        <Breakdown
          id="por-categoria"
          title="Por categoría"
          header="Categoría"
          rows={analysis.by_category.map((fila) => ({
            key: fila.category,
            label: INCIDENT_CATEGORY_LABELS[fila.category],
            count: fila.count,
            percentage: fila.percentage,
          }))}
        />
        <Breakdown
          id="por-estado"
          title="Por estado"
          header="Estado"
          rows={analysis.by_status.map((fila) => ({
            key: fila.status,
            label: INCIDENT_STATUS_LABELS[fila.status],
            count: fila.count,
            percentage: fila.percentage,
          }))}
        />
      </div>

      <SatisfactionIndex analysis={analysis} />
    </div>
  );
}

// --- Totales ---

function Totals({ analysis }: { analysis: IncidentAnalysis }) {
  const tarjetas = [
    { label: "Registros totales", value: analysis.total_records, tone: "text-white" },
    { label: "Válidos", value: analysis.valid_records, tone: "text-emerald-300" },
    {
      label: "Inválidos",
      value: analysis.invalid_records,
      tone: analysis.invalid_records > 0 ? "text-acento-400" : "text-white",
    },
  ];

  return (
    <dl className="grid gap-3 sm:grid-cols-3">
      {tarjetas.map((tarjeta) => (
        <div
          key={tarjeta.label}
          className="rounded-lg border border-marca-800 bg-marca-900 p-4"
        >
          <dt className="text-sm text-slate-400">{tarjeta.label}</dt>
          <dd className={`mt-2 text-3xl font-semibold tabular-nums ${tarjeta.tone}`}>
            {formatearNumero(tarjeta.value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

// --- Registros invalidos ---

function InvalidRecords({ analysis }: { analysis: IncidentAnalysis }) {
  if (analysis.invalid_records === 0) {
    return (
      <p className="rounded-lg border border-emerald-800 bg-emerald-950 px-4 py-3 text-sm text-emerald-100">
        Todos los registros son válidos.
      </p>
    );
  }

  const reglas = analysis.invalid_by_rule.filter((regla) => regla.count > 0);
  const sumaPorRegla = reglas.reduce((suma, regla) => suma + regla.count, 0);
  const muestras = analysis.invalid_samples;

  return (
    <section
      aria-labelledby="registros-invalidos"
      className="rounded-lg border border-acento-600 bg-marca-900 p-5"
    >
      <h3 id="registros-invalidos" className="font-semibold text-acento-300">
        {formatearNumero(analysis.invalid_records)}{" "}
        {analysis.invalid_records === 1
          ? "registro no válido, excluido"
          : "registros no válidos, excluidos"}{" "}
        de las métricas
      </h3>

      <ul className="mt-3 space-y-1 text-sm">
        {reglas.map((regla) => (
          <li key={regla.rule} className="flex justify-between gap-4">
            <span className="text-slate-300">{INCIDENT_RULE_LABELS[regla.rule]}</span>
            <span className="tabular-nums text-white">{formatearNumero(regla.count)}</span>
          </li>
        ))}
      </ul>

      {sumaPorRegla > analysis.invalid_records && (
        <p className="mt-3 text-xs text-slate-400">
          Un registro puede incumplir varias reglas a la vez: por eso la suma es
          mayor que el número de registros no válidos.
        </p>
      )}

      {muestras.length > 0 && (
        <details className="mt-4 text-sm">
          <summary className="cursor-pointer rounded text-acento-400 hover:text-acento-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400">
            Ver en qué filas del fichero están
          </summary>

          <div className="mt-3 overflow-x-auto rounded-md border border-marca-800">
            <table className="w-full border-collapse">
              <thead className="text-left text-slate-200">
                <tr>
                  <th scope="col" className="bg-marca-800 px-3 py-2 font-medium">Línea</th>
                  <th scope="col" className="bg-marca-800 px-3 py-2 font-medium">Ticket</th>
                  <th scope="col" className="bg-marca-800 px-3 py-2 font-medium">Motivo</th>
                </tr>
              </thead>
              <tbody>
                {muestras.map((muestra) => (
                  <tr key={muestra.line} className="border-t border-marca-800 align-top">
                    <td className="px-3 py-2 tabular-nums text-white">{muestra.line}</td>
                    <td className="px-3 py-2 font-mono text-slate-300">
                      {muestra.ticket_id || (
                        <span className="font-sans text-slate-500">Sin identificador válido</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-slate-300">
                      {muestra.rules.map((regla) => INCIDENT_RULE_LABELS[regla]).join(" · ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {analysis.invalid_records > muestras.length && (
            <p className="mt-2 text-xs text-slate-400">
              Se muestran las primeras {muestras.length} de{" "}
              {formatearNumero(analysis.invalid_records)}.
            </p>
          )}
        </details>
      )}
    </section>
  );
}

// --- Desgloses por categoria y por estado ---

interface BreakdownRow {
  key: string;
  label: string;
  count: number;
  percentage: number;
}

function Breakdown({
  id,
  title,
  header,
  rows,
}: {
  id: string;
  title: string;
  header: string;
  rows: BreakdownRow[];
}) {
  return (
    <section
      aria-labelledby={id}
      className="rounded-lg border border-marca-800 bg-marca-900 p-5"
    >
      <h3 id={id} className="text-sm font-semibold text-white">
        {title}
      </h3>

      <table className="mt-4 w-full border-collapse text-sm">
        <thead className="text-left text-xs text-slate-400">
          <tr>
            <th scope="col" className="pb-2 font-medium">{header}</th>
            <th scope="col" className="pb-2 text-right font-medium">Tickets</th>
            <th scope="col" className="pb-2 text-right font-medium">% válidos</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((fila) => (
            <tr key={fila.key} className="border-t border-marca-800">
              <td className="py-2 pr-3">
                <span className="text-slate-200">{fila.label}</span>
                {/* La barra repite el porcentaje de la columna de al lado:
                    para el lector de pantalla basta con el numero. */}
                <span
                  aria-hidden="true"
                  className="mt-1.5 block h-1.5 overflow-hidden rounded-full bg-marca-950"
                >
                  <span
                    className="block h-full rounded-full bg-acento-500"
                    style={{ width: `${fila.percentage}%` }}
                  />
                </span>
              </td>
              <td className="py-2 text-right tabular-nums text-white">
                {formatearNumero(fila.count)}
              </td>
              <td className="py-2 pl-3 text-right tabular-nums text-slate-300">
                {formatearPorcentaje(fila.percentage)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

// --- Indice de satisfaccion ---

function SatisfactionIndex({ analysis }: { analysis: IncidentAnalysis }) {
  const { average_score, scored_records, distribution } = analysis.satisfaction;
  const maximo = Math.max(1, ...distribution.map((fila) => fila.count));

  return (
    <section
      aria-labelledby="satisfaccion"
      className="rounded-lg border border-marca-800 bg-marca-900 p-5"
    >
      <h3 id="satisfaccion" className="text-sm font-semibold text-white">
        Índice de satisfacción
      </h3>
      <p className="mt-1 text-xs text-slate-400">
        Solo los tickets cerrados: son los únicos que tienen puntuación.
      </p>

      <div className="mt-4 grid gap-6 md:grid-cols-[12rem_1fr]">
        <div>
          {average_score === null ? (
            <p className="text-sm text-slate-400">
              Ningún ticket cerrado tiene puntuación.
            </p>
          ) : (
            <>
              <p className="text-4xl font-semibold tabular-nums text-white">
                {formatearNumero(average_score, 2)}
                <span className="text-lg font-normal text-slate-400"> / 5</span>
              </p>
              <p className="mt-1 text-sm text-slate-400">
                Media de {formatearNumero(scored_records)}{" "}
                {scored_records === 1 ? "ticket cerrado" : "tickets cerrados"}
              </p>
            </>
          )}
        </div>

        <ul className="space-y-2">
          {distribution.map((fila) => (
            <li key={fila.score} className="flex items-center gap-3 text-sm">
              <span className="w-40 shrink-0 text-slate-300">
                {fila.score} · {SATISFACTION_SCORE_LABELS[fila.score]}
              </span>
              <span
                aria-hidden="true"
                className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-marca-950"
              >
                <span
                  className="block h-full rounded-full bg-acento-500"
                  style={{ width: `${(fila.count / maximo) * 100}%` }}
                />
              </span>
              <span className="w-10 shrink-0 text-right tabular-nums text-white">
                {formatearNumero(fila.count)}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
