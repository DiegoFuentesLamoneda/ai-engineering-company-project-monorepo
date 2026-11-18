import type { Metadata } from "next";
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
    </div>
  );
}
