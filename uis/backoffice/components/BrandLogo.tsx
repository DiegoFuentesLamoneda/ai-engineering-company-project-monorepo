/**
 * Logotipo de Nexova, la misma marca que la web publica en uis/website
 * (tres nodos en progresion ascendente; el superior, en ambar, es la posicion
 * cubierta). Va en linea en vez de como archivo para ahorrar una peticion y
 * para que el texto herede el color del contenedor: aqui el fondo es oscuro.
 */
export default function BrandLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 152 32"
      role="img"
      aria-label="Nexova"
      className={className}
    >
      <title>Nexova</title>
      <path
        d="M6 25 L15 17 L27 6"
        fill="none"
        stroke="#578dcd"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity=".7"
      />
      <circle cx="6" cy="25" r="4" fill="#336fb4" />
      <circle cx="15" cy="17" r="4" fill="#578dcd" />
      <circle cx="27" cy="6" r="4.5" fill="#eda820" />
      <text
        x="42"
        y="24"
        fill="currentColor"
        fontFamily="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
        fontSize="19"
        fontWeight="700"
        letterSpacing="1.6"
      >
        NEXOVA
      </text>
    </svg>
  );
}
