import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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
 * Layout raíz: lo común a todas las pantallas del backoffice (documento,
 * tipografías, estilos y tema oscuro). Nada más.
 *
 * Lo demás depende del grupo de rutas:
 * - app/(protected)/layout.tsx: barra lateral y navegación, para las vistas
 *   que exigen sesión.
 * - app/(auth)/layout.tsx: /login y /register, sin navegación.
 *
 * Es un único layout raíz a propósito. Con uno por grupo, pasar de /login al
 * panel recargaría la página entera.
 */
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-marca-950 text-slate-100">{children}</body>
    </html>
  );
}
