import { Suspense } from "react";
import CandidateDetail from "@/components/CandidateDetail";

/** En Next 15+ params es una Promise: hay que esperarla. */
export default async function CandidateDetailPage({
  params,
}: PageProps<"/candidates/[id]">) {
  const { id } = await params;

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Suspense fallback={<p className="text-sm text-slate-400">Cargando…</p>}>
        <CandidateDetail id={id} />
      </Suspense>
    </div>
  );
}
