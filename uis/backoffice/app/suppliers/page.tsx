import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import SupplierFilters from "@/components/SupplierFilters";
import SupplierList from "@/components/SupplierList";

export const metadata: Metadata = {
  title: "Directorio de proveedores · Backoffice · Nexova Solutions",
};

export default function SuppliersPage() {
  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white">
            Directorio de proveedores
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Proveedores externos de las oficinas de Valencia y Miami
          </p>
        </div>

        <Link
          href="/suppliers/new"
          className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Nuevo proveedor
        </Link>
      </header>

      {/* useSearchParams necesita una frontera de Suspense para poder prerenderizar. */}
      <Suspense fallback={<p className="text-sm text-slate-400">Cargando…</p>}>
        <SupplierFilters />
        <SupplierList />
      </Suspense>
    </div>
  );
}
