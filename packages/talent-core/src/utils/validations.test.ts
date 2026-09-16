import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { sampleCandidates, sampleVacancies } from "../data/samples.js";
import { makeCandidate, makeVacancy } from "../testing/factories.js";
import { isValidEmail, validateCandidate, validateVacancy } from "./validations.js";

/** Comprueba que la validación falla y que el error señala el campo esperado. */
function assertFallaPor(
  result: { valid: boolean; errors: string[] },
  campo: string,
): void {
  assert.equal(result.valid, false);
  assert.ok(
    result.errors.some((error) => error.startsWith(campo)),
    `esperaba un error sobre ${campo}, llegaron: ${JSON.stringify(result.errors)}`,
  );
}

describe("isValidEmail", () => {
  it("acepta direcciones bien formadas", () => {
    for (const email of [
      "a@b.co",
      "maria.gonzalez@email.com",
      "user+tag@sub.domain.com",
      "  maria@email.com  ",
    ]) {
      assert.equal(isValidEmail(email), true, email);
    }
  });

  it("rechaza direcciones sin arroba, sin dominio o mal puntuadas", () => {
    for (const email of [
      "",
      "sinarroba.com",
      "@email.com",
      "user@",
      "user@nodot",
      "user@.com",
      "user@dominio.",
      "dos@@email.com",
      "con espacio@email.com",
    ]) {
      assert.equal(isValidEmail(email), false, email);
    }
  });
});

describe("validateCandidate", () => {
  it("acepta un candidato correcto", () => {
    assert.deepEqual(validateCandidate(makeCandidate()), { valid: true, errors: [] });
  });

  it("admite los extremos del rango de experiencia", () => {
    assert.equal(validateCandidate(makeCandidate({ yearsOfExperience: 0 })).valid, true);
    assert.equal(validateCandidate(makeCandidate({ yearsOfExperience: 50 })).valid, true);
  });

  it("rechaza experiencia negativa o superior a 50", () => {
    assertFallaPor(validateCandidate(makeCandidate({ yearsOfExperience: -1 })), "yearsOfExperience");
    assertFallaPor(validateCandidate(makeCandidate({ yearsOfExperience: 51 })), "yearsOfExperience");
  });

  it("rechaza salarios que no sean positivos", () => {
    assertFallaPor(validateCandidate(makeCandidate({ currentSalary: 0 })), "currentSalary");
    assertFallaPor(validateCandidate(makeCandidate({ expectedSalary: -100 })), "expectedSalary");
  });

  it("rechaza un candidato sin habilidades", () => {
    assertFallaPor(validateCandidate(makeCandidate({ skills: [] })), "skills");
  });

  it("rechaza un email mal formado", () => {
    assertFallaPor(validateCandidate(makeCandidate({ email: "maria.gonzalez" })), "email");
  });

  it("rechaza un teléfono vacío o en blanco", () => {
    assertFallaPor(validateCandidate(makeCandidate({ phone: "" })), "phone");
    assertFallaPor(validateCandidate(makeCandidate({ phone: "   " })), "phone");
  });

  it("acumula todos los errores en lugar de parar en el primero", () => {
    const roto = makeCandidate({
      yearsOfExperience: -5,
      currentSalary: 0,
      expectedSalary: 0,
      skills: [],
      email: "roto",
      phone: "",
    });
    assert.equal(validateCandidate(roto).errors.length, 6);
  });
});

describe("validateVacancy", () => {
  it("acepta una vacante correcta", () => {
    assert.deepEqual(validateVacancy(makeVacancy()), { valid: true, errors: [] });
  });

  it("rechaza una vacante sin habilidades requeridas", () => {
    assertFallaPor(validateVacancy(makeVacancy({ requiredSkills: [] })), "requiredSkills");
  });

  it("rechaza experiencia mínima negativa", () => {
    assertFallaPor(validateVacancy(makeVacancy({ minYearsExperience: -1 })), "minYearsExperience");
  });

  it("rechaza un rango de experiencia invertido", () => {
    assertFallaPor(
      validateVacancy(makeVacancy({ minYearsExperience: 8, maxYearsExperience: 4 })),
      "maxYearsExperience",
    );
  });

  it("admite un rango de experiencia de un solo valor", () => {
    assert.equal(
      validateVacancy(makeVacancy({ minYearsExperience: 5, maxYearsExperience: 5 })).valid,
      true,
    );
  });

  it("rechaza salarios que no sean positivos", () => {
    assertFallaPor(validateVacancy(makeVacancy({ salaryRangeMin: 0 })), "salaryRangeMin");
    assertFallaPor(validateVacancy(makeVacancy({ salaryRangeMax: -1 })), "salaryRangeMax");
  });

  it("rechaza un rango salarial invertido", () => {
    assertFallaPor(
      validateVacancy(makeVacancy({ salaryRangeMin: 7000, salaryRangeMax: 5000 })),
      "salaryRangeMax",
    );
  });

  it("acumula todos los errores en lugar de parar en el primero", () => {
    const rota = makeVacancy({
      requiredSkills: [],
      minYearsExperience: -1,
      maxYearsExperience: -5,
      salaryRangeMin: 0,
      salaryRangeMax: 0,
    });
    assert.equal(validateVacancy(rota).errors.length, 5);
  });
});

describe("datos de ejemplo", () => {
  it("conserva sin tocar los tres candidatos del enunciado", () => {
    assert.deepEqual(
      sampleCandidates.slice(0, 3).map((c) => [c.id, c.fullName, c.expectedSalary]),
      [
        ["C-2024-0451", "María González", 4200],
        ["C-2024-0452", "Juan Pérez", 2800],
        ["C-2024-0453", "Carolina Silva", 6500],
      ],
    );
  });

  it("conserva sin tocar la vacante del enunciado", () => {
    assert.deepEqual(sampleVacancies[0]?.id, "V-2024-0892");
    assert.deepEqual(sampleVacancies[0]?.requiredSkills, ["TypeScript", "React", "Node.js"]);
  });

  it("todos los candidatos de ejemplo pasan la validación", () => {
    for (const candidate of sampleCandidates) {
      assert.deepEqual(validateCandidate(candidate), { valid: true, errors: [] }, candidate.id);
    }
  });

  it("todas las vacantes de ejemplo pasan la validación", () => {
    for (const vacancy of sampleVacancies) {
      assert.deepEqual(validateVacancy(vacancy), { valid: true, errors: [] }, vacancy.id);
    }
  });
});
