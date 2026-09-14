"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ApiError, patchCandidate } from "@/lib/api";
import { formatearFecha } from "@/lib/format";
import { STAGE_LABELS, STAGE_VALUES, STATUS_LABELS, STATUS_VALUES } from "@/lib/labels";
import { useCandidate } from "@/hooks/useCandidate";
import CandidateNotes from "@/components/CandidateNotes";
import type { Stage, Status } from "@/types/candidate";

const CLASE_SELECT =
  "rounded-md border border-marca-700 bg-marca-900 px-3 py-2 text-sm text-slate-100 " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 " +
  "disabled:opacity-50";

/** Una fila de dato del panel de informacion. */
function Dato({ etiqueta, children }: { etiqueta: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">{etiqueta}</dt>
      <dd className="mt-1 text-sm text-slate-100">{children}</dd>
    </div>
  );
}

export default function CandidateDetail({ id }: { id: string }) {
  const { candidate, setCandidate, isLoading, error } = useCandidate(id);
  const searchParams = useSearchParams();

  const [guardando, setGuardando] = useState(false);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);
  const [guardado, setGuardado] = useState(false);

  // El aviso de "guardado" desaparece solo a los 2 segundos.
  useEffect(() => {
    if (!guardado) return;
    const temporizador = setTimeout(() => setGuardado(false), 2000);
    return () => clearTimeout(temporizador);
  }, [guardado]);

  // Volvemos al listado conservando los filtros que traiamos.
  const consulta = searchParams.toString();
  const volverHref = consulta ? `/?${consulta}` : "/";

  async function actualizar(cambios: { status?: Status; stage?: Stage }) {
    if (!candidate) return;

    setGuardando(true);
    setErrorAccion(null);

    try {
      // El PATCH devuelve el candidato completo: lo usamos para refrescar
      // la vista sin lanzar una segunda peticion.
      const actualizado = await patchCandidate(candidate.id, cambios);
      setCandidate(actualizado);
      setGuardado(true);
    } catch (e) {
      setErrorAccion(e instanceof ApiError ? e.message : "No se ha podido guardar.");
    } finally {
      setGuardando(false);
    }
  }

  if (isLoading) {
    return <p className="py-12 text-center text-sm text-slate-400">Cargando candidatura…</p>;
  }

  if (error || !candidate) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se ha podido cargar la candidatura</p>
        <p className="mt-1">{error ?? "No existe."}</p>
        <Link
          href={volverHref}
          className="mt-3 inline-block text-acento-400 underline underline-offset-4"
        >
          Volver al listado
        </Link>
      </div>
    );
  }

  return (
    <>
      <Link
        href={volverHref}
        className="text-sm text-acento-400 underline underline-offset-4 hover:text-acento-300"
      >
        ← Volver al listado
      </Link>

      <header className="mt-4 mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            {candidate.full_name}
          </h1>
          <p className="mt-1 text-sm text-slate-400">{candidate.position}</p>
        </div>

        <Link
          href={`/candidates/${candidate.id}/edit`}
          className="rounded-md border border-marca-700 px-4 py-2 text-sm font-medium text-slate-100 transition-colors hover:bg-marca-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Editar datos
        </Link>
      </header>

      <section className="mb-6 rounded-lg border border-marca-800 bg-marca-900 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-200">Seguimiento</h2>

        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-400">Estado</span>
            <select
              value={candidate.status}
              disabled={guardando}
              onChange={(evento) => actualizar({ status: evento.target.value as Status })}
              className={CLASE_SELECT}
            >
              {STATUS_VALUES.map((valor) => (
                <option key={valor} value={valor}>
                  {STATUS_LABELS[valor]}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="text-xs uppercase tracking-wide text-slate-400">Etapa</span>
            <select
              value={candidate.stage}
              disabled={guardando}
              onChange={(evento) => actualizar({ stage: evento.target.value as Stage })}
              className={CLASE_SELECT}
            >
              {STAGE_VALUES.map((valor) => (
                <option key={valor} value={valor}>
                  {STAGE_LABELS[valor]}
                </option>
              ))}
            </select>
          </label>

          <p aria-live="polite" className="pb-2 text-sm">
            {guardando && <span className="text-slate-400">Guardando…</span>}
            {!guardando && guardado && (
              <span className="text-emerald-400">Cambios guardados</span>
            )}
          </p>
        </div>

        {errorAccion && (
          <p className="mt-3 rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100">
            {errorAccion}
          </p>
        )}
      </section>

      <section className="rounded-lg border border-marca-800 bg-marca-900 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-200">Datos de la candidatura</h2>

        <dl className="grid gap-5 sm:grid-cols-2">
          <Dato etiqueta="Email">
            <a
              href={`mailto:${candidate.email}`}
              className="text-acento-400 underline underline-offset-4"
            >
              {candidate.email}
            </a>
          </Dato>

          <Dato etiqueta="Teléfono">{candidate.phone}</Dato>
          <Dato etiqueta="Puesto">{candidate.position}</Dato>
          <Dato etiqueta="Años de experiencia">{candidate.experience_years}</Dato>

          <Dato etiqueta="LinkedIn">
            {candidate.linkedin_url ? (
              <a
                href={candidate.linkedin_url}
                target="_blank"
                rel="noreferrer"
                className="text-acento-400 underline underline-offset-4"
              >
                Ver perfil
              </a>
            ) : (
              <span className="text-slate-500">No indicado</span>
            )}
          </Dato>

          <Dato etiqueta="Currículum">
            {candidate.cv_url ? (
              <a
                href={candidate.cv_url}
                target="_blank"
                rel="noreferrer"
                className="text-acento-400 underline underline-offset-4"
              >
                Descargar CV
              </a>
            ) : (
              <span className="text-slate-500">No indicado</span>
            )}
          </Dato>

          <Dato etiqueta="Fecha de candidatura">{formatearFecha(candidate.applied_at)}</Dato>
          <Dato etiqueta="Última actualización">{formatearFecha(candidate.updated_at)}</Dato>
        </dl>
      </section>

      <CandidateNotes recordId={candidate.id} />
    </>
  );
}
