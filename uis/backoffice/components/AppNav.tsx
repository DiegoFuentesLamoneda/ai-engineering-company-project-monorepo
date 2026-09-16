"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  /** Descripcion breve, solo visible en la barra lateral. */
  hint: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Panel", hint: "Resumen de operaciones" },
  { href: "/candidates", label: "Candidaturas", hint: "Seguimiento del proceso activo" },
];

interface Props {
  /** "vertical" en la barra lateral, "horizontal" en la cabecera movil. */
  orientation?: "vertical" | "horizontal";
}

export default function AppNav({ orientation = "vertical" }: Props) {
  const ruta = usePathname();
  const esVertical = orientation === "vertical";

  return (
    <nav
      aria-label="Secciones del backoffice"
      className={esVertical ? "flex flex-col gap-1" : "flex gap-2 overflow-x-auto"}
    >
      {NAV_ITEMS.map((item) => {
        // "/" solo esta activo en la raiz; el resto tambien en sus subrutas.
        const activo =
          item.href === "/" ? ruta === "/" : ruta.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={activo ? "page" : undefined}
            className={`rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 ${
              activo
                ? "bg-marca-800 font-semibold text-white"
                : "text-slate-300 hover:bg-marca-800 hover:text-white"
            } ${esVertical ? "" : "whitespace-nowrap"}`}
          >
            {item.label}
            {esVertical && (
              <span className="mt-0.5 block text-xs font-normal text-slate-400">
                {item.hint}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
