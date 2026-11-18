import type { Metadata } from "next";
import Link from "next/link";
import ChangePasswordForm from "@/components/ChangePasswordForm";

export const metadata: Metadata = {
  title: "Cambiar la contraseña · Backoffice · Nexova Solutions",
};

export default function ChangePasswordPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-10">
      <p className="mb-4 text-sm">
        <Link
          href="/account/profile"
          className="text-acento-400 underline underline-offset-4 hover:text-acento-300"
        >
          ← Mi perfil
        </Link>
      </p>
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Cambiar la contraseña
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Con la actual. Si no la recuerdas, cierra sesión y usa «¿Olvidaste tu contraseña?».
        </p>
      </header>

      <ChangePasswordForm />
    </div>
  );
}
