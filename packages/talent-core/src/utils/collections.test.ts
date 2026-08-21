import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { makeCandidate } from "../testing/factories.js";
import {
  filterCandidatesByAvailability,
  filterCandidatesBySeniority,
  filterCandidatesBySkills,
  normalizeSkill,
  sortCandidatesByExperience,
  sortCandidatesBySalary,
  sortCandidatesBySeniorityThenSalary,
} from "./collections.js";

const ana = makeCandidate({
  id: "C-1",
  skills: ["TypeScript", "React", "Node.js"],
  seniority: "Senior",
  availability: "Immediate",
  expectedSalary: 6000,
  yearsOfExperience: 8,
});

const beto = makeCandidate({
  id: "C-2",
  skills: ["typescript", "react"],
  seniority: "Junior",
  availability: "1 month",
  expectedSalary: 2500,
  yearsOfExperience: 2,
});

const clara = makeCandidate({
  id: "C-3",
  skills: ["Python", "Django"],
  seniority: "Senior",
  availability: "Not available",
  expectedSalary: 4000,
  yearsOfExperience: 5,
});

const candidates = [ana, beto, clara];

/** Los ids resultantes, que es lo que de verdad se quiere comprobar. */
const ids = (result: { id: string }[]): string[] => result.map((c) => c.id);

describe("normalizeSkill", () => {
  it("pasa a minúsculas y recorta los espacios", () => {
    assert.equal(normalizeSkill("  TypeScript "), "typescript");
  });
});

describe("filterCandidatesBySkills", () => {
  it("devuelve solo a quien tiene todas las habilidades requeridas", () => {
    assert.deepEqual(ids(filterCandidatesBySkills(candidates, ["TypeScript", "Node.js"])), ["C-1"]);
  });

  it("compara sin distinguir mayúsculas en ambos lados", () => {
    assert.deepEqual(ids(filterCandidatesBySkills(candidates, ["typescript", "REACT"])), ["C-1", "C-2"]);
  });

  it("sin habilidades requeridas no descarta a nadie", () => {
    assert.deepEqual(ids(filterCandidatesBySkills(candidates, [])), ["C-1", "C-2", "C-3"]);
  });

  it("devuelve vacío cuando nadie cumple", () => {
    assert.deepEqual(filterCandidatesBySkills(candidates, ["COBOL"]), []);
  });

  it("acepta una colección vacía", () => {
    assert.deepEqual(filterCandidatesBySkills([], ["TypeScript"]), []);
  });

  it("no modifica la colección recibida", () => {
    const original = [...candidates];
    filterCandidatesBySkills(candidates, ["TypeScript"]);
    assert.deepEqual(candidates, original);
  });
});

describe("filterCandidatesBySeniority", () => {
  it("devuelve los candidatos del nivel pedido", () => {
    assert.deepEqual(ids(filterCandidatesBySeniority(candidates, "Senior")), ["C-1", "C-3"]);
  });

  it("devuelve vacío si nadie tiene ese nivel", () => {
    assert.deepEqual(filterCandidatesBySeniority(candidates, "Executive"), []);
  });

  it("acepta una colección vacía", () => {
    assert.deepEqual(filterCandidatesBySeniority([], "Senior"), []);
  });
});

describe("filterCandidatesByAvailability", () => {
  it("acepta cualquiera de los estados indicados", () => {
    assert.deepEqual(ids(filterCandidatesByAvailability(candidates, ["Immediate", "1 month"])), ["C-1", "C-2"]);
  });

  it("filtra por un único estado", () => {
    assert.deepEqual(ids(filterCandidatesByAvailability(candidates, ["Not available"])), ["C-3"]);
  });

  it("sin estados aceptables no devuelve a nadie", () => {
    assert.deepEqual(filterCandidatesByAvailability(candidates, []), []);
  });

  it("acepta una colección vacía", () => {
    assert.deepEqual(filterCandidatesByAvailability([], ["Immediate"]), []);
  });
});

describe("sortCandidatesBySalary", () => {
  it("ordena de menor a mayor salario esperado", () => {
    assert.deepEqual(ids(sortCandidatesBySalary(candidates, "asc")), ["C-2", "C-3", "C-1"]);
  });

  it("ordena de mayor a menor salario esperado", () => {
    assert.deepEqual(ids(sortCandidatesBySalary(candidates, "desc")), ["C-1", "C-3", "C-2"]);
  });

  it("no modifica la colección recibida", () => {
    const original = ids(candidates);
    sortCandidatesBySalary(candidates, "desc");
    assert.deepEqual(ids(candidates), original);
  });

  it("acepta una colección vacía", () => {
    assert.deepEqual(sortCandidatesBySalary([], "asc"), []);
  });
});

describe("sortCandidatesByExperience", () => {
  it("ordena de menor a mayor experiencia", () => {
    assert.deepEqual(ids(sortCandidatesByExperience(candidates, "asc")), ["C-2", "C-3", "C-1"]);
  });

  it("ordena de mayor a menor experiencia", () => {
    assert.deepEqual(ids(sortCandidatesByExperience(candidates, "desc")), ["C-1", "C-3", "C-2"]);
  });

  it("no modifica la colección recibida", () => {
    const original = ids(candidates);
    sortCandidatesByExperience(candidates, "asc");
    assert.deepEqual(ids(candidates), original);
  });

  it("acepta una colección vacía", () => {
    assert.deepEqual(sortCandidatesByExperience([], "desc"), []);
  });
});

describe("sortCandidatesBySeniorityThenSalary", () => {
  it("ordena por nivel y, dentro del nivel, por salario ascendente", () => {
    // Junior primero; luego los dos Senior, el que menos pide por delante.
    assert.deepEqual(ids(sortCandidatesBySeniorityThenSalary(candidates, "asc")), [
      "C-2",
      "C-3",
      "C-1",
    ]);
  });

  it("invierte los dos criterios en orden descendente", () => {
    assert.deepEqual(ids(sortCandidatesBySeniorityThenSalary(candidates, "desc")), [
      "C-1",
      "C-3",
      "C-2",
    ]);
  });

  it("desempata por salario solo dentro del mismo nivel", () => {
    // El Junior pide 2500, menos que los dos Senior, y aun así va detrás en
    // orden descendente: el nivel manda sobre el salario.
    const ordenados = sortCandidatesBySeniorityThenSalary(candidates, "desc");
    assert.equal(ordenados.at(-1)?.seniority, "Junior");
  });

  it("no modifica la colección recibida", () => {
    const original = ids(candidates);
    sortCandidatesBySeniorityThenSalary(candidates, "asc");
    assert.deepEqual(ids(candidates), original);
  });

  it("acepta una colección vacía", () => {
    assert.deepEqual(sortCandidatesBySeniorityThenSalary([], "asc"), []);
  });
});
