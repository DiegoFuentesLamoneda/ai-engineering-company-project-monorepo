/**
 * Un campo de texto con su etiqueta, una ayuda opcional y el error debajo.
 * Lo comparten el login, el registro y el perfil.
 *
 * Accesibilidad: la etiqueta va unida al input por htmlFor; el error y la
 * ayuda, por aria-describedby, así un lector de pantalla los lee al entrar
 * en el campo. aria-invalid marca el campo con error.
 */

export const INPUT_CLASS =
  "w-full rounded-md border border-marca-700 bg-marca-950 px-3 py-2 text-sm text-slate-100 " +
  "placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400 aria-[invalid=true]:border-red-400";

interface FormFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (valor: string) => void;
  type?: "text" | "email" | "password" | "tel";
  /** Lo que el navegador puede rellenar solo: "email", "current-password"… */
  autoComplete?: string;
  required?: boolean;
  placeholder?: string;
  hint?: string;
  error?: string;
}

export default function FormField({
  id,
  label,
  value,
  onChange,
  type = "text",
  autoComplete,
  required = false,
  placeholder,
  hint,
  error,
}: FormFieldProps) {
  // El error sustituye a la ayuda: dos textos debajo del campo se leen mal.
  const descripcion = error ? `${id}-error` : hint ? `${id}-hint` : undefined;

  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
        {label}
        {required ? (
          <span className="ml-1 text-acento-400" aria-hidden="true">
            *
          </span>
        ) : (
          <span className="ml-1 normal-case tracking-normal text-slate-500">(opcional)</span>
        )}
      </label>
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        autoComplete={autoComplete}
        placeholder={placeholder}
        required={required}
        aria-invalid={Boolean(error)}
        aria-describedby={descripcion}
        onChange={(evento) => onChange(evento.target.value)}
        className={INPUT_CLASS}
      />
      {error ? (
        <p id={`${id}-error`} className="mt-1 text-xs text-red-300">
          {error}
        </p>
      ) : (
        hint && (
          <p id={`${id}-hint`} className="mt-1 text-xs text-slate-500">
            {hint}
          </p>
        )
      )}
    </div>
  );
}

/** Mensaje general del formulario (lo que no es de un campo concreto). */
export function FormAlert({ texto }: { texto: string | null }) {
  // El contenedor está siempre para que aria-live anuncie el mensaje al
  // aparecer. Si se monta a la vez que el texto, algunos lectores no lo leen.
  return (
    <div aria-live="polite">
      {texto && (
        <p className="rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100">
          {texto}
        </p>
      )}
    </div>
  );
}

export const SUBMIT_CLASS =
  "w-full rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors " +
  "hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-acento-400 disabled:cursor-not-allowed disabled:opacity-40";
