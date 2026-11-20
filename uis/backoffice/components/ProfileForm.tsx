"use client";

import { useEffect, useState } from "react";
import FormField, { FormAlert, SUBMIT_CLASS } from "@/components/FormField";
import {
  API_FIELD_MESSAGES,
  checkAddress,
  checkName,
  checkPhone,
  notifyProfileChange,
  textOrNull,
} from "@/lib/account";
import { ApiError, getMe, updateMyProfile } from "@/lib/api";
import type { Profile, ProfileFields, ProfileUpdate } from "@/types/auth";

type Campo = keyof ProfileFields;
type Valores = Record<Campo, string>;

const CAMPOS: Campo[] = ["name", "phone", "address"];

/**
 * En el formulario un dato que falta es "", en la API es null. Si el perfil
 * entero no llega, el formulario sale vacío en vez de romperse.
 */
function aValores(perfil: Profile | null | undefined): Valores {
  return {
    name: perfil?.name ?? "",
    phone: perfil?.phone ?? "",
    address: perfil?.address ?? "",
  };
}

function validar(valores: Valores): Partial<Record<Campo, string>> {
  const errores: Partial<Record<Campo, string>> = {
    name: checkName(valores.name),
    phone: checkPhone(valores.phone),
    address: checkAddress(valores.address),
  };
  return Object.fromEntries(Object.entries(errores).filter(([, texto]) => texto));
}

/**
 * Solo los campos que han cambiado respecto a lo guardado. PUT /profiles/me
 * deja como está lo que no llega y borra lo que llega a null, así que
 * vaciar un campo lo borra en la API.
 */
function cambiosDesde(guardado: Valores, valores: Valores): ProfileUpdate {
  const cambios: ProfileUpdate = {};
  for (const campo of CAMPOS) {
    const nuevo = textOrNull(valores[campo]);
    if (nuevo !== textOrNull(guardado[campo])) cambios[campo] = nuevo;
  }
  return cambios;
}

/**
 * Mi perfil: el email de la cuenta y los datos de contacto, que se leen de
 * GET /auth/me y se guardan con PUT /profiles/me. El token lo pone
 * lib/api.ts en cada petición.
 */
export default function ProfileForm() {
  const [email, setEmail] = useState<string | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  /** Lo último que la API ha confirmado: contra esto se miran los cambios. */
  const [guardado, setGuardado] = useState<Valores | null>(null);
  const [valores, setValores] = useState<Valores>({ name: "", phone: "", address: "" });
  const [errores, setErrores] = useState<Partial<Record<Campo, string>>>({});
  const [errorGeneral, setErrorGeneral] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  // Cada «Reintentar» suma uno y vuelve a pedir el perfil.
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vigente = true;
    getMe()
      .then((me) => {
        if (!vigente) return;
        setEmail(me?.email ?? null);
        setGuardado(aValores(me?.profile));
        setValores(aValores(me?.profile));
      })
      .catch((e) => {
        if (!vigente) return;
        setErrorCarga(e instanceof ApiError ? e.message : "No se ha podido cargar tu perfil.");
      });
    return () => {
      vigente = false;
    };
  }, [intento]);

  function reintentarCarga() {
    // Se quita el error para que vuelva a salir "Cargando tu perfil…".
    setErrorCarga(null);
    setIntento((n) => n + 1);
  }

  function cambiar(campo: Campo, valor: string) {
    setValores((anteriores) => ({ ...anteriores, [campo]: valor }));
    setErrores((anteriores) => {
      const copia = { ...anteriores };
      delete copia[campo];
      return copia;
    });
    // "Cambios guardados" deja de ser verdad en cuanto se toca algo.
    setAviso(null);
  }

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    if (enviando || !guardado) return;

    const erroresLocales = validar(valores);
    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      setErrorGeneral("Revisa los campos marcados.");
      setAviso(null);
      return;
    }

    const cambios = cambiosDesde(guardado, valores);
    if (Object.keys(cambios).length === 0) {
      setErrorGeneral(null);
      setAviso("No hay cambios que guardar.");
      return;
    }

    setEnviando(true);
    setErrorGeneral(null);
    setAviso(null);

    try {
      const perfil = await updateMyProfile(cambios);
      // Se muestra lo que ha guardado la API (sin espacios sobrantes, por ejemplo).
      setGuardado(aValores(perfil));
      setValores(aValores(perfil));
      setAviso("Cambios guardados.");
      notifyProfileChange(perfil);
    } catch (e) {
      if (!(e instanceof ApiError)) {
        setErrorGeneral("No se han podido guardar los cambios. Inténtalo de nuevo.");
        return;
      }
      const erroresApi: Partial<Record<Campo, string>> = {};
      for (const campo of Object.keys(e.fieldErrors)) {
        if ((CAMPOS as string[]).includes(campo)) {
          erroresApi[campo as Campo] = API_FIELD_MESSAGES[campo];
        }
      }
      setErrores(erroresApi);
      setErrorGeneral(
        Object.keys(erroresApi).length > 0
          ? "La API ha rechazado los cambios. Revisa los campos marcados."
          : e.message,
      );
    } finally {
      setEnviando(false);
    }
  }

  if (errorCarga) {
    return (
      <div role="alert" className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-100">
        <p className="font-medium">No se ha podido cargar tu perfil</p>
        <p className="mt-1">{errorCarga}</p>
        <button
          type="button"
          onClick={reintentarCarga}
          className="mt-3 rounded-md border border-red-400 px-3 py-1.5 text-sm font-medium text-red-50 transition-colors hover:bg-red-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!guardado) {
    return (
      <p role="status" className="py-12 text-center text-sm text-slate-400">
        Cargando tu perfil…
      </p>
    );
  }

  return (
    <form
      onSubmit={enviar}
      noValidate
      className="max-w-lg space-y-5 rounded-lg border border-marca-800 bg-marca-900 p-6"
    >
      <div>
        <p className="mb-1 text-xs uppercase tracking-wide text-slate-400">Email</p>
        <p className="text-sm text-white">{email ?? "—"}</p>
        <p className="mt-1 text-xs text-slate-500">
          Es el email con el que entras. No se puede cambiar desde aquí.
        </p>
      </div>

      <p className="border-t border-marca-800 pt-5 text-sm text-slate-400">
        Los datos de contacto son opcionales. Deja un campo vacío para borrarlo.
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

      <FormAlert texto={errorGeneral} />

      <div aria-live="polite">
        {aviso && <p className="text-sm text-emerald-300">{aviso}</p>}
      </div>

      <button type="submit" disabled={enviando} className={SUBMIT_CLASS}>
        {enviando ? "Guardando…" : "Guardar cambios"}
      </button>
    </form>
  );
}
