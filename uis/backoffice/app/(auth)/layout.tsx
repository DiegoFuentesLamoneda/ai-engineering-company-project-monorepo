import BrandLogo from "@/components/BrandLogo";
import { COMPANY } from "@/lib/company";

/**
 * Layout de /login y /register: una tarjeta centrada, sin barra lateral.
 * Sin sesión, la navegación del backoffice solo llevaría a pantallas que
 * devuelven a /login.
 */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <BrandLogo className="mx-auto h-8 w-auto text-white" />
          <p className="mt-3 text-xs uppercase tracking-wider text-acento-400">Backoffice</p>
        </div>

        <main className="rounded-lg border border-marca-800 bg-marca-900 p-6 shadow-lg">
          {children}
        </main>

        <p className="mt-6 text-center text-xs text-slate-500">
          Herramienta de uso interno de {COMPANY.name}.
        </p>
      </div>
    </div>
  );
}
