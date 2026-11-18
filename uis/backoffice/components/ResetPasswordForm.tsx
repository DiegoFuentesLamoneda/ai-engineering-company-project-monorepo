"use client";

import { useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import FormField, { FormAlert, SUBMIT_CLASS } from "@/components/FormField";
import { API_FIELD_MESSAGES, MIN_PASSWORD_LENGTH, checkNewPassword } from "@/lib/account";
import { ApiError, resetPassword } from "@/lib/api";
import { FORGOT_PASSWORD_PATH, LOGIN_PATH } from "@/lib/auth-routes";

/** La URL no cambia mientras se está en la página: no hay nada que escuchar. */
const sinSuscripcion = () => () => {};

/** El token del enlace del email, o null si la URL no lo trae. */
function leerToken(): string | null {
  return new URLSearchParams(window.location.search).get("token") || null;
}

/** En el servidor no hay URL: undefined es "todavía no se sabe". */
const tokenEnServidor = () => undefined;

const LINK_CLASS = "text-acento-400 underline underline-offset-4 hover:text-acento-300";

type Campo = "password" | "passwordConfirm";

/**
 * Elegir la contraseña nueva con el enlace del email: POST /auth/reset-password.
 *
 * - Sale bien: a /login con el aviso "Contraseña actualizada". Con replace y
 *   no push, para que "atrás" no devuelva a una URL con un token ya gastado.
 * - El enlace no vale (400: inventado, caducado o ya usado): el mensaje de
 *   la API y un enlace a /forgot-password para pedir otro. El formulario se
 *   desactiva, porque con ese token ningún intento más va a funcionar.
 *
 * La confirmación solo existe aquí: una contraseña mal escrita dos veces
 * igual es poco probable, y una mal escrita una vez no se podría recuperar.
 */
export default function ResetPasswordForm() {
  const router = useRouter();
  const token = useSyncExternalStore(sinSuscripcion, leerToken, tokenEnServidor);

  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [errores, setErrores] = useState<Partial<Record<Campo, string>>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [enlaceNoValido, setEnlaceNoValido] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function limpiarError(campo: Campo) {
    setErrores((anteriores) => {
      const copia = { ...anteriores };
      delete copia[campo];
      return copia;
    });
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando || !token) return;

    const erroresLocales: Partial<Record<Campo, string>> = {};
    const errorPassword = checkNewPassword(password);
    if (errorPassword) erroresLocales.password = errorPassword;
    if (passwordConfirm !== password) {
      erroresLocales.passwordConfirm = "Las contraseñas no coinciden.";
    }
    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);

    try {
      await resetPassword(token, password);
      // Se queda "enviando" a propósito: el botón sigue desactivado hasta que
      // la navegación termina.
      router.replace(`${LOGIN_PATH}?reason=password-reset`);
    } catch (e) {
      setEnviando(false);
      if (!(e instanceof ApiError)) {
        setErrorGeneral("No se ha podido cambiar la contraseña. Inténtalo de nuevo.");
      } else if (e.status === 400) {
        setEnlaceNoValido(e.message);
      } else if ("new_password" in e.fieldErrors) {
        // 422: Pydantic responde en inglés; se muestra la regla en español.
        setErrores({ password: API_FIELD_MESSAGES.password });
      } else {
        setErrorGeneral(e.message);
      }
    }
  }

  // Sin ?token= no hay nada que enviar: se dice por qué y cómo seguir.
  if (token === null) {
    return (
      <div className="space-y-5">
        <h1 className="text-xl font-semibold tracking-tight text-white">
          Restablecer la contraseña
        </h1>
        <EnlaceNoValido texto="Este enlace no está completo. Ábrelo desde el email o pide uno nuevo." />
      </div>
    );
  }

  return (
    <form onSubmit={enviar} noValidate className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight text-white">
          Elige una contraseña nueva
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Al guardarla se cierran las sesiones abiertas con la anterior.
        </p>
      </header>

      <fieldset disabled={enlaceNoValido !== null} className="space-y-5">
        <FormField
          id="password"
          label="Contraseña nueva"
          type="password"
          autoComplete="new-password"
          required
          hint={`Al menos ${MIN_PASSWORD_LENGTH} caracteres.`}
          value={password}
          onChange={(valor) => {
            setPassword(valor);
            limpiarError("password");
          }}
          error={errores.password}
        />

        <FormField
          id="passwordConfirm"
          label="Repite la contraseña nueva"
          type="password"
          autoComplete="new-password"
          required
          value={passwordConfirm}
          onChange={(valor) => {
            setPasswordConfirm(valor);
            limpiarError("passwordConfirm");
          }}
          error={errores.passwordConfirm}
        />

        <FormAlert texto={errorGeneral} />

        <button type="submit" disabled={enviando} className={SUBMIT_CLASS}>
          {enviando ? "Guardando…" : "Guardar la contraseña"}
        </button>
      </fieldset>

      {/* Siempre montado, para que aria-live lea el aviso al aparecer. */}
      <div aria-live="polite">{enlaceNoValido && <EnlaceNoValido texto={enlaceNoValido} />}</div>

      <p className="text-center text-sm text-slate-400">
        <Link href={LOGIN_PATH} className={LINK_CLASS}>
          Volver a iniciar sesión
        </Link>
      </p>
    </form>
  );
}

/** El error de un enlace que no sirve, con la salida: pedir otro. */
function EnlaceNoValido({ texto }: { texto: string }) {
  return (
    <div className="rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100">
      <p>{texto}</p>
      <p className="mt-2">
        <Link href={FORGOT_PASSWORD_PATH} className={LINK_CLASS}>
          Pedir un enlace nuevo
        </Link>
      </p>
    </div>
  );
}
