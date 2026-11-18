"use client";

import { useState } from "react";
import Link from "next/link";
import FormField, { FormAlert, SUBMIT_CLASS } from "@/components/FormField";
import { API_FIELD_MESSAGES, checkEmail } from "@/lib/account";
import { ApiError, forgotPassword } from "@/lib/api";
import { LOGIN_PATH } from "@/lib/auth-routes";

/**
 * El texto del ticket AUTH-03, literal. Es el mismo tenga cuenta el email o
 * no: si cambiase, la pantalla diría a cualquiera qué emails están
 * registrados en el backoffice.
 */
const MENSAJE_ENVIADO = "Si esa dirección está registrada, recibirás un enlace en breve.";

/**
 * Pedir el enlace: POST /auth/forgot-password.
 *
 * Tras un 200 el formulario se queda desactivado con el mensaje fijo. Así
 * no se pide un segundo enlace por impaciencia (el segundo anularía el
 * primero) y no se gasta el límite de 3 por hora de la API.
 *
 * Lo que sí se muestra como error es lo que no depende de la cuenta: sin
 * conexión o con la API caída, decir "recibirás un enlace" sería mentir.
 */
export default function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [errorEmail, setErrorEmail] = useState<string | undefined>();
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando || enviado) return;

    const error = checkEmail(email);
    if (error) {
      setErrorEmail(error);
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);

    try {
      await forgotPassword(email.trim());
      setEnviado(true);
    } catch (e) {
      // 422: la API no ve un email en lo escrito (la validación local es más laxa).
      if (e instanceof ApiError && "email" in e.fieldErrors) {
        setErrorEmail(API_FIELD_MESSAGES.email);
      } else {
        setErrorGeneral(
          e instanceof ApiError ? e.message : "No se ha podido enviar. Inténtalo de nuevo.",
        );
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} noValidate className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight text-white">
          Restablecer la contraseña
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Escribe el email de tu cuenta y te enviaremos un enlace para elegir una contraseña
          nueva.
        </p>
      </header>

      {/* Un fieldset desactivado desactiva de una vez el campo y el botón. */}
      <fieldset disabled={enviado} className="space-y-5">
        <FormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(valor) => {
            setEmail(valor);
            setErrorEmail(undefined);
          }}
          error={errorEmail}
        />

        <FormAlert texto={errorGeneral} />

        <button type="submit" disabled={enviando} className={SUBMIT_CLASS}>
          {enviado ? "Enlace solicitado" : enviando ? "Enviando…" : "Enviar el enlace"}
        </button>
      </fieldset>

      {/* Siempre montado, como FormAlert, para que aria-live lea el mensaje al aparecer. */}
      <div aria-live="polite">
        {enviado && (
          <p className="rounded-md border border-emerald-800 bg-emerald-950 px-3 py-2 text-sm text-emerald-100">
            {MENSAJE_ENVIADO} Si no lo ves en unos minutos, mira en la carpeta de spam.
          </p>
        )}
      </div>

      <p className="text-center text-sm text-slate-400">
        <Link
          href={LOGIN_PATH}
          className="text-acento-400 underline underline-offset-4 hover:text-acento-300"
        >
          Volver a iniciar sesión
        </Link>
      </p>
    </form>
  );
}
