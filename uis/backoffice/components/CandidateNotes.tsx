"use client";

import { useState } from "react";
import { ApiError, createNote, deleteNote } from "@/lib/api";
import { formatearFechaHora } from "@/lib/format";
import { useNotes } from "@/hooks/useNotes";

export default function CandidateNotes({ recordId }: { recordId: string }) {
  const { notes, setNotes, isLoading, error } = useNotes(recordId);

  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [borrandoId, setBorrandoId] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const textoValido = texto.trim().length > 0;

  async function anadirNota(evento: React.FormEvent) {
    evento.preventDefault();
    if (!textoValido || enviando) return;

    setEnviando(true);
    setErrorAccion(null);

    try {
      // El POST devuelve la nota creada: la anadimos arriba sin recargar.
      const nueva = await createNote(recordId, texto.trim());
      setNotes([nueva, ...notes]);
      setTexto("");
    } catch (e) {
      setErrorAccion(e instanceof ApiError ? e.message : "No se ha podido guardar la nota.");
    } finally {
      setEnviando(false);
    }
  }

  async function eliminarNota(noteId: string) {
    const confirmado = window.confirm(
      "¿Eliminar esta nota? Esta acción no se puede deshacer.",
    );
    if (!confirmado) return;

    setBorrandoId(noteId);
    setErrorAccion(null);

    try {
      await deleteNote(recordId, noteId);
      setNotes(notes.filter((nota) => nota.id !== noteId));
    } catch (e) {
      setErrorAccion(e instanceof ApiError ? e.message : "No se ha podido eliminar la nota.");
    } finally {
      setBorrandoId(null);
    }
  }

  return (
    <section className="mt-6 rounded-lg border border-marca-800 bg-marca-900 p-5">
      <h2 className="mb-4 text-sm font-semibold text-slate-200">Notas internas</h2>

      <form onSubmit={anadirNota} className="mb-5">
        <label htmlFor="nueva-nota" className="sr-only">
          Nueva nota
        </label>
        <textarea
          id="nueva-nota"
          value={texto}
          onChange={(evento) => setTexto(evento.target.value)}
          rows={3}
          placeholder="Anota aquí lo relevante de la llamada o la entrevista…"
          className="w-full rounded-md border border-marca-700 bg-marca-950 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400"
        />

        <div className="mt-2 flex items-center gap-3">
          <button
            type="submit"
            disabled={!textoValido || enviando}
            className="rounded-md bg-acento-500 px-4 py-2 text-sm font-semibold text-marca-950 transition-colors hover:bg-acento-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-acento-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {enviando ? "Guardando…" : "Añadir nota"}
          </button>

          {!textoValido && (
            <span className="text-xs text-slate-500">La nota no puede estar vacía.</span>
          )}
        </div>
      </form>

      {errorAccion && (
        <p className="mb-4 rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100">
          {errorAccion}
        </p>
      )}

      {isLoading && <p className="text-sm text-slate-400">Cargando notas…</p>}

      {!isLoading && error && (
        <p className="rounded-md border border-red-800 bg-red-950 px-3 py-2 text-sm text-red-100">
          {error}
        </p>
      )}

      {!isLoading && !error && notes.length === 0 && (
        <p className="text-sm text-slate-400">
          Todavía no hay notas para esta candidatura.
        </p>
      )}

      {!isLoading && !error && notes.length > 0 && (
        <ul className="space-y-3">
          {notes.map((nota) => (
            <li
              key={nota.id}
              className="rounded-md border border-marca-800 bg-marca-950 p-3"
            >
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm text-slate-100">{nota.content}</p>

                <button
                  type="button"
                  onClick={() => eliminarNota(nota.id)}
                  disabled={borrandoId === nota.id}
                  className="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-red-300 hover:bg-red-950 hover:text-red-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-400 disabled:opacity-50"
                >
                  {borrandoId === nota.id ? "Eliminando…" : "Eliminar"}
                </button>
              </div>

              <p className="mt-2 text-xs text-slate-500">
                {formatearFechaHora(nota.created_at)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
