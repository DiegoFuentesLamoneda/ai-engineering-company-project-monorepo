import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Para el navegador, localhost y 127.0.0.1 son origenes distintos aunque
  // apunten a la misma maquina: la politica del mismo origen compara el texto
  // del host, no la IP a la que resuelve. Next bloquea por defecto sus
  // recursos de desarrollo desde un origen que no sea el suyo, asi que
  // entrando por 127.0.0.1 el WebSocket de HMR y los chunks quedan
  // bloqueados, la pagina nunca se hidrata y los componentes se quedan
  // colgados en su estado de carga: sin error visible, porque la peticion a
  // la API ni siquiera llega a hacerse.
  //
  // Solo afecta a `next dev`. En produccion no tiene ningun efecto.
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
