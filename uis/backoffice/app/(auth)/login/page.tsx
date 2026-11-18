import type { Metadata } from "next";
import LoginForm from "@/components/LoginForm";
import SessionEndedNotice from "@/components/SessionEndedNotice";

export const metadata: Metadata = {
  title: "Iniciar sesión · Backoffice · Nexova Solutions",
};

export default function LoginPage() {
  return (
    <>
      <SessionEndedNotice />
      <LoginForm />
    </>
  );
}
