import type { Metadata } from "next";
import ResetPasswordForm from "@/components/ResetPasswordForm";

export const metadata: Metadata = {
  title: "Contraseña nueva · Backoffice · Nexova Solutions",
  // La URL lleva el token del enlace. Sin esto, al salir de la página hacia
  // otra web, el navegador podría mandarle la URL entera en la cabecera Referer.
  referrer: "no-referrer",
};

export default function ResetPasswordPage() {
  return <ResetPasswordForm />;
}
