import type { Metadata } from "next";
import RegisterForm from "@/components/RegisterForm";

export const metadata: Metadata = {
  title: "Crear una cuenta · Backoffice · Nexova Solutions",
};

export default function RegisterPage() {
  return <RegisterForm />;
}
