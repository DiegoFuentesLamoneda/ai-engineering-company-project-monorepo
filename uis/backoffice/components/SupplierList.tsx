"use client";

import SupplierRateEditor from "@/components/SupplierRateEditor";
import SupplierStatusToggle from "@/components/SupplierStatusToggle";
import { useSupplierFilters } from "@/hooks/useSupplierFilters";
import { useSuppliers } from "@/hooks/useSuppliers";
import { formatearFechaCorta } from "@/lib/format";
import { CATEGORY_LABELS, COUNTRY_LABELS } from "@/lib/labels";
import { DIAS_AVISO_RENOVACION, diasHastaRenovacion, renuevaPronto } from "@/lib/suppliers";

function textoRenovacion(dias: number): string {
  if (dias === 0) return "Renueva hoy";
  if (dias === 1) return "Renueva mañana";
  return `Renueva en ${dias} días`;
}

export default function SupplierList() {
  const filtros = useSupplierFilters();
  const { suppliers, isLoading, error, reemplazar } = useSuppliers(filtros);

  if (isLoading) {
    return <p className="py-12 text-center text-sm text-slate-400">Cargando proveedores…</p>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se han podido cargar los proveedores</p>
        <p className="mt-1">{error}</p>
        <p className="mt-2 text-red-200">
          ¿Está arrancada la API? Ver <code>services/api/README.md</code>.
        </p>
      </div>
    );
  }

  if (suppliers.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-slate-400">
        No hay proveedores que coincidan con los filtros.
      </p>
    );
  }

  // Una sola fecha para toda la tabla: todas las filas cuentan desde el mismo hoy.
  const hoy = new Date();
  const activos = suppliers.filter((s) => s.status === "active").length;
  const suspendidos = suppliers.length - activos;
  const porRenovar = suppliers.filter((s) => renuevaPronto(s.contract_renewal_date, hoy)).length;

  return (
    <>
      <p className="mb-3 text-sm text-slate-400">
        {suppliers.length} {suppliers.length === 1 ? "proveedor" : "proveedores"} · {activos}{" "}
        {activos === 1 ? "activo" : "activos"} · {suspendidos}{" "}
        {suspendidos === 1 ? "suspendido" : "suspendidos"}
        {porRenovar > 0 && (
          <span className="text-acento-400">
            {" "}
            · {porRenovar} {porRenovar === 1 ? "renueva" : "renuevan"} en los próximos{" "}
            {DIAS_AVISO_RENOVACION} días
          </span>
        )}
      </p>

      {/* Como en candidaturas: en escritorio solo hace scroll la tabla. */}
      <div className="overflow-x-auto rounded-lg border border-marca-800 bg-marca-900 shadow-sm md:max-h-[calc(100vh-22rem)] md:overflow-y-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="text-left text-slate-200">
            <tr>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Proveedor</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">País</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Categorías</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Tarifa mensual</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Renovación</th>
              <th className="sticky top-0 z-10 bg-marca-800 px-4 py-3 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((supplier) => {
              const suspendido = supplier.status === "suspended";
              const dias = supplier.contract_renewal_date
                ? diasHastaRenovacion(supplier.contract_renewal_date, hoy)
                : null;
              const pronto = renuevaPronto(supplier.contract_renewal_date, hoy);

              return (
                <tr
                  key={supplier.id}
                  className={`border-t border-marca-800 align-top ${
                    suspendido ? "bg-marca-950 text-slate-400" : "text-slate-200 hover:bg-marca-800"
                  }`}
                >
                  <td className="px-4 py-3">
                    <span className={`font-medium ${suspendido ? "text-slate-400" : "text-white"}`}>
                      {supplier.name}
                    </span>
                    {supplier.contact_email && (
                      <span className="block text-xs text-slate-500">{supplier.contact_email}</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">{COUNTRY_LABELS[supplier.country]}</td>
                  <td className="px-4 py-3">
                    <ul className="flex max-w-xs flex-wrap gap-1">
                      {supplier.categories.map((categoria) => (
                        <li
                          key={categoria}
                          className="rounded border border-marca-700 px-1.5 py-0.5 text-xs"
                        >
                          {CATEGORY_LABELS[categoria]}
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td className="px-4 py-3">
                    <SupplierRateEditor supplier={supplier} onActualizado={reemplazar} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {supplier.contract_renewal_date ? (
                      <>
                        <span className={pronto ? "font-medium text-acento-400" : undefined}>
                          {formatearFechaCorta(supplier.contract_renewal_date)}
                        </span>
                        {pronto && dias !== null && (
                          <span className="mt-1 block w-fit rounded-full bg-acento-500 px-2 py-0.5 text-xs font-semibold text-marca-950">
                            {textoRenovacion(dias)}
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <SupplierStatusToggle supplier={supplier} onActualizado={reemplazar} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
