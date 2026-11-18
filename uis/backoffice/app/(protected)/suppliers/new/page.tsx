import type { Metadata } from "next";
import Link from "next/link";
import SupplierForm from "@/components/SupplierForm";

export const metadata: Metadata = {
  title: "Nuevo proveedor · Backoffice · Nexova Solutions",
};

export default function NewSupplierPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link
        href="/suppliers"
        className="text-sm text-acento-400 underline underline-offset-4 hover:text-acento-300"
      >
        ← Volver al directorio
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Nuevo proveedor</h1>
        <p className="mt-1 text-sm text-slate-400">
          Alta de un proveedor externo en el directorio
        </p>
      </header>

      <SupplierForm />
    </div>
  );
}
