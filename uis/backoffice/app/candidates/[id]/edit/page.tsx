import { Suspense } from "react";
import Link from "next/link";
import EditCandidateForm from "@/components/EditCandidateForm";

export default async function EditCandidatePage({
  params,
}: PageProps<"/candidates/[id]/edit">) {
  const { id } = await params;

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link
        href={`/candidates/${id}`}
        className="text-sm text-acento-400 underline underline-offset-4 hover:text-acento-300"
      >
        ← Volver a la candidatura
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Editar candidatura
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Corrige los datos personales o profesionales del candidato
        </p>
      </header>

      <Suspense fallback={<p className="text-sm text-slate-400">Cargando…</p>}>
        <EditCandidateForm id={id} />
      </Suspense>
    </div>
  );
}
