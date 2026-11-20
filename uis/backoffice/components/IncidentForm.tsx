"use client";

import { useState } from "react";
import Link from "next/link";
import { ApiError, createIncident } from "@/lib/api";
import {
  BRANCH_LABELS,
  BRANCH_VALUES,
  MANAGER_CATEGORY_DESCRIPTIONS,
  MANAGER_CATEGORY_LABELS,
  MANAGER_CATEGORY_VALUES,
  ORIGIN_DESCRIPTIONS,
  ORIGIN_LABELS,
  ORIGIN_VALUES,
} from "@/lib/labels";
import type {
  Branch,
  FieldErrorCode,
  IncidentInput,
  IncidentManagerCategory,
  IncidentOrigin,
} from "@/types/incident-manager";

/** Los límites de la API (IncidentCreate en schemas.py). */
const MAX_TITULO = 120;
const MAX_DESCRIPCION = 2000;

/** Los desplegables empiezan vacíos: nada se elige por defecto sin mirarlo. */
interface ValoresFormulario {
  title: string;
  description: string;
  category: IncidentManagerCategory | "";
  origin: IncidentOrigin | "";
  branch: Branch | "";
}

type Campo = keyof ValoresFormulario;
type Errores = Partial<Record<Campo, string>>;

const VALORES_INICIALES: ValoresFormulario = {
  title: "",
  description: "",
  category: "",
  origin: "",
  branch: "",
};

const CLASE_INPUT =
  "w-full rounded-md border border-marca-700 bg-marca-950 px-3 py-2 text-sm text-slate-100 " +
  "placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400 aria-[invalid=true]:border-red-400";

const CLASE_ETIQUETA = "mb-1 block text-xs uppercase tracking-wide text-slate-400";

/** Cómo se llama cada campo en una frase: "Falta el título". */
const NOMBRE_CAMPO: Record<Campo, string> = {
  title: "el título",
  description: "la descripción",
  category: "la categoría",
  origin: "el origen",
  branch: "la sede",
};

/**
 * El 400 del gestor trae un código estable por campo. Con él se escribe el
 * mensaje en lenguaje llano; el texto de la API ("El campo 'title'…") está
 * pensado para quien lee la API, no para quien rellena el formulario.
 */
function mensajePorCodigo(campo: Campo, codigo: string): string {
  const nombre = NOMBRE_CAMPO[campo];
  switch (codigo as FieldErrorCode) {
    case "missing":
    case "blank":
      return `Falta ${nombre}.`;
    case "too_long":
      return campo === "title"
        ? `El título admite como máximo ${MAX_TITULO} caracteres.`
        : `La descripción admite como máximo ${MAX_DESCRIPCION} caracteres.`;
    case "invalid_choice":
      return `Elige ${nombre} de la lista.`;
    default:
      return `Revisa ${nombre}: el servidor no lo ha aceptado.`;
  }
}

/** Las mismas reglas que la API, comprobadas antes de enviar. */
function validar(valores: ValoresFormulario): Errores {
  const errores: Errores = {};
  const titulo = valores.title.trim();
  const descripcion = valores.description.trim();

  if (!titulo) errores.title = "Escribe un título que resuma la incidencia.";
  else if (titulo.length > MAX_TITULO)
    errores.title = `El título admite como máximo ${MAX_TITULO} caracteres.`;

  if (!descripcion) errores.description = "Cuenta qué ha pasado: la descripción es obligatoria.";
  else if (descripcion.length > MAX_DESCRIPCION)
    errores.description = `La descripción admite como máximo ${MAX_DESCRIPCION} caracteres.`;

  if (!valores.category) errores.category = "Elige la categoría que mejor encaje.";
  if (!valores.origin) errores.origin = "Elige quién reporta la incidencia.";
  if (!valores.branch) errores.branch = "Elige la sede a la que corresponde.";

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
  return (
    <span className="ml-1 text-acento-400" aria-hidden="true">
      *
    </span>
  );
}

/** El id de la ayuda o del error, para aria-describedby. El error manda. */
function descritoPor(campo: Campo, errores: Errores, hayAyuda: boolean): string | undefined {
  if (errores[campo]) return `${campo}-error`;
  return hayAyuda ? `${campo}-hint` : undefined;
}

export default function IncidentForm() {
  const [valores, setValores] = useState<ValoresFormulario>(VALORES_INICIALES);
  const [errores, setErrores] = useState<Errores>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [registrada, setRegistrada] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  // Si la reporta personal de una oficina, la sede es la de esa oficina: se
  // resalta para que no se quede en la primera de la lista sin pensarlo.
  const sedeResaltada = valores.origin === "branch";

  function cambiar<C extends Campo>(campo: C, valor: ValoresFormulario[C]) {
    setValores((anteriores) => ({ ...anteriores, [campo]: valor }));
    // Al corregir un campo, su error desaparece; y la confirmación anterior,
    // en cuanto se empieza la siguiente.
    setErrores((anteriores) => {
      const copia = { ...anteriores };
      delete copia[campo];
      return copia;
    });
    setRegistrada(null);
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando) return;

    setRegistrada(null);
    const erroresLocales = validar(valores);
    if (
      Object.keys(erroresLocales).length > 0 ||
      !valores.category ||
      !valores.origin ||
      !valores.branch
    ) {
      setErrores(erroresLocales);
      setErrorGeneral("Revisa los campos marcados.");
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);
    setErrores({});

    const input: IncidentInput = {
      title: valores.title.trim(),
      description: valores.description.trim(),
      category: valores.category,
      origin: valores.origin,
      branch: valores.branch,
    };

    try {
      const incidencia = await createIncident(input);
      // Formulario limpio para la siguiente y confirmación con lo registrado.
      setValores(VALORES_INICIALES);
      setRegistrada(incidencia.title);
    } catch (e) {
      if (!(e instanceof ApiError)) {
        setErrorGeneral("No se ha podido registrar la incidencia. Inténtalo de nuevo.");
        return;
      }

      // Cada campo que rechaza la API se marca bajo su input.
      const erroresApi: Errores = {};
      for (const [campo, codigo] of Object.entries(e.fieldCodes)) {
        if (campo in NOMBRE_CAMPO) {
          erroresApi[campo as Campo] = mensajePorCodigo(campo as Campo, codigo);
        }
      }
      setErrores(erroresApi);
      setErrorGeneral(
        Object.keys(erroresApi).length > 0
          ? "El servidor no ha aceptado la incidencia. Revisa los campos marcados."
          : e.message,
      );
    } finally {
      setEnviando(false);
    }
  }

  const ayudaSede = sedeResaltada
    ? "La reporta personal de una oficina: elige la oficina desde la que llega."
    : "Si no corresponde a una oficina concreta, usa Central.";

  return (
    <form onSubmit={enviar} noValidate>
      <div className="grid gap-5 rounded-lg border border-marca-800 bg-marca-900 p-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="title" className={CLASE_ETIQUETA}>
            Título
            <Obligatorio />
          </label>
          <input
            id="title"
            type="text"
            value={valores.title}
            maxLength={MAX_TITULO}
            placeholder="El ATS no envía las notificaciones a candidatos"
            aria-invalid={Boolean(errores.title)}
            aria-describedby={descritoPor("title", errores, true)}
            onChange={(evento) => cambiar("title", evento.target.value)}
            className={CLASE_INPUT}
          />
          {errores.title ? (
            <MensajeError id="title" texto={errores.title} />
          ) : (
            <p id="title-hint" className="mt-1 text-xs text-slate-500">
              {valores.title.length}/{MAX_TITULO} caracteres
            </p>
          )}
        </div>

        <div className="sm:col-span-2">
          <label htmlFor="description" className={CLASE_ETIQUETA}>
            Descripción
            <Obligatorio />
          </label>
          <textarea
            id="description"
            rows={5}
            value={valores.description}
            maxLength={MAX_DESCRIPCION}
            placeholder="Qué ha pasado, desde cuándo y a quién afecta"
            aria-invalid={Boolean(errores.description)}
            aria-describedby={descritoPor("description", errores, true)}
            onChange={(evento) => cambiar("description", evento.target.value)}
            className={CLASE_INPUT}
          />
          {errores.description ? (
            <MensajeError id="description" texto={errores.description} />
          ) : (
            <p id="description-hint" className="mt-1 text-xs text-slate-500">
              {valores.description.length}/{MAX_DESCRIPCION} caracteres
            </p>
          )}
        </div>

        <div className="sm:col-span-2">
          <label htmlFor="category" className={CLASE_ETIQUETA}>
            Categoría
            <Obligatorio />
          </label>
          <select
            id="category"
            value={valores.category}
            aria-invalid={Boolean(errores.category)}
            aria-describedby={descritoPor("category", errores, Boolean(valores.category))}
            onChange={(evento) =>
              cambiar("category", evento.target.value as IncidentManagerCategory | "")
            }
            className={CLASE_INPUT}
          >
            <option value="">Elige una categoría</option>
            {MANAGER_CATEGORY_VALUES.map((valor) => (
              <option key={valor} value={valor}>
                {MANAGER_CATEGORY_LABELS[valor]}
              </option>
            ))}
          </select>
          {errores.category ? (
            <MensajeError id="category" texto={errores.category} />
          ) : (
            valores.category && (
              <p id="category-hint" className="mt-1 text-xs text-slate-500">
                {MANAGER_CATEGORY_DESCRIPTIONS[valores.category]}
              </p>
            )
          )}
        </div>

        <div>
          <label htmlFor="origin" className={CLASE_ETIQUETA}>
            Quién la reporta
            <Obligatorio />
          </label>
          <select
            id="origin"
            value={valores.origin}
            aria-invalid={Boolean(errores.origin)}
            aria-describedby={descritoPor("origin", errores, Boolean(valores.origin))}
            onChange={(evento) => cambiar("origin", evento.target.value as IncidentOrigin | "")}
            className={CLASE_INPUT}
          >
            <option value="">Elige el origen</option>
            {ORIGIN_VALUES.map((valor) => (
              <option key={valor} value={valor}>
                {ORIGIN_LABELS[valor]}
              </option>
            ))}
          </select>
          {errores.origin ? (
            <MensajeError id="origin" texto={errores.origin} />
          ) : (
            valores.origin && (
              <p id="origin-hint" className="mt-1 text-xs text-slate-500">
                {ORIGIN_DESCRIPTIONS[valores.origin]}
              </p>
            )
          )}
        </div>

        <div
          className={
            sedeResaltada
              ? "-m-2 rounded-md border border-acento-500 bg-marca-800 p-2"
              : undefined
          }
        >
          <label htmlFor="branch" className={CLASE_ETIQUETA}>
            Sede
            <Obligatorio />
          </label>
          <select
            id="branch"
            value={valores.branch}
            aria-invalid={Boolean(errores.branch)}
            aria-describedby={descritoPor("branch", errores, true)}
            onChange={(evento) => cambiar("branch", evento.target.value as Branch | "")}
            className={CLASE_INPUT}
          >
            <option value="">Elige una sede</option>
            {BRANCH_VALUES.map((valor) => (
              <option key={valor} value={valor}>
                {BRANCH_LABELS[valor]}
              </option>
            ))}
          </select>
          {errores.branch ? (
            <MensajeError id="branch" texto={errores.branch} />
          ) : (
            <p
              id="branch-hint"
              className={`mt-1 text-xs ${sedeResaltada ? "text-acento-300" : "text-slate-500"}`}
            >
              {ayudaSede}
            </p>
          )}
        </div>
      </div>

      {/* Siempre montado: aria-live solo anuncia lo que cambia dentro. */}
      <div aria-live="polite" className="mt-4 empty:hidden">
        {errorGeneral && (
          <p className="rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100">
            {errorGeneral}
          </p>
        )}
        {registrada && (
          <p className="rounded-md border border-emerald-700 bg-emerald-950 px-3 py-2 text-sm text-emerald-100">
            Incidencia registrada: «{registrada}». Queda abierta en la lista de incidencias.
          </p>
        )}
      </div>

      <div className="mt-5 flex items-center gap-3">
        <button
          type="submit"
          disabled={enviando}
          className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {enviando ? "Registrando…" : "Registrar incidencia"}
        </button>

        <Link
          href="/incidents"
          className="rounded-md px-3 py-2 text-sm text-slate-300 underline underline-offset-4 hover:text-slate-100"
        >
          Cancelar
        </Link>
      </div>
    </form>
  );
}
