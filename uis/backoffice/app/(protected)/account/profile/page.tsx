import type { Metadata } from "next";
import Link from "next/link";
import ProfileForm from "@/components/ProfileForm";

export const metadata: Metadata = {
  title: "Mi perfil · Backoffice · Nexova Solutions",
};

export default function ProfilePage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Mi perfil</h1>
        <p className="mt-1 text-sm text-slate-400">Tu cuenta y tus datos de contacto</p>
      </header>

      <ProfileForm />

      <section
        aria-labelledby="password-heading"
        className="mt-6 max-w-lg rounded-lg border border-marca-800 bg-marca-900 p-6"
      >
        <h2 id="password-heading" className="text-sm font-semibold text-white">
          Contraseña
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Al cambiarla se cierran las sesiones abiertas en otros navegadores o equipos.
        </p>
        <Link
          href="/account/change-password"
          className="mt-4 inline-block rounded-md border border-marca-700 px-3 py-1.5 text-sm text-slate-200 transition-colors hover:bg-marca-800 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        >
          Cambiar la contraseña
        </Link>
      </section>
    </div>
  );
}
