import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { makeCandidate } from "../testing/factories.js";
import {
  binarySearchCandidateBySalary,
  findCandidateByEmail,
  findCandidateById,
} from "./search.js";

const candidates = [
  makeCandidate({ id: "C-1", email: "ana.lopez@email.com", expectedSalary: 6000 }),
  makeCandidate({ id: "C-2", email: "Beto.Ruiz@Email.com", expectedSalary: 2500 }),
  makeCandidate({ id: "C-3", email: "clara.diaz@email.com", expectedSalary: 4000 }),
];

/** Los mismos candidatos ordenados por salario esperado ascendente: 2500, 4000, 6000. */
const bySalary = [candidates[1]!, candidates[2]!, candidates[0]!];

describe("findCandidateById", () => {
  it("encuentra al candidato en una colección desordenada", () => {
    assert.equal(findCandidateById(candidates, "C-3")?.id, "C-3");
  });

  it("devuelve null si el id no existe", () => {
    assert.equal(findCandidateById(candidates, "C-99"), null);
  });

  it("distingue mayúsculas en el id", () => {
    assert.equal(findCandidateById(candidates, "c-1"), null);
  });

  it("devuelve null con una colección vacía", () => {
    assert.equal(findCandidateById([], "C-1"), null);
  });
});

describe("findCandidateByEmail", () => {
  it("encuentra al candidato por email exacto", () => {
    assert.equal(findCandidateByEmail(candidates, "ana.lopez@email.com")?.id, "C-1");
  });

  it("compara el email sin distinguir mayúsculas", () => {
    assert.equal(findCandidateByEmail(candidates, "beto.ruiz@email.com")?.id, "C-2");
    assert.equal(findCandidateByEmail(candidates, "CLARA.DIAZ@EMAIL.COM")?.id, "C-3");
  });

  it("devuelve null si el email no existe", () => {
    assert.equal(findCandidateByEmail(candidates, "nadie@email.com"), null);
  });

  it("devuelve null con una colección vacía", () => {
    assert.equal(findCandidateByEmail([], "ana.lopez@email.com"), null);
  });
});

describe("binarySearchCandidateBySalary", () => {
  it("encuentra el primer elemento", () => {
    assert.equal(binarySearchCandidateBySalary(bySalary, 2500), 0);
  });

  it("encuentra el elemento central", () => {
    assert.equal(binarySearchCandidateBySalary(bySalary, 4000), 1);
  });

  it("encuentra el último elemento", () => {
    assert.equal(binarySearchCandidateBySalary(bySalary, 6000), 2);
  });

  it("devuelve -1 si el salario está entre dos valores existentes", () => {
    assert.equal(binarySearchCandidateBySalary(bySalary, 3000), -1);
  });

  it("devuelve -1 si el salario queda fuera del rango por abajo y por arriba", () => {
    assert.equal(binarySearchCandidateBySalary(bySalary, 100), -1);
    assert.equal(binarySearchCandidateBySalary(bySalary, 99_000), -1);
  });

  it("devuelve -1 con una colección vacía", () => {
    assert.equal(binarySearchCandidateBySalary([], 4000), -1);
  });

  it("resuelve una colección de un solo elemento", () => {
    const uno = [makeCandidate({ expectedSalary: 4000 })];
    assert.equal(binarySearchCandidateBySalary(uno, 4000), 0);
    assert.equal(binarySearchCandidateBySalary(uno, 3999), -1);
  });

  it("con salarios repetidos devuelve un índice válido cualquiera", () => {
    const conEmpates = [
      makeCandidate({ id: "C-1", expectedSalary: 2000 }),
      makeCandidate({ id: "C-2", expectedSalary: 5000 }),
      makeCandidate({ id: "C-3", expectedSalary: 5000 }),
      makeCandidate({ id: "C-4", expectedSalary: 5000 }),
      makeCandidate({ id: "C-5", expectedSalary: 9000 }),
    ];
    const index = binarySearchCandidateBySalary(conEmpates, 5000);
    assert.ok(index >= 0, "debería encontrar alguno de los tres");
    assert.equal(conEmpates[index]?.expectedSalary, 5000);
  });

  it("funciona sobre una colección larga", () => {
    // 0, 100, 200 … 9900: comprueba que de verdad se descarta media colección
    // en cada paso y no se está recorriendo el array entero.
    const muchos = Array.from({ length: 100 }, (_, i) =>
      makeCandidate({ id: `C-${i}`, expectedSalary: i * 100 }),
    );
    assert.equal(binarySearchCandidateBySalary(muchos, 0), 0);
    assert.equal(binarySearchCandidateBySalary(muchos, 4200), 42);
    assert.equal(binarySearchCandidateBySalary(muchos, 9900), 99);
    assert.equal(binarySearchCandidateBySalary(muchos, 4250), -1);
  });

  it("no modifica la colección recibida", () => {
    const original = bySalary.map((c) => c.id);
    binarySearchCandidateBySalary(bySalary, 4000);
    assert.deepEqual(
      bySalary.map((c) => c.id),
      original,
    );
  });
});
