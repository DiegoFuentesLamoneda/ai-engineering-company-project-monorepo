import { Suspense } from "react";
import Link from "next/link";
import CandidateFilters from "@/components/CandidateFilters";
import CandidateList from "@/components/CandidateList";
import { ACTIVE_PROCESS } from "@/lib/company";

export default function CandidatesPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Candidaturas
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {ACTIVE_PROCESS.position} · {ACTIVE_PROCESS.office}
          </p>
        </div>

        <Link
          href="/candidates/new"
          className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Nueva candidatura
        </Link>
      </header>

      {/* useSearchParams necesita una frontera de Suspense para poder prerenderizar. */}
      <Suspense fallback={<p className="text-sm text-slate-400">Cargando…</p>}>
        <CandidateFilters />
        <CandidateList />
      </Suspense>
    </div>
  );
}
