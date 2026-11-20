import type { Metadata } from "next";
import Link from "next/link";
import IncidentForm from "@/components/IncidentForm";

export const metadata: Metadata = {
  title: "Nueva incidencia · Backoffice · Nexova Solutions",
};

export default function NewIncidentPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <Link
        href="/incidents"
        className="text-sm text-acento-400 underline underline-offset-4 hover:text-acento-300"
      >
        ← Volver a incidencias
      </Link>

      <header className="mt-4 mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Nueva incidencia</h1>
        <p className="mt-1 text-sm text-slate-400">
          Registro de una incidencia en el gestor centralizado: nace abierta
        </p>
      </header>

      <IncidentForm />
    </div>
  );
}
