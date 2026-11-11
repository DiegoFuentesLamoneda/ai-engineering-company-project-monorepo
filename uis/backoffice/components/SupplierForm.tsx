"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError, createSupplier } from "@/lib/api";
import {
  CATEGORY_LABELS,
  CATEGORY_VALUES,
  COUNTRY_LABELS,
  COUNTRY_VALUES,
  SUPPLIER_STATUS_LABELS,
  SUPPLIER_STATUS_VALUES,
} from "@/lib/labels";
import { CURRENCY_BY_COUNTRY } from "@/lib/suppliers";
import type { Category, Country, SupplierInput, SupplierStatus } from "@/types/supplier";

/** Los inputs devuelven cadenas; las categorias, una lista de marcadas. */
interface ValoresFormulario {
  name: string;
  country: Country | "";
  categories: Category[];
  monthly_rate: string;
  status: SupplierStatus;
  contract_renewal_date: string;
  contact_email: string;
  notes: string;
}

type Campo = keyof ValoresFormulario;

const VALORES_INICIALES: ValoresFormulario = {
  name: "",
  country: "",
  categories: [],
  monthly_rate: "",
  status: "active",
  contract_renewal_date: "",
  contact_email: "",
  notes: "",
};

const PATRON_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

const CLASE_INPUT =
  "w-full rounded-md border border-marca-700 bg-marca-950 px-3 py-2 text-sm text-slate-100 " +
  "placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400";

const CLASE_ETIQUETA = "mb-1 block text-xs uppercase tracking-wide text-slate-400";

/**
 * Los mensajes que genera Pydantic llegan en ingles ("Input should be
 * greater than 0"). Si la API rechaza un campo, se muestra el texto en
 * espanol de ese campo; un campo que no esta aqui va al error general.
 */
const MENSAJE_API_POR_CAMPO: Record<Campo, string> = {
  name: "La API ha rechazado el nombre: no puede estar vacío.",
  country: "La API ha rechazado el país: elige uno de la lista.",
  categories: "La API ha rechazado las categorías: elige al menos una, sin repetir.",
  monthly_rate: "La API ha rechazado la tarifa: tiene que ser mayor que cero.",
  status: "La API ha rechazado el estado: elige uno de la lista.",
  contract_renewal_date: "La API ha rechazado la fecha: usa el formato día/mes/año.",
  contact_email: "La API ha rechazado el email: el formato no es válido.",
  notes: "La API ha rechazado las notas.",
};

/** Las mismas reglas que la API, comprobadas antes de enviar. */
function validar(valores: ValoresFormulario): Partial<Record<Campo, string>> {
  const errores: Partial<Record<Campo, string>> = {};

  if (!valores.name.trim()) {
    errores.name = "El nombre es obligatorio.";
  }

  if (!valores.country) {
    errores.country = "Elige el país del proveedor.";
  }

  if (valores.categories.length === 0) {
    errores.categories = "Marca al menos una categoría.";
  }

  const tarifa = Number(valores.monthly_rate.replace(",", "."));
  if (valores.monthly_rate.trim() === "") {
    errores.monthly_rate = "La tarifa mensual es obligatoria.";
  } else if (!Number.isFinite(tarifa) || tarifa <= 0) {
    errores.monthly_rate = "Introduce un importe mayor que cero.";
  }

  const email = valores.contact_email.trim();
  if (email && !PATRON_EMAIL.test(email)) {
    errores.contact_email = "El formato del email no es válido.";
  }

  return errores;
}

function MensajeError({ id, texto }: { id: string; texto?: string }) {
  if (!texto) return null;
  return (
    <p id={`${id}-error`} className="mt-1 text-xs text-red-300">
      {texto}
    </p>
  );
}

function Obligatorio() {
  return <span className="ml-1 text-acento-400">*</span>;
}

export default function SupplierForm() {
  const router = useRouter();

  const [valores, setValores] = useState<ValoresFormulario>(VALORES_INICIALES);
  const [errores, setErrores] = useState<Partial<Record<Campo, string>>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // La moneda no se elige: la fija el pais (Espana factura en EUR, EE. UU. en USD).
  const moneda = valores.country ? CURRENCY_BY_COUNTRY[valores.country] : null;

  function cambiar<C extends Campo>(campo: C, valor: ValoresFormulario[C]) {
    setValores((anteriores) => ({ ...anteriores, [campo]: valor }));
    // Al corregir un campo, su error desaparece.
    setErrores((anteriores) => {
      const copia = { ...anteriores };
      delete copia[campo];
      return copia;
    });
  }

  function alternarCategoria(categoria: Category, marcada: boolean) {
    const siguientes = marcada
      ? [...valores.categories, categoria]
      : valores.categories.filter((c) => c !== categoria);
    // Se guardan en el orden del BRIEFING, no en el orden en que se marcan.
    cambiar(
      "categories",
      CATEGORY_VALUES.filter((c) => siguientes.includes(c)),
    );
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando) return;

    const erroresLocales = validar(valores);
    if (Object.keys(erroresLocales).length > 0 || !valores.country || !moneda) {
      setErrores(erroresLocales);
      setErrorGeneral("Revisa los campos marcados.");
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);
    setErrores({});

    const input: SupplierInput = {
      name: valores.name.trim(),
      country: valores.country,
      categories: valores.categories,
      monthly_rate: Number(valores.monthly_rate.replace(",", ".")),
      currency: moneda,
      status: valores.status,
      // Los campos opcionales viajan como null, no como cadena vacia.
      contract_renewal_date: valores.contract_renewal_date || null,
      contact_email: valores.contact_email.trim() || null,
      notes: valores.notes.trim() || null,
    };

    try {
      await createSupplier(input);
      // refresh() invalida la cache para que el directorio muestre el alta.
      router.push("/suppliers");
      router.refresh();
    } catch (e) {
      if (!(e instanceof ApiError)) {
        setErrorGeneral("No se ha podido registrar el proveedor. Inténtalo de nuevo.");
        return;
      }

      // Cada campo que rechaza la API se marca bajo su input, en espanol.
      const erroresApi: Partial<Record<Campo, string>> = {};
      for (const campo of Object.keys(e.fieldErrors)) {
        if (campo in MENSAJE_API_POR_CAMPO) {
          erroresApi[campo as Campo] = MENSAJE_API_POR_CAMPO[campo as Campo];
        }
      }
      setErrores(erroresApi);
      setErrorGeneral(
        Object.keys(erroresApi).length > 0
          ? "La API ha rechazado el alta. Revisa los campos marcados."
          : e.message,
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} noValidate>
      <div className="grid gap-5 rounded-lg border border-marca-800 bg-marca-900 p-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="name" className={CLASE_ETIQUETA}>
            Nombre
            <Obligatorio />
          </label>
          <input
            id="name"
            type="text"
            value={valores.name}
            placeholder="TalentTest Pro"
            aria-invalid={Boolean(errores.name)}
            aria-describedby={errores.name ? "name-error" : undefined}
            onChange={(evento) => cambiar("name", evento.target.value)}
            className={CLASE_INPUT}
          />
          <MensajeError id="name" texto={errores.name} />
        </div>

        <div>
          <label htmlFor="country" className={CLASE_ETIQUETA}>
            País
            <Obligatorio />
          </label>
          <select
            id="country"
            value={valores.country}
            aria-invalid={Boolean(errores.country)}
            aria-describedby={errores.country ? "country-error" : "currency-hint"}
            onChange={(evento) => cambiar("country", evento.target.value as Country | "")}
            className={CLASE_INPUT}
          >
            <option value="">Elige un país</option>
            {COUNTRY_VALUES.map((valor) => (
              <option key={valor} value={valor}>
                {COUNTRY_LABELS[valor]}
              </option>
            ))}
          </select>
          <MensajeError id="country" texto={errores.country} />
          {!errores.country && (
            <p id="currency-hint" className="mt-1 text-xs text-slate-500">
              {moneda
                ? `Factura en ${moneda}: la moneda la fija el país.`
                : "La moneda se fija con el país."}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="monthly_rate" className={CLASE_ETIQUETA}>
            Tarifa mensual{moneda ? ` (${moneda})` : ""}
            <Obligatorio />
          </label>
          <input
            id="monthly_rate"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            value={valores.monthly_rate}
            placeholder="450"
            aria-invalid={Boolean(errores.monthly_rate)}
            aria-describedby={errores.monthly_rate ? "monthly_rate-error" : undefined}
            onChange={(evento) => cambiar("monthly_rate", evento.target.value)}
            className={CLASE_INPUT}
          />
          <MensajeError id="monthly_rate" texto={errores.monthly_rate} />
        </div>

        <fieldset
          className="sm:col-span-2"
          aria-describedby={errores.categories ? "categories-error" : undefined}
        >
          <legend className={CLASE_ETIQUETA}>
            Categorías
            <Obligatorio />
          </legend>
          <div className="grid gap-2 sm:grid-cols-3">
            {CATEGORY_VALUES.map((categoria) => (
              <label
                key={categoria}
                className="flex items-center gap-2 rounded-md border border-marca-800 px-3 py-2 text-sm text-slate-200 has-[:checked]:border-acento-500 has-[:checked]:bg-marca-800"
              >
                <input
                  type="checkbox"
                  checked={valores.categories.includes(categoria)}
                  onChange={(evento) => alternarCategoria(categoria, evento.target.checked)}
                  className="accent-acento-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
                />
                {CATEGORY_LABELS[categoria]}
              </label>
            ))}
          </div>
          <MensajeError id="categories" texto={errores.categories} />
        </fieldset>

        <div>
          <label htmlFor="status" className={CLASE_ETIQUETA}>
            Estado
          </label>
          <select
            id="status"
            value={valores.status}
            onChange={(evento) => cambiar("status", evento.target.value as SupplierStatus)}
            className={CLASE_INPUT}
          >
            {SUPPLIER_STATUS_VALUES.map((valor) => (
              <option key={valor} value={valor}>
                {SUPPLIER_STATUS_LABELS[valor]}
              </option>
            ))}
          </select>
          <MensajeError id="status" texto={errores.status} />
        </div>

        <div>
          <label htmlFor="contract_renewal_date" className={CLASE_ETIQUETA}>
            Renovación del contrato (opcional)
          </label>
          <input
            id="contract_renewal_date"
            type="date"
            value={valores.contract_renewal_date}
            aria-invalid={Boolean(errores.contract_renewal_date)}
            aria-describedby={
              errores.contract_renewal_date ? "contract_renewal_date-error" : undefined
            }
            onChange={(evento) => cambiar("contract_renewal_date", evento.target.value)}
            className={`${CLASE_INPUT} [color-scheme:dark]`}
          />
          <MensajeError id="contract_renewal_date" texto={errores.contract_renewal_date} />
        </div>

        <div className="sm:col-span-2">
          <label htmlFor="contact_email" className={CLASE_ETIQUETA}>
            Email de contacto (opcional)
          </label>
          <input
            id="contact_email"
            type="email"
            value={valores.contact_email}
            placeholder="cuentas@proveedor.com"
            aria-invalid={Boolean(errores.contact_email)}
            aria-describedby={errores.contact_email ? "contact_email-error" : undefined}
            onChange={(evento) => cambiar("contact_email", evento.target.value)}
            className={CLASE_INPUT}
          />
          <MensajeError id="contact_email" texto={errores.contact_email} />
        </div>

        <div className="sm:col-span-2">
          <label htmlFor="notes" className={CLASE_ETIQUETA}>
            Notas (opcional)
          </label>
          <textarea
            id="notes"
            rows={3}
            value={valores.notes}
            placeholder="Condiciones especiales, persona de contacto…"
            onChange={(evento) => cambiar("notes", evento.target.value)}
            className={CLASE_INPUT}
          />
          <MensajeError id="notes" texto={errores.notes} />
        </div>
      </div>

      {errorGeneral && (
        <p
          aria-live="polite"
          className="mt-4 rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100"
        >
          {errorGeneral}
        </p>
      )}

      <div className="mt-5 flex items-center gap-3">
        <button
          type="submit"
          disabled={enviando}
          className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {enviando ? "Guardando…" : "Registrar proveedor"}
        </button>

        <Link
          href="/suppliers"
          className="rounded-md px-3 py-2 text-sm text-slate-300 underline underline-offset-4 hover:text-slate-100"
        >
          Cancelar
        </Link>
      </div>
    </form>
  );
}
