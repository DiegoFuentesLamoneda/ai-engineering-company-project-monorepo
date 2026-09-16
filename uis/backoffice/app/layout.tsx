import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import AppNav from "@/components/AppNav";
import BrandLogo from "@/components/BrandLogo";
import { COMPANY } from "@/lib/company";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Backoffice · Nexova Solutions",
  description:
    "Aplicación interna de Nexova Solutions para las operaciones de selección de talento",
};

/**
 * Layout propio del backoffice, distinto del de la web publica: barra lateral
 * de navegacion en escritorio, cabecera con las secciones en movil y un aviso
 * permanente de que lo que se ve aqui es informacion interna.
 */
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-marca-950 text-slate-100">
        <div className="flex min-h-screen flex-col md:flex-row">
          {/* Barra lateral: solo en escritorio. */}
          <aside className="hidden w-64 shrink-0 flex-col border-r border-marca-800 bg-marca-900 md:flex">
            <div className="px-5 py-6">
              <BrandLogo className="h-7 w-auto text-white" />
              <p className="mt-3 text-xs uppercase tracking-wider text-acento-400">
                Backoffice
              </p>
            </div>

            <div className="px-2">
              <AppNav />
            </div>

            <div className="mt-auto border-t border-marca-800 px-5 py-4 text-xs text-slate-400">
              <p className="font-medium text-slate-300">{COMPANY.name}</p>
              {COMPANY.offices.map((oficina) => (
                <p key={oficina}>{oficina}</p>
              ))}
            </div>
          </aside>

          {/* Cabecera: solo en movil, con las mismas secciones. */}
          <header className="border-b border-marca-800 bg-marca-900 px-4 py-3 md:hidden">
            <div className="mb-3 flex items-baseline gap-3">
              <BrandLogo className="h-6 w-auto text-white" />
              <span className="text-xs uppercase tracking-wider text-acento-400">
                Backoffice
              </span>
            </div>
            <AppNav orientation="horizontal" />
          </header>

          <div className="flex min-w-0 flex-1 flex-col">
            <main className="flex-1">{children}</main>

            <footer className="border-t border-marca-800 px-6 py-4 text-xs text-slate-500">
              Herramienta de uso interno. Las candidaturas y las notas son
              información sobre personas: no se comparten fuera de Nexova.
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
