import type { Metadata } from "next";
import ForgotPasswordForm from "@/components/ForgotPasswordForm";

export const metadata: Metadata = {
  title: "Restablecer la contraseña · Backoffice · Nexova Solutions",
};

export default function ForgotPasswordPage() {
  return <ForgotPasswordForm />;
}
