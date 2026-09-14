"use client";

import Link from "next/link";
import CandidateForm, { valoresDesdeCandidato } from "@/components/CandidateForm";
import { useCandidate } from "@/hooks/useCandidate";

/**
 * El PUT exige el objeto completo, asi que hay que cargar la candidatura
 * antes de pintar el formulario: si enviaramos solo los campos tocados,
 * la API lo rechazaria.
 */
export default function EditCandidateForm({ id }: { id: string }) {
  const { candidate, isLoading, error } = useCandidate(id);

  if (isLoading) {
    return <p className="py-12 text-center text-sm text-slate-400">Cargando candidatura…</p>;
  }

  if (error || !candidate) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se ha podido cargar la candidatura</p>
        <p className="mt-1">{error ?? "No existe."}</p>
        <Link href="/" className="mt-3 inline-block text-acento-400 underline underline-offset-4">
          Volver al listado
        </Link>
      </div>
    );
  }

  return (
    <CandidateForm
      modo="editar"
      candidateId={candidate.id}
      valoresIniciales={valoresDesdeCandidato(candidate)}
    />
  );
}
