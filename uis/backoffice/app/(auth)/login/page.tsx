import type { Metadata } from "next";
import LoginForm from "@/components/LoginForm";
import LoginNotice from "@/components/LoginNotice";

export const metadata: Metadata = {
  title: "Iniciar sesión · Backoffice · Nexova Solutions",
};

export default function LoginPage() {
  return (
    <>
      <LoginNotice />
      <LoginForm />
    </>
  );
}
