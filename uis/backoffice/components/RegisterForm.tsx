"use client";

import { useState } from "react";
import Link from "next/link";
import FormField, { FormAlert, SUBMIT_CLASS } from "@/components/FormField";
import {
  API_FIELD_MESSAGES,
  MIN_PASSWORD_LENGTH,
  checkAddress,
  checkEmail,
  checkName,
  checkNewPassword,
  checkPhone,
  textOrNull,
} from "@/lib/account";
import { ApiError, register } from "@/lib/api";

interface Valores {
  email: string;
  password: string;
  /** Solo en el formulario: no hay forma de recuperar una contraseña mal escrita. */
  passwordConfirm: string;
  name: string;
  phone: string;
  address: string;
}

type Campo = keyof Valores;

const VALORES_INICIALES: Valores = {
  email: "",
  password: "",
  passwordConfirm: "",
  name: "",
  phone: "",
  address: "",
};

function validar(valores: Valores): Partial<Record<Campo, string>> {
  const errores: Partial<Record<Campo, string>> = {
    email: checkEmail(valores.email),
    password: checkNewPassword(valores.password),
    passwordConfirm:
      valores.passwordConfirm !== valores.password ? "Las contraseñas no coinciden." : undefined,
    name: checkName(valores.name),
    phone: checkPhone(valores.phone),
    address: checkAddress(valores.address),
  };
  // Fuera los campos sin error, para que "hay errores" sea "hay claves".
  return Object.fromEntries(Object.entries(errores).filter(([, texto]) => texto));
}

/**
 * Registro: POST /users con las credenciales y el perfil opcional, y después
 * POST /auth/login con las mismas credenciales (lo hace register()). Si todo
 * sale bien hay sesión, y GuestGuard lleva al panel.
 */
export default function RegisterForm() {
  const [valores, setValores] = useState<Valores>(VALORES_INICIALES);
  const [errores, setErrores] = useState<Partial<Record<Campo, string>>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function cambiar(campo: Campo, valor: string) {
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

    let dentro = false;
    try {
      await register({
        email: valores.email.trim(),
        password: valores.password,
        name: textOrNull(valores.name),
        phone: textOrNull(valores.phone),
        address: textOrNull(valores.address),
      });
      dentro = true;
    } catch (e) {
      if (!(e instanceof ApiError)) {
        setErrorGeneral("No se ha podido crear la cuenta. Inténtalo de nuevo.");
        return;
      }

      // 409: el email ya tiene cuenta. Es un error del campo email.
      if (e.status === 409) {
        setErrores({ email: e.message });
        setErrorGeneral(null);
        return;
      }

      // 422: cada campo que rechaza la API, bajo su input y en español.
      const erroresApi: Partial<Record<Campo, string>> = {};
      for (const campo of Object.keys(e.fieldErrors)) {
        if (campo in API_FIELD_MESSAGES) {
          erroresApi[campo as Campo] = API_FIELD_MESSAGES[campo];
        }
      }
      setErrores(erroresApi);
      setErrorGeneral(
        Object.keys(erroresApi).length > 0
          ? "La API ha rechazado el registro. Revisa los campos marcados."
          : e.message,
      );
    } finally {
      // Si sale bien, enviando se queda a true hasta que la guardia navega:
      // así no se envía dos veces. Si falla, por la vía que sea, se reactiva.
      if (!dentro) setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} noValidate className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight text-white">Crear una cuenta</h1>
        <p className="mt-1 text-sm text-slate-400">
          Al crearla se inicia la sesión. Los datos de contacto puedes completarlos después
          en tu perfil.
        </p>
      </header>

      <FormField
        id="email"
        label="Email"
        type="email"
        autoComplete="email"
        required
        value={valores.email}
        onChange={(valor) => cambiar("email", valor)}
        error={errores.email}
      />

      <FormField
        id="password"
        label="Contraseña"
        type="password"
        autoComplete="new-password"
        required
        hint={`Al menos ${MIN_PASSWORD_LENGTH} caracteres.`}
        value={valores.password}
        onChange={(valor) => cambiar("password", valor)}
        error={errores.password}
      />

      <FormField
        id="passwordConfirm"
        label="Repite la contraseña"
        type="password"
        autoComplete="new-password"
        required
        value={valores.passwordConfirm}
        onChange={(valor) => cambiar("passwordConfirm", valor)}
        error={errores.passwordConfirm}
      />

      <fieldset className="space-y-5 border-t border-marca-800 pt-5">
        <legend className="sr-only">Perfil</legend>
        <p className="text-sm text-slate-400" aria-hidden="true">
          Perfil
        </p>

        <FormField
          id="name"
          label="Nombre"
          autoComplete="name"
          value={valores.name}
          onChange={(valor) => cambiar("name", valor)}
          error={errores.name}
        />

        <FormField
          id="phone"
          label="Teléfono"
          type="tel"
          autoComplete="tel"
          placeholder="+34 600 000 000"
          value={valores.phone}
          onChange={(valor) => cambiar("phone", valor)}
          error={errores.phone}
        />

        <FormField
          id="address"
          label="Dirección"
          autoComplete="street-address"
          value={valores.address}
          onChange={(valor) => cambiar("address", valor)}
          error={errores.address}
        />
      </fieldset>

      <FormAlert texto={errorGeneral} />

      <button type="submit" disabled={enviando} className={SUBMIT_CLASS}>
        {enviando ? "Creando la cuenta…" : "Crear la cuenta"}
      </button>

      <p className="text-center text-sm text-slate-400">
        ¿Ya tienes cuenta?{" "}
        <Link
          href="/login"
          className="text-acento-400 underline underline-offset-4 hover:text-acento-300"
        >
          Iniciar sesión
        </Link>
      </p>
    </form>
  );
}
