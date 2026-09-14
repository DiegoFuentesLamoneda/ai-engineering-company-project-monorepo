import Link from "next/link";
import CandidateForm from "@/components/CandidateForm";

export default function NewCandidatePage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link
        href="/candidates"
        className="text-sm text-acento-400 underline underline-offset-4 hover:text-acento-300"
      >
        ← Volver al listado
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Nueva candidatura
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Registro manual de candidaturas recibidas por otras vías
        </p>
      </header>

      <CandidateForm modo="crear" />
    </div>
  );
}
