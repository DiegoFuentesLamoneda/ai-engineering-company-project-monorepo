/**
 * Cableado del banco de pruebas.
 *
 * Este archivo no tiene lógica de negocio: solo lee los controles, llama a
 * `@repo/talent-core` y pinta lo que devuelve. Toda la inteligencia vive en el
 * paquete, que es justo lo que el hito quiere demostrar — la misma capa lógica
 * servirá luego a la API y a la interfaz real de los consultores.
 */

import {
  AVAILABILITY_STATUSES,
  SENIORITY_LEVELS,
  binarySearchCandidateBySalary,
  calculateAverageSalary,
  calculateVacancyFillRate,
  countCandidatesByStatus,
  filterCandidatesByAvailability,
  filterCandidatesBySeniority,
  filterCandidatesBySkills,
  findCandidateByEmail,
  findCandidateById,
  findTopSkills,
  groupCandidatesBySeniority,
  rankCandidatesForVacancy,
  sampleCandidates,
  sampleProcesses,
  sampleVacancies,
  sortCandidatesByExperience,
  sortCandidatesBySalary,
  sortCandidatesBySeniorityThenSalary,
  summarizeExpectedSalaries,
  validateCandidate,
} from "./dist/index.js";

const $ = (id) => document.getElementById(id);

const titulo = $("resultado-titulo");
const nota = $("resultado-nota");
const cuerpo = $("resultado-cuerpo");

// --- Pintado ---------------------------------------------------------------

/** Construye una tabla accesible a partir de cabeceras y filas. */
function tabla(headers, rows) {
  if (rows.length === 0) {
    return `<p class="text-sm text-marca-600">Ningún resultado.</p>`;
  }

  const th = headers
    .map(
      (h) =>
        `<th scope="col" class="border-b border-marca-200 px-3 py-2 text-left font-semibold whitespace-nowrap">${h}</th>`,
    )
    .join("");

  const tr = rows
    .map(
      (row) =>
        `<tr class="odd:bg-marca-50">${row
          .map((cell) => `<td class="border-b border-marca-100 px-3 py-2 align-top">${cell}</td>`)
          .join("")}</tr>`,
    )
    .join("");

  return `<table class="w-full min-w-[36rem] text-sm"><thead>${th ? `<tr>${th}</tr>` : ""}</thead><tbody>${tr}</tbody></table>`;
}

function mostrar(titulo_, nota_, html) {
  titulo.textContent = titulo_;
  nota.textContent = nota_;
  cuerpo.innerHTML = html;
}

/** Tabla estándar de candidatos, la que se usa en casi todas las respuestas. */
function tablaCandidatos(candidates) {
  return tabla(
    ["Id", "Candidato", "Seniority", "Años", "Inglés", "Pide", "Disponibilidad", "Estado"],
    candidates.map((c) => [
      c.id,
      c.fullName,
      c.seniority,
      c.yearsOfExperience,
      c.englishLevel,
      `${c.expectedSalary.toLocaleString("es-ES")} USD`,
      c.availability,
      c.status,
    ]),
  );
}

function resultadoValidacion(candidate, { valid, errors }) {
  if (valid) {
    return `<p class="rounded border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-900">
      <strong>${candidate.fullName}</strong> pasa todas las reglas de negocio.</p>`;
  }

  return `<p class="mb-2 text-sm">La ficha de <strong>${candidate.fullName}</strong> tiene ${errors.length} ${errors.length === 1 ? "error" : "errores"}:</p>
    <ul class="space-y-1">${errors
      .map(
        (e) =>
          `<li class="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">${e}</li>`,
      )
      .join("")}</ul>`;
}

// --- Controles -------------------------------------------------------------

const vacanteSelect = $("vacante");

function poblarControles() {
  $("dataset").textContent =
    `${sampleCandidates.length} candidatos · ${sampleVacancies.length} vacantes · ${sampleProcesses.length} procesos`;

  for (const nivel of SENIORITY_LEVELS) {
    $("seniority").insertAdjacentHTML("beforeend", `<option value="${nivel}">${nivel}</option>`);
  }

  for (const estado of AVAILABILITY_STATUSES) {
    const id = `disp-${estado.replace(/\s/g, "-")}`;
    $("availability").insertAdjacentHTML(
      "beforeend",
      `<label for="${id}" class="flex items-center gap-1.5 text-sm">
         <input type="checkbox" id="${id}" value="${estado}" class="rounded border-marca-400 text-marca-700 focus:ring-marca-400" />
         ${estado}
       </label>`,
    );
  }

  for (const vacancy of sampleVacancies) {
    vacanteSelect.insertAdjacentHTML(
      "beforeend",
      `<option value="${vacancy.id}">${vacancy.title} — ${vacancy.companyName}</option>`,
    );
  }
  describirVacante();
}

function vacanteSeleccionada() {
  return sampleVacancies.find((v) => v.id === vacanteSelect.value) ?? sampleVacancies[0];
}

function describirVacante() {
  const v = vacanteSeleccionada();
  $("vacante-detalle").textContent =
    `Pide ${v.requiredSkills.join(", ")} · ${v.minYearsExperience}-${v.maxYearsExperience} años · ` +
    `${v.requiredEnglishLevel} · ${v.requiredSeniority} · ` +
    `${v.salaryRangeMin.toLocaleString("es-ES")}-${v.salaryRangeMax.toLocaleString("es-ES")} USD`;
}

// --- Acciones --------------------------------------------------------------

function filtrar() {
  const skills = $("skills")
    .value.split(",")
    .map((s) => s.trim())
    .filter((s) => s !== "");
  const seniority = $("seniority").value;
  const disponibilidades = [...$("availability").querySelectorAll("input:checked")].map(
    (input) => input.value,
  );

  let resultado = sampleCandidates;
  const aplicados = [];

  if (skills.length > 0) {
    resultado = filterCandidatesBySkills(resultado, skills);
    aplicados.push(`habilidades: ${skills.join(", ")}`);
  }
  if (seniority !== "") {
    resultado = filterCandidatesBySeniority(resultado, seniority);
    aplicados.push(`seniority: ${seniority}`);
  }
  if (disponibilidades.length > 0) {
    resultado = filterCandidatesByAvailability(resultado, disponibilidades);
    aplicados.push(`disponibilidad: ${disponibilidades.join(" o ")}`);
  }

  mostrar(
    `${resultado.length} de ${sampleCandidates.length} candidatos`,
    aplicados.length > 0 ? `Filtros encadenados — ${aplicados.join(" · ")}` : "Sin filtros",
    tablaCandidatos(resultado),
  );
}

const ORDENACIONES = {
  salario: { fn: sortCandidatesBySalary, etiqueta: "salario esperado" },
  experiencia: { fn: sortCandidatesByExperience, etiqueta: "años de experiencia" },
  nivel: { fn: sortCandidatesBySeniorityThenSalary, etiqueta: "nivel y, a igualdad, salario" },
};

function ordenar(campo, order) {
  const { fn, etiqueta } = ORDENACIONES[campo];

  mostrar(
    `Ordenado por ${etiqueta}`,
    `${order === "asc" ? "Ascendente" : "Descendente"} · la lista original no se modifica`,
    tablaCandidatos(fn(sampleCandidates, order)),
  );
}

function buscarPorId() {
  const id = $("buscar-id").value.trim();
  const encontrado = findCandidateById(sampleCandidates, id);

  mostrar(
    "Búsqueda lineal por id",
    `findCandidateById(candidates, "${id}") → ${encontrado === null ? "null" : encontrado.fullName}`,
    encontrado === null
      ? `<p class="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">No hay ningún candidato con ese id. La función devuelve <code>null</code>, no un error.</p>`
      : tablaCandidatos([encontrado]),
  );
}

function buscarPorEmail() {
  const email = $("buscar-email").value.trim();
  const encontrado = findCandidateByEmail(sampleCandidates, email);

  mostrar(
    "Búsqueda lineal por email",
    `Comparación sin distinguir mayúsculas → ${encontrado === null ? "null" : encontrado.fullName}`,
    encontrado === null
      ? `<p class="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">Ningún candidato con ese email. Devuelve <code>null</code>.</p>`
      : tablaCandidatos([encontrado]),
  );
}

function buscarPorSalario() {
  const objetivo = Number($("buscar-salario").value);

  // La binaria exige el array ordenado: se ordena primero, siempre.
  const ordenados = sortCandidatesBySalary(sampleCandidates, "asc");
  const indice = binarySearchCandidateBySalary(ordenados, objetivo);

  const secuencia = ordenados
    .map((c, i) => {
      const activo = i === indice;
      return `<span class="inline-block rounded px-1.5 py-0.5 ${activo ? "bg-acento-400 font-bold text-marca-950" : "text-marca-600"}">${c.expectedSalary.toLocaleString("es-ES")}</span>`;
    })
    .join("");

  mostrar(
    "Búsqueda binaria por salario esperado",
    indice === -1
      ? `Ningún candidato pide ${objetivo.toLocaleString("es-ES")} USD → devuelve -1`
      : `Encontrado en el índice ${indice}`,
    `<p class="mb-3 text-sm text-marca-700">Lista ordenada ascendente, que es la precondición del algoritmo:</p>
     <p class="mb-4 text-sm">${secuencia}</p>
     ${indice === -1 ? "" : tablaCandidatos([ordenados[indice]])}`,
  );
}

function rankear() {
  const vacancy = vacanteSeleccionada();
  const ranking = rankCandidatesForVacancy(sampleCandidates, vacancy);

  mostrar(
    `Ranking para ${vacancy.title}`,
    `${vacancy.companyName} · ${vacancy.id} · puntuación de 0 a 100`,
    tabla(
      ["#", "Puntuación", "Candidato", "Seniority", "Inglés", "Años", "Pide"],
      ranking.map(({ candidate, score }, i) => [
        i + 1,
        `<span class="inline-block min-w-10 rounded px-2 py-0.5 text-center font-bold ${
          score >= 80
            ? "bg-green-100 text-green-900"
            : score >= 50
              ? "bg-acento-300 text-marca-950"
              : "bg-marca-100 text-marca-700"
        }">${score}</span>`,
        candidate.fullName,
        candidate.seniority,
        candidate.englishLevel,
        candidate.yearsOfExperience,
        `${candidate.expectedSalary.toLocaleString("es-ES")} USD`,
      ]),
    ),
  );
}

function reportePorEstado() {
  const conteo = countCandidatesByStatus(sampleCandidates);

  mostrar(
    "Candidatos por estado",
    "Los cuatro estados salen siempre, aunque estén a cero",
    tabla(
      ["Estado", "Candidatos"],
      Object.entries(conteo).map(([estado, n]) => [estado, n]),
    ),
  );
}

function reportePorSeniority() {
  const grupos = groupCandidatesBySeniority(sampleCandidates);

  mostrar(
    "Candidatos por seniority",
    "Los cinco niveles salen siempre, aunque estén vacíos",
    tabla(
      ["Nivel", "Candidatos", "Quiénes"],
      Object.entries(grupos).map(([nivel, lista]) => [
        nivel,
        lista.length,
        lista.map((c) => c.fullName).join(" · ") || "—",
      ]),
    ),
  );
}

function reporteTopSkills() {
  const top = findTopSkills(sampleCandidates, 10);

  mostrar(
    "Habilidades más frecuentes",
    "Agrupadas sin distinguir mayúsculas · empates resueltos alfabéticamente",
    tabla(
      ["Habilidad", "Candidatos"],
      top.map((s) => [s.skill, s.count]),
    ),
  );
}

function reporteMetricas() {
  const usd = (n) => `${n.toLocaleString("es-ES")} USD`;
  const salarios = summarizeExpectedSalaries(sampleCandidates);

  const filas = [
    ["Salario esperado medio", usd(calculateAverageSalary(sampleCandidates))],
    ["Tasa de cobertura de vacantes", `${calculateVacancyFillRate(sampleProcesses)} %`],
    ["Procesos registrados", sampleProcesses.length],
  ];

  // `summarizeExpectedSalaries` devuelve null si no hay candidatos: el mínimo
  // de un conjunto vacío no existe.
  if (salarios !== null) {
    filas.push(
      ["Coste total de la base de talento", usd(salarios.total)],
      ["Salario esperado más bajo", usd(salarios.min)],
      ["Salario esperado más alto", usd(salarios.max)],
    );
  }

  mostrar(
    "Métricas del informe semanal",
    "Las cifras que hoy se preparan a mano para dirección",
    tabla(["Métrica", "Valor"], filas),
  );
}

function validar(roto) {
  const base = sampleCandidates[0];
  const candidate = roto
    ? {
        ...base,
        yearsOfExperience: 80,
        currentSalary: 0,
        expectedSalary: -100,
        skills: [],
        email: "esto-no-es-un-email",
        phone: "   ",
      }
    : base;

  mostrar(
    roto ? "Ficha rota a propósito" : "Ficha correcta",
    "validateCandidate acumula todos los errores, no para en el primero",
    resultadoValidacion(candidate, validateCandidate(candidate)),
  );
}

function limpiar() {
  $("skills").value = "";
  $("seniority").value = "";
  for (const input of $("availability").querySelectorAll("input")) input.checked = false;
  filtrar();
}

// --- Arranque --------------------------------------------------------------

const acciones = {
  filtrar,
  limpiar,
  "salario-asc": () => ordenar("salario", "asc"),
  "salario-desc": () => ordenar("salario", "desc"),
  "experiencia-asc": () => ordenar("experiencia", "asc"),
  "experiencia-desc": () => ordenar("experiencia", "desc"),
  "nivel-asc": () => ordenar("nivel", "asc"),
  "nivel-desc": () => ordenar("nivel", "desc"),
  "buscar-id": buscarPorId,
  "buscar-email": buscarPorEmail,
  "buscar-salario": buscarPorSalario,
  rankear,
  "por-estado": reportePorEstado,
  "por-seniority": reportePorSeniority,
  "top-skills": reporteTopSkills,
  metricas: reporteMetricas,
  "validar-ok": () => validar(false),
  "validar-ko": () => validar(true),
};

document.addEventListener("click", (event) => {
  const boton = event.target.closest("[data-action]");
  if (boton === null) return;

  const accion = acciones[boton.dataset.action];
  if (accion !== undefined) accion();
});

vacanteSelect.addEventListener("change", describirVacante);

poblarControles();
mostrar(
  "Base de talento completa",
  `${sampleCandidates.length} candidatos de ejemplo — usa los controles de la izquierda`,
  tablaCandidatos(sampleCandidates),
);
