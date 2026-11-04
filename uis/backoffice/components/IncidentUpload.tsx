"use client";

import { useRef, useState, type ChangeEvent, type DragEvent } from "react";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

/**
 * Zona para soltar el CSV, o hacer clic y elegirlo.
 *
 * Es un <label> que envuelve un <input type="file"> oculto a la vista pero no
 * al teclado ni al lector de pantalla: con Tab se llega al input, el foco se
 * dibuja en la zona entera y Enter abre el selector. Arrastrar es un extra
 * para raton; elegir el fichero es lo que funciona siempre.
 */
export default function IncidentUpload({ onFile, disabled = false }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  // dragenter/dragleave saltan tambien al pasar por encima de cada hijo de la
  // zona. Contando entradas y salidas, el resaltado no parpadea.
  const profundidad = useRef(0);

  function handleDragEnter(e: DragEvent) {
    e.preventDefault();
    profundidad.current += 1;
    setIsDragging(true);
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    profundidad.current -= 1;
    if (profundidad.current === 0) setIsDragging(false);
  }

  // Sin preventDefault en dragover, el navegador no deja soltar aqui y abre
  // el fichero en la pestana.
  function handleDragOver(e: DragEvent) {
    e.preventDefault();
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    profundidad.current = 0;
    setIsDragging(false);

    const fichero = e.dataTransfer.files[0];
    if (fichero && !disabled) onFile(fichero);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const fichero = e.target.files?.[0];
    if (fichero) onFile(fichero);
    // Vaciar el input permite volver a elegir el mismo fichero: si no, el
    // navegador no dispara change porque "no ha cambiado nada".
    e.target.value = "";
  }

  return (
    <label
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-acento-400 ${
        disabled ? "cursor-wait opacity-60" : "cursor-pointer"
      } ${
        isDragging
          ? "border-acento-400 bg-marca-800"
          : "border-marca-700 bg-marca-900 hover:border-marca-500"
      }`}
    >
      <input
        type="file"
        accept=".csv,text/csv"
        onChange={handleChange}
        disabled={disabled}
        className="sr-only"
      />
      <span className="text-sm font-semibold text-white">
        {isDragging ? "Suelta el fichero aquí" : "Arrastra aquí el CSV del helpdesk"}
      </span>
      <span className="text-sm text-slate-400">
        o <span className="text-acento-400 underline">haz clic para elegirlo</span>
      </span>
      <span className="mt-2 text-xs text-slate-500">
        Exportación de tickets de soporte en CSV, codificada en UTF-8
      </span>
    </label>
  );
}
