import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { Candidate } from "../types/models.js";
import { makeCandidate, makeProcess, makeVacancy } from "../testing/factories.js";
import {
  calculateAverageSalary,
  calculateCandidateScore,
  calculateVacancyFillRate,
  countCandidatesByStatus,
  findTopSkills,
  groupCandidatesBySeniority,
  rankCandidatesForVacancy,
  summarizeExpectedSalaries,
} from "./transformations.js";

// La vacante del contexto: 3 requeridas, 2 preferidas, 4-8 años, B2, Senior,
// 5000-7000 USD.
const vacancy = makeVacancy();

/** Encaje perfecto con `vacancy`: los cinco bloques al máximo, 100 puntos. */
const perfectMatch: Partial<Candidate> = {
  skills: ["TypeScript", "React", "Node.js", "PostgreSQL", "Docker"],
  yearsOfExperience: 6,
  seniority: "Senior",
  englishLevel: "B2",
  expectedSalary: 6000,
};

/** Puntúa un candidato perfecto con un solo campo cambiado. */
const score = (overrides: Partial<Candidate> = {}): number =>
  calculateCandidateScore(makeCandidate({ ...perfectMatch, ...overrides }), vacancy);

describe("calculateCandidateScore · total", () => {
  it("da 100 al encaje perfecto", () => {
    assert.equal(score(), 100);
  });

  it("da 0 cuando no encaja nada", () => {
    assert.equal(
      score({
        skills: ["COBOL"],
        yearsOfExperience: 0,
        seniority: "Junior",
        englishLevel: "A1",
        expectedSalary: 20_000,
      }),
      0,
    );
  });
});

describe("calculateCandidateScore · habilidades (40 máx)", () => {
  it("da los 40 con todas las requeridas, aunque no tenga ninguna preferida", () => {
    assert.equal(score({ skills: ["TypeScript", "React", "Node.js"] }), 100);
  });

  it("da 20 con al menos la mitad de las requeridas", () => {
    assert.equal(score({ skills: ["TypeScript", "React"] }), 80);
  });

  it("da 0 con menos de la mitad de las requeridas", () => {
    assert.equal(score({ skills: ["TypeScript"] }), 60);
    assert.equal(score({ skills: [] }), 60);
  });

  it("suma 10 por preferida, y el bloque nunca pasa de 40", () => {
    // Media requeridas (20) + las dos preferidas (20) = 40 justos.
    assert.equal(score({ skills: ["TypeScript", "React", "PostgreSQL", "Docker"] }), 100);
    // Todas las requeridas (40) + una preferida (10) = 50, capado a 40.
    assert.equal(score({ skills: ["TypeScript", "React", "Node.js", "PostgreSQL"] }), 100);
    // Una requerida (0) + las dos preferidas (20) = 20.
    assert.equal(score({ skills: ["TypeScript", "PostgreSQL", "Docker"] }), 80);
  });

  it("compara las habilidades sin distinguir mayúsculas", () => {
    assert.equal(
      score({ skills: ["typescript", "react", "node.js", "postgresql", "docker"] }),
      100,
    );
  });

  it("da el tramo completo si la vacante no exige habilidades", () => {
    const sinRequisitos = makeVacancy({ requiredSkills: [], preferredSkills: [] });
    const candidate = makeCandidate({ ...perfectMatch, skills: [] });
    assert.equal(calculateCandidateScore(candidate, sinRequisitos), 100);
  });
});

describe("calculateCandidateScore · experiencia (20 máx)", () => {
  it("da 20 dentro del rango, extremos incluidos", () => {
    assert.equal(score({ yearsOfExperience: 4 }), 100);
    assert.equal(score({ yearsOfExperience: 8 }), 100);
  });

  it("da 10 si se sale del rango 1 o 2 años", () => {
    assert.equal(score({ yearsOfExperience: 3 }), 90);
    assert.equal(score({ yearsOfExperience: 2 }), 90);
    assert.equal(score({ yearsOfExperience: 9 }), 90);
    assert.equal(score({ yearsOfExperience: 10 }), 90);
  });

  it("da 0 si se sale más de 2 años", () => {
    assert.equal(score({ yearsOfExperience: 1 }), 80);
    assert.equal(score({ yearsOfExperience: 11 }), 80);
  });
});

describe("calculateCandidateScore · seniority (15 máx)", () => {
  it("da 15 al nivel exacto", () => {
    assert.equal(score({ seniority: "Senior" }), 100);
  });

  it("da 7 a un nivel de distancia, arriba o abajo", () => {
    assert.equal(score({ seniority: "Lead" }), 92);
    assert.equal(score({ seniority: "Semi-Senior" }), 92);
  });

  it("da 0 a dos niveles o más de distancia", () => {
    assert.equal(score({ seniority: "Junior" }), 85);
    assert.equal(score({ seniority: "Executive" }), 85);
  });
});

describe("calculateCandidateScore · inglés (15 máx)", () => {
  it("da 15 si iguala o supera el nivel pedido", () => {
    assert.equal(score({ englishLevel: "B2" }), 100);
    assert.equal(score({ englishLevel: "C1" }), 100);
    assert.equal(score({ englishLevel: "Native" }), 100);
  });

  it("da 0 si no llega", () => {
    assert.equal(score({ englishLevel: "B1" }), 85);
    assert.equal(score({ englishLevel: "A1" }), 85);
  });
});

describe("calculateCandidateScore · salario (10 máx)", () => {
  it("da 10 dentro del rango, extremos incluidos", () => {
    assert.equal(score({ expectedSalary: 5000 }), 100);
    assert.equal(score({ expectedSalary: 7000 }), 100);
  });

  it("da 10 si pide menos del mínimo: pedir poco no penaliza", () => {
    assert.equal(score({ expectedSalary: 3000 }), 100);
  });

  it("da 5 hasta un 20 % por encima del máximo", () => {
    assert.equal(score({ expectedSalary: 8000 }), 95);
    assert.equal(score({ expectedSalary: 8400 }), 95);
  });

  it("da 0 por encima de ese 20 %", () => {
    assert.equal(score({ expectedSalary: 8401 }), 90);
  });
});

describe("rankCandidatesForVacancy", () => {
  const alto = makeCandidate({ id: "C-alto", ...perfectMatch });
  const medio = makeCandidate({ id: "C-medio", ...perfectMatch, seniority: "Junior" });
  const bajo = makeCandidate({ id: "C-bajo", ...perfectMatch, skills: ["COBOL"] });

  it("ordena de mayor a menor puntuación", () => {
    const ranking = rankCandidatesForVacancy([bajo, alto, medio], vacancy);
    assert.deepEqual(
      ranking.map((r) => [r.candidate.id, r.score]),
      [
        ["C-alto", 100],
        ["C-medio", 85],
        ["C-bajo", 60],
      ],
    );
  });

  it("mantiene el orden de entrada en los empates", () => {
    const gemelo = makeCandidate({ id: "C-gemelo", ...perfectMatch });
    const ranking = rankCandidatesForVacancy([alto, gemelo], vacancy);
    assert.deepEqual(
      ranking.map((r) => r.candidate.id),
      ["C-alto", "C-gemelo"],
    );
  });

  it("devuelve vacío con una colección vacía", () => {
    assert.deepEqual(rankCandidatesForVacancy([], vacancy), []);
  });

  it("no modifica la colección recibida", () => {
    const candidates = [bajo, alto, medio];
    const original = candidates.map((c) => c.id);
    rankCandidatesForVacancy(candidates, vacancy);
    assert.deepEqual(
      candidates.map((c) => c.id),
      original,
    );
  });
});

describe("groupCandidatesBySeniority", () => {
  it("agrupa y deja vacíos los niveles sin candidatos", () => {
    const grupos = groupCandidatesBySeniority([
      makeCandidate({ id: "C-1", seniority: "Junior" }),
      makeCandidate({ id: "C-2", seniority: "Senior" }),
      makeCandidate({ id: "C-3", seniority: "Senior" }),
    ]);

    assert.deepEqual(
      Object.fromEntries(
        Object.entries(grupos).map(([nivel, lista]) => [nivel, lista.map((c) => c.id)]),
      ),
      {
        Junior: ["C-1"],
        "Semi-Senior": [],
        Senior: ["C-2", "C-3"],
        Lead: [],
        Executive: [],
      },
    );
  });

  it("con una colección vacía devuelve los cinco niveles vacíos", () => {
    assert.deepEqual(groupCandidatesBySeniority([]), {
      Junior: [],
      "Semi-Senior": [],
      Senior: [],
      Lead: [],
      Executive: [],
    });
  });
});

describe("countCandidatesByStatus", () => {
  it("cuenta cada estado e incluye los que están a cero", () => {
    assert.deepEqual(
      countCandidatesByStatus([
        makeCandidate({ status: "Active" }),
        makeCandidate({ status: "Active" }),
        makeCandidate({ status: "Hired" }),
      ]),
      { Active: 2, "In process": 0, Hired: 1, Inactive: 0 },
    );
  });

  it("con una colección vacía devuelve los cuatro estados a cero", () => {
    assert.deepEqual(countCandidatesByStatus([]), {
      Active: 0,
      "In process": 0,
      Hired: 0,
      Inactive: 0,
    });
  });
});

describe("calculateAverageSalary", () => {
  it("promedia el salario esperado y redondea a 2 decimales", () => {
    assert.equal(
      calculateAverageSalary([
        makeCandidate({ expectedSalary: 1000 }),
        makeCandidate({ expectedSalary: 2000 }),
        makeCandidate({ expectedSalary: 3001 }),
      ]),
      2000.33,
    );
  });

  it("resuelve un único candidato", () => {
    assert.equal(calculateAverageSalary([makeCandidate({ expectedSalary: 5000 })]), 5000);
  });

  it("devuelve 0 con una colección vacía, no NaN", () => {
    assert.equal(calculateAverageSalary([]), 0);
  });
});

describe("summarizeExpectedSalaries", () => {
  it("calcula total, media, mínimo y máximo", () => {
    assert.deepEqual(
      summarizeExpectedSalaries([
        makeCandidate({ expectedSalary: 2000 }),
        makeCandidate({ expectedSalary: 1000 }),
        makeCandidate({ expectedSalary: 3001 }),
      ]),
      { total: 6001, average: 2000.33, min: 1000, max: 3001 },
    );
  });

  it("no depende del orden de entrada", () => {
    const desordenados = [5000, 1000, 9000].map((s) => makeCandidate({ expectedSalary: s }));
    const ordenados = [1000, 5000, 9000].map((s) => makeCandidate({ expectedSalary: s }));
    assert.deepEqual(summarizeExpectedSalaries(desordenados), summarizeExpectedSalaries(ordenados));
  });

  it("con un único candidato, el mínimo y el máximo son el mismo", () => {
    assert.deepEqual(summarizeExpectedSalaries([makeCandidate({ expectedSalary: 4200 })]), {
      total: 4200,
      average: 4200,
      min: 4200,
      max: 4200,
    });
  });

  it("devuelve null con una colección vacía, no ceros", () => {
    assert.equal(summarizeExpectedSalaries([]), null);
  });
});

describe("findTopSkills", () => {
  const candidates = [
    makeCandidate({ skills: ["TypeScript", "React"] }),
    makeCandidate({ skills: ["typescript", "Node.js"] }),
    makeCandidate({ skills: ["TypeScript", "React", "Node.js"] }),
    makeCandidate({ skills: ["Docker"] }),
  ];

  it("ordena por frecuencia y desempata alfabéticamente", () => {
    assert.deepEqual(findTopSkills(candidates, 3), [
      { skill: "TypeScript", count: 3 },
      { skill: "Node.js", count: 2 },
      { skill: "React", count: 2 },
    ]);
  });

  it("agrupa sin distinguir mayúsculas y reporta la primera grafía vista", () => {
    const soloMinusculas = [makeCandidate({ skills: ["typescript"] }), makeCandidate({ skills: ["TypeScript"] })];
    assert.deepEqual(findTopSkills(soloMinusculas, 1), [{ skill: "typescript", count: 2 }]);
  });

  it("cuenta candidatos, no repeticiones dentro de una misma ficha", () => {
    const repetida = [makeCandidate({ skills: ["React", "react", "REACT"] })];
    assert.deepEqual(findTopSkills(repetida, 5), [{ skill: "React", count: 1 }]);
  });

  it("devuelve todas si topN supera el número de habilidades", () => {
    assert.equal(findTopSkills(candidates, 99).length, 4);
  });

  it("devuelve vacío con topN menor o igual que 0", () => {
    assert.deepEqual(findTopSkills(candidates, 0), []);
    assert.deepEqual(findTopSkills(candidates, -3), []);
  });

  it("devuelve vacío con una colección vacía", () => {
    assert.deepEqual(findTopSkills([], 5), []);
  });
});

describe("calculateVacancyFillRate", () => {
  it("calcula el porcentaje de procesos contratados, a 2 decimales", () => {
    const processes = [
      makeProcess({ stage: "Hired" }),
      makeProcess({ stage: "Hired" }),
      makeProcess({ stage: "Hired" }),
      makeProcess({ stage: "Rejected" }),
      makeProcess({ stage: "Offer" }),
      makeProcess({ stage: "Screening" }),
      makeProcess({ stage: "Interview" }),
    ];
    assert.equal(calculateVacancyFillRate(processes), 42.86);
  });

  it("devuelve 0 si ninguno terminó en contratación", () => {
    assert.equal(
      calculateVacancyFillRate([makeProcess({ stage: "Rejected" }), makeProcess({ stage: "Offer" })]),
      0,
    );
  });

  it("devuelve 100 si todos terminaron en contratación", () => {
    assert.equal(
      calculateVacancyFillRate([makeProcess({ stage: "Hired" }), makeProcess({ stage: "Hired" })]),
      100,
    );
  });

  it("devuelve 0 sin procesos, no NaN", () => {
    assert.equal(calculateVacancyFillRate([]), 0);
  });
});
