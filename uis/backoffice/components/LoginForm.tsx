"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import FormField, { FormAlert, SUBMIT_CLASS } from "@/components/FormField";
import { checkEmail } from "@/lib/account";
import { ApiError, login } from "@/lib/api";

type Campo = "email" | "password";

/**
 * Inicio de sesión: POST /auth/login con email y contraseña. Si sale bien,
 * login() guarda el token y se entra al panel.
 *
 * Un error de credenciales no se marca en un campo concreto: decir "este
 * email no existe" le confirmaría a un atacante qué cuentas hay. La API
 * responde lo mismo en los dos casos, y aquí también.
 */
export default function LoginForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errores, setErrores] = useState<Partial<Record<Campo, string>>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
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
    if (enviando) return;

    const erroresLocales: Partial<Record<Campo, string>> = {};
    const errorEmail = checkEmail(email);
    if (errorEmail) erroresLocales.email = errorEmail;
    if (!password) erroresLocales.password = "Escribe tu contraseña.";

    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      setErrorGeneral(null);
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);

    try {
      await login(email.trim(), password);
      // replace y no push: con "atrás" no se vuelve al formulario de login.
      router.replace("/");
    } catch (e) {
      setErrorGeneral(
        e instanceof ApiError ? e.message : "No se ha podido iniciar sesión. Inténtalo de nuevo.",
      );
      // La contraseña se vacía tras un fallo; el email se deja para corregirlo.
      setPassword("");
      setEnviando(false);
    }
    // Si sale bien, enviando se queda a true: el botón sigue desactivado
    // hasta que carga el panel y no se puede enviar dos veces.
  }

  return (
    <form onSubmit={enviar} noValidate className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight text-white">Iniciar sesión</h1>
        <p className="mt-1 text-sm text-slate-400">Entra con el email de tu cuenta.</p>
      </header>

      <FormField
        id="email"
        label="Email"
        type="email"
        autoComplete="email"
        required
        value={email}
        onChange={(valor) => {
          setEmail(valor);
          limpiarError("email");
        }}
        error={errores.email}
      />

      <FormField
        id="password"
        label="Contraseña"
        type="password"
        autoComplete="current-password"
        required
        value={password}
        onChange={(valor) => {
          setPassword(valor);
          limpiarError("password");
        }}
        error={errores.password}
      />

      <FormAlert texto={errorGeneral} />

      <button type="submit" disabled={enviando} className={SUBMIT_CLASS}>
        {enviando ? "Entrando…" : "Iniciar sesión"}
      </button>

      <p className="text-center text-sm text-slate-400">
        ¿No tienes cuenta?{" "}
        <Link
          href="/register"
          className="text-acento-400 underline underline-offset-4 hover:text-acento-300"
        >
          Crear una cuenta
        </Link>
      </p>
    </form>
  );
}
