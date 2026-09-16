"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ApiError, createCandidate, updateCandidate } from "@/lib/api";
import type { Candidate, CandidateInput } from "@/types/candidate";

/** Los valores del formulario son cadenas: es lo que devuelven los inputs. */
export interface ValoresFormulario {
  full_name: string;
  email: string;
  phone: string;
  position: string;
  experience_years: string;
  linkedin_url: string;
  cv_url: string;
}

const VALORES_VACIOS: ValoresFormulario = {
  full_name: "",
  email: "",
  phone: "",
  // Puesto de la campana activa de Nexova.
  position: "Asistente de Dirección",
  experience_years: "",
  linkedin_url: "",
  cv_url: "",
};

/** Convierte una candidatura existente en valores de formulario. */
export function valoresDesdeCandidato(candidato: Candidate): ValoresFormulario {
  return {
    full_name: candidato.full_name,
    email: candidato.email,
    phone: candidato.phone,
    position: candidato.position,
    experience_years: String(candidato.experience_years),
    linkedin_url: candidato.linkedin_url ?? "",
    cv_url: candidato.cv_url ?? "",
  };
}

const CLASE_INPUT =
  "w-full rounded-md border border-marca-700 bg-marca-950 px-3 py-2 text-sm text-slate-100 " +
  "placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400";

/**
 * Validacion en el navegador. La API comprueba el tipo, pero no el sentido:
 * acepta 7000 anos de experiencia sin rechistar.
 */
function validar(valores: ValoresFormulario): Record<string, string> {
  const errores: Record<string, string> = {};

  if (!valores.full_name.trim()) {
    errores.full_name = "El nombre completo es obligatorio.";
  }

  if (!valores.email.trim()) {
    errores.email = "El email es obligatorio.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valores.email.trim())) {
    errores.email = "El formato del email no es válido.";
  }

  if (!valores.phone.trim()) {
    errores.phone = "El teléfono es obligatorio.";
  }

  if (!valores.position.trim()) {
    errores.position = "El puesto es obligatorio.";
  }

  const anos = Number(valores.experience_years);
  if (valores.experience_years.trim() === "") {
    errores.experience_years = "Los años de experiencia son obligatorios.";
  } else if (Number.isNaN(anos) || anos < 0) {
    errores.experience_years = "Introduce un número igual o mayor que cero.";
  } else if (anos > 60) {
    errores.experience_years = "Revisa el dato: más de 60 años de experiencia.";
  }

  return errores;
}

interface CampoProps {
  id: keyof ValoresFormulario;
  etiqueta: string;
  valor: string;
  error?: string;
  tipo?: string;
  requerido?: boolean;
  placeholder?: string;
  onChange: (valor: string) => void;
}

function Campo({
  id,
  etiqueta,
  valor,
  error,
  tipo = "text",
  requerido = false,
  placeholder,
  onChange,
}: CampoProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
        {etiqueta}
        {requerido && <span className="ml-1 text-acento-400">*</span>}
      </label>

      <input
        id={id}
        name={id}
        type={tipo}
        value={valor}
        placeholder={placeholder}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(evento) => onChange(evento.target.value)}
        className={CLASE_INPUT}
      />

      {error && (
        <p id={`${id}-error`} className="mt-1 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}

interface Props {
  modo: "crear" | "editar";
  /** Obligatorio en modo editar. */
  candidateId?: string;
  valoresIniciales?: ValoresFormulario;
}

export default function CandidateForm({ modo, candidateId, valoresIniciales }: Props) {
  const router = useRouter();

  const [valores, setValores] = useState<ValoresFormulario>(
    valoresIniciales ?? VALORES_VACIOS,
  );
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function cambiar(campo: keyof ValoresFormulario, valor: string) {
    setValores((anteriores) => ({ ...anteriores, [campo]: valor }));
    // Al corregir un campo, su error desaparece.
    setErrores((anteriores) => {
      const copia = { ...anteriores };
      delete copia[campo];
      return copia;
    });
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando) return;

    const erroresLocales = validar(valores);
    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      setErrorGeneral("Revisa los campos marcados.");
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);
    setErrores({});

    const input: CandidateInput = {
      full_name: valores.full_name.trim(),
      email: valores.email.trim(),
      phone: valores.phone.trim(),
      position: valores.position.trim(),
      experience_years: Number(valores.experience_years),
      // Los campos opcionales viajan como null, no como cadena vacia.
      linkedin_url: valores.linkedin_url.trim() || null,
      cv_url: valores.cv_url.trim() || null,
    };

    try {
      const candidato =
        modo === "crear"
          ? await createCandidate(input)
          : await updateCandidate(candidateId as string, input);

      // refresh() invalida la cache del listado para que muestre el cambio.
      router.push(`/candidates/${candidato.id}`);
      router.refresh();
    } catch (e) {
      if (e instanceof ApiError) {
        // El 422 trae el error de cada campo: lo pintamos bajo su input.
        setErrores(e.fieldErrors);
        setErrorGeneral(e.message);
      } else {
        setErrorGeneral("No se ha podido guardar. Inténtalo de nuevo.");
      }
    } finally {
      setEnviando(false);
    }
  }

  const volverHref = modo === "editar" && candidateId ? `/candidates/${candidateId}` : "/";

  return (
    <form onSubmit={enviar} noValidate>
      <div className="grid gap-5 rounded-lg border border-marca-800 bg-marca-900 p-5 sm:grid-cols-2">
        <Campo
          id="full_name"
          etiqueta="Nombre completo"
          valor={valores.full_name}
          error={errores.full_name}
          requerido
          placeholder="María Fernández López"
          onChange={(valor) => cambiar("full_name", valor)}
        />

        <Campo
          id="email"
          etiqueta="Email"
          tipo="email"
          valor={valores.email}
          error={errores.email}
          requerido
          placeholder="maria.fernandez@email.com"
          onChange={(valor) => cambiar("email", valor)}
        />

        <Campo
          id="phone"
          etiqueta="Teléfono"
          valor={valores.phone}
          error={errores.phone}
          requerido
          placeholder="+34 600 000 000"
          onChange={(valor) => cambiar("phone", valor)}
        />

        <Campo
          id="position"
          etiqueta="Puesto"
          valor={valores.position}
          error={errores.position}
          requerido
          onChange={(valor) => cambiar("position", valor)}
        />

        <Campo
          id="experience_years"
          etiqueta="Años de experiencia"
          tipo="number"
          valor={valores.experience_years}
          error={errores.experience_years}
          requerido
          placeholder="5"
          onChange={(valor) => cambiar("experience_years", valor)}
        />

        <Campo
          id="linkedin_url"
          etiqueta="LinkedIn (opcional)"
          tipo="url"
          valor={valores.linkedin_url}
          error={errores.linkedin_url}
          placeholder="https://linkedin.com/in/…"
          onChange={(valor) => cambiar("linkedin_url", valor)}
        />

        <Campo
          id="cv_url"
          etiqueta="Enlace al CV (opcional)"
          tipo="url"
          valor={valores.cv_url}
          error={errores.cv_url}
          placeholder="https://…"
          onChange={(valor) => cambiar("cv_url", valor)}
        />
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
          {enviando
            ? "Guardando…"
            : modo === "crear"
              ? "Registrar candidatura"
              : "Guardar cambios"}
        </button>

        <Link
          href={volverHref}
          className="rounded-md px-3 py-2 text-sm text-slate-300 underline underline-offset-4 hover:text-slate-100"
        >
          Cancelar
        </Link>
      </div>

      {modo === "crear" && (
        <p className="mt-3 text-xs text-slate-500">
          La candidatura se registrará como <strong>Recibida</strong> y en la etapa{" "}
          <strong>Pendiente de revisión</strong>.
        </p>
      )}
    </form>
  );
}
