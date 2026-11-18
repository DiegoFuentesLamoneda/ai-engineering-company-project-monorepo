"use client";

import { useState } from "react";
import FormField, { FormAlert, SUBMIT_CLASS } from "@/components/FormField";
import { API_FIELD_MESSAGES, MIN_PASSWORD_LENGTH, checkNewPassword } from "@/lib/account";
import { ApiError, changePassword } from "@/lib/api";

type Campo = "currentPassword" | "newPassword" | "newPasswordConfirm";
type Valores = Record<Campo, string>;

const VACIO: Valores = { currentPassword: "", newPassword: "", newPasswordConfirm: "" };

/** Las comprobaciones que no necesitan a la API. Si alguna falla, no se envía nada. */
function validar(valores: Valores): Partial<Record<Campo, string>> {
  const errores: Partial<Record<Campo, string>> = {};
  if (!valores.currentPassword) {
    errores.currentPassword = "Escribe tu contraseña actual.";
  }
  const errorNueva = checkNewPassword(valores.newPassword);
  if (errorNueva) {
    errores.newPassword = errorNueva;
  } else if (valores.newPassword === valores.currentPassword) {
    errores.newPassword = "La nueva contraseña tiene que ser distinta de la actual.";
  }
  if (valores.newPasswordConfirm !== valores.newPassword) {
    errores.newPasswordConfirm = "Las contraseñas no coinciden.";
  }
  return errores;
}

/**
 * Cambiar la contraseña con la sesión iniciada: POST /auth/change-password.
 *
 * - La confirmación se comprueba aquí, antes de llamar a la API (lo pide el
 *   ticket AUTH-03). Igual que la regla de longitud y que la nueva no sea la
 *   misma: la API lo vuelve a mirar, pero así no se gasta un viaje.
 * - Sale bien: lib/api.ts guarda el token nuevo y se sigue dentro. Los
 *   campos se vacían, para no dejar contraseñas escritas en la pantalla.
 * - 400: la contraseña actual no es correcta. El mensaje de la API va bajo
 *   ese campo. (La otra causa de 400, nueva igual que la actual, ya no llega:
 *   la para validar().)
 * - 401: la sesión ha caducado. lib/api.ts la cierra y AuthGuard lleva a
 *   /login, como en cualquier otra vista.
 */
export default function ChangePasswordForm() {
  const [valores, setValores] = useState<Valores>(VACIO);
  const [errores, setErrores] = useState<Partial<Record<Campo, string>>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function cambiar(campo: Campo, valor: string) {
    setValores((anteriores) => ({ ...anteriores, [campo]: valor }));
    setErrores((anteriores) => {
      const copia = { ...anteriores };
      delete copia[campo];
      return copia;
    });
    setAviso(null);
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando) return;

    const erroresLocales = validar(valores);
    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      setErrorGeneral(null);
      setAviso(null);
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);
    setAviso(null);

    try {
      await changePassword(valores.currentPassword, valores.newPassword);
      setValores(VACIO);
      setErrores({});
      setAviso(
        "Contraseña cambiada. Sigues dentro, y las sesiones abiertas en otros navegadores o equipos se han cerrado.",
      );
    } catch (e) {
      if (!(e instanceof ApiError)) {
        setErrorGeneral("No se ha podido cambiar la contraseña. Inténtalo de nuevo.");
      } else if (e.status === 400) {
        setErrores({ currentPassword: e.message });
      } else if ("new_password" in e.fieldErrors) {
        // 422: Pydantic responde en inglés; se muestra la regla en español.
        setErrores({ newPassword: API_FIELD_MESSAGES.password });
      } else {
        setErrorGeneral(e.message);
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form
      onSubmit={enviar}
      noValidate
      className="max-w-lg space-y-5 rounded-lg border border-marca-800 bg-marca-900 p-6"
    >
      <FormField
        id="currentPassword"
        label="Contraseña actual"
        type="password"
        autoComplete="current-password"
        required
        value={valores.currentPassword}
        onChange={(valor) => cambiar("currentPassword", valor)}
        error={errores.currentPassword}
      />

      <FormField
        id="newPassword"
        label="Contraseña nueva"
        type="password"
        autoComplete="new-password"
        required
        hint={`Al menos ${MIN_PASSWORD_LENGTH} caracteres, distinta de la actual.`}
        value={valores.newPassword}
        onChange={(valor) => cambiar("newPassword", valor)}
        error={errores.newPassword}
      />

      <FormField
        id="newPasswordConfirm"
        label="Repite la contraseña nueva"
        type="password"
        autoComplete="new-password"
        required
        value={valores.newPasswordConfirm}
        onChange={(valor) => cambiar("newPasswordConfirm", valor)}
        error={errores.newPasswordConfirm}
      />

      <FormAlert texto={errorGeneral} />

      {/* Siempre montado, para que aria-live lea el aviso al aparecer. */}
      <div aria-live="polite">
        {aviso && (
          <p className="rounded-md border border-emerald-800 bg-emerald-950 px-3 py-2 text-sm text-emerald-100">
            {aviso}
          </p>
        )}
      </div>

      <button type="submit" disabled={enviando} className={SUBMIT_CLASS}>
        {enviando ? "Guardando…" : "Cambiar la contraseña"}
      </button>
    </form>
  );
}
