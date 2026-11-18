"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { subscribeToProfile } from "@/lib/account";
import { getMe, logout } from "@/lib/api";
import type { Me } from "@/types/auth";

/**
 * Quién ha entrado y el botón de cerrar sesión, en la barra superior de las
 * vistas protegidas.
 *
 * Cerrar sesión solo borra el token. No navega: AuthGuard ve que la sesión
 * ya no existe y lleva a /login, igual que si se cerrara en otra pestaña.
 */
export default function SessionMenu() {
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    // Si la vista se desmonta antes de que llegue la respuesta, se ignora.
    let vigente = true;
    getMe()
      .then((datos) => {
        if (vigente) setMe(datos);
      })
      // Sin datos se enseña solo el botón. Un 401 ya lo gestiona lib/api.ts,
      // que cierra la sesión, y la guardia lleva a /login.
      .catch(() => {});
    return () => {
      vigente = false;
    };
  }, []);

  // Al guardar el perfil, el nombre de aquí cambia sin recargar.
  useEffect(
    () =>
      subscribeToProfile((profile) => {
        setMe((actual) => (actual ? { ...actual, profile } : actual));
      }),
    [],
  );

  const nombre = me?.profile.name;

  return (
    <div className="flex items-center justify-end gap-4">
      {me && (
        <Link
          href="/account/profile"
          className="min-w-0 rounded-md text-right text-sm leading-tight hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          <span className="block truncate font-medium text-white">{nombre ?? me.email}</span>
          {nombre && <span className="block truncate text-xs text-slate-400">{me.email}</span>}
        </Link>
      )}
      <button
        type="button"
        onClick={logout}
        className="shrink-0 rounded-md border border-marca-700 px-3 py-1.5 text-sm text-slate-200 transition-colors hover:bg-marca-800 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
      >
        Cerrar sesión
      </button>
    </div>
  );
}
