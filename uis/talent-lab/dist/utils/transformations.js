/**
 * Scoring, matching, agrupaciones y reportes.
 *
 * Es el corazón del hito: lo que hoy hacen a ojo los 40 consultores de
 * selección. Todo se calcula a partir de los parámetros recibidos — sin estado
 * global, sin fechas del sistema — para que dos ejecuciones con los mismos
 * datos den siempre el mismo resultado.
 */
import { ENGLISH_LEVELS, SENIORITY_LEVELS } from "../types/models.js";
import { normalizeSkill } from "./collections.js";
/**
 * Puntúa el encaje de un candidato con una vacante, de 0 a 100.
 *
 * Cinco bloques que suman exactamente 100. Usa `ENGLISH_LEVELS` y
 * `SENIORITY_LEVELS` de `types/models.ts` como escala: el índice en esas
 * constantes es lo que permite comparar niveles.
 *
 * **Habilidades — 40 puntos máx.**
 * - Requeridas: 40 si las tiene todas; 20 si tiene al menos el 50 %; 0 si
 *   tiene menos. Los tramos **no** se acumulan, se aplica el que corresponda.
 *   Si la vacante no exige ninguna habilidad, el tramo vale 40.
 * - Preferidas: 10 por cada una que tenga, hasta 20.
 * - El bloque se capa: `min(40, requeridas + preferidas)`. Sin ese tope el
 *   máximo global sería 120 sobre 100 — ver la nota del README.
 * - El matching es case-insensitive: usa `normalizeSkill` de `collections.ts`.
 *
 * **Experiencia — 20 puntos máx.** Distancia en años al extremo más cercano
 * del rango `[minYearsExperience, maxYearsExperience]`: 20 si está dentro
 * (distancia 0), 10 si se sale 1 o 2 años, 0 si se sale más.
 *
 * **Seniority — 15 puntos máx.** 15 si coincide con `requiredSeniority`, 7 si
 * está un nivel por encima o por debajo, 0 en otro caso.
 *
 * **Inglés — 15 puntos máx.** 15 si iguala o supera `requiredEnglishLevel`,
 * 0 si no llega.
 *
 * **Salario — 10 puntos máx.** 10 si `expectedSalary` no pasa de
 * `salaryRangeMax` —pedir menos del mínimo no penaliza, ver README—, 5 si lo
 * pasa hasta en un 20 %, 0 si lo pasa más.
 *
 * @param candidate Candidato a evaluar.
 * @param vacancy Vacante contra la que se evalúa.
 * @returns Puntuación entera entre 0 y 100 (`Math.round` del total).
 */
export function calculateCandidateScore(candidate, vacancy) {
    const total = scoreSkills(candidate, vacancy) +
        scoreExperience(candidate, vacancy) +
        scoreSeniority(candidate, vacancy) +
        scoreEnglish(candidate, vacancy) +
        scoreSalary(candidate, vacancy);
    return Math.round(total);
}
// --- Los cinco bloques del scoring -----------------------------------------
//
// Uno por criterio, para poder razonar cada regla por separado. No se exportan:
// solo tienen sentido como partes de `calculateCandidateScore`.
/** Habilidades — 40 puntos máx. */
function scoreSkills(candidate, vacancy) {
    const owned = new Set(candidate.skills.map(normalizeSkill));
    const required = vacancy.requiredSkills.map(normalizeSkill);
    const matchedRequired = required.filter((skill) => owned.has(skill)).length;
    let requiredPoints;
    if (matchedRequired === required.length) {
        // Cubre también la vacante que no exige ninguna habilidad.
        requiredPoints = 40;
    }
    else if (matchedRequired / required.length >= 0.5) {
        requiredPoints = 20;
    }
    else {
        requiredPoints = 0;
    }
    const matchedPreferred = vacancy.preferredSkills
        .map(normalizeSkill)
        .filter((skill) => owned.has(skill)).length;
    const preferredPoints = Math.min(20, matchedPreferred * 10);
    return Math.min(40, requiredPoints + preferredPoints);
}
/** Experiencia — 20 puntos máx. */
function scoreExperience(candidate, vacancy) {
    // Años que se sale del rango por el extremo más cercano. Dentro del rango
    // ambas restas son negativas, así que el 0 gana y la distancia es 0.
    const distance = Math.max(vacancy.minYearsExperience - candidate.yearsOfExperience, candidate.yearsOfExperience - vacancy.maxYearsExperience, 0);
    if (distance === 0)
        return 20;
    if (distance <= 2)
        return 10;
    return 0;
}
/** Seniority — 15 puntos máx. */
function scoreSeniority(candidate, vacancy) {
    const distance = Math.abs(SENIORITY_LEVELS.indexOf(candidate.seniority) -
        SENIORITY_LEVELS.indexOf(vacancy.requiredSeniority));
    if (distance === 0)
        return 15;
    if (distance === 1)
        return 7;
    return 0;
}
/** Nivel de inglés — 15 puntos máx. */
function scoreEnglish(candidate, vacancy) {
    const candidateLevel = ENGLISH_LEVELS.indexOf(candidate.englishLevel);
    const requiredLevel = ENGLISH_LEVELS.indexOf(vacancy.requiredEnglishLevel);
    return candidateLevel >= requiredLevel ? 15 : 0;
}
/** Salario — 10 puntos máx. */
function scoreSalary(candidate, vacancy) {
    // Solo se mira el techo: pedir menos del mínimo no penaliza.
    if (candidate.expectedSalary <= vacancy.salaryRangeMax)
        return 10;
    if (candidate.expectedSalary <= vacancy.salaryRangeMax * 1.2)
        return 5;
    return 0;
}
/**
 * Puntúa a todos los candidatos contra una vacante y los ordena de mejor a peor.
 *
 * - Los empates conservan el orden en el que llegaron.
 * - No modifica `candidates`.
 *
 * @param candidates Candidatos a rankear.
 * @param vacancy Vacante de referencia.
 * @returns Array nuevo de `{ candidate, score }`, puntuación descendente.
 */
export function rankCandidatesForVacancy(candidates, vacancy) {
    // `.map` ya devuelve un array nuevo, así que ordenarlo no toca el original.
    // Y `.sort` es estable, de modo que los empates conservan el orden de entrada.
    return candidates
        .map((candidate) => ({
        candidate,
        score: calculateCandidateScore(candidate, vacancy),
    }))
        .sort((a, b) => b.score - a.score);
}
/**
 * Agrupa candidatos por nivel de seniority.
 *
 * El `Record` es **total**: las cinco claves de `SENIORITY_LEVELS` aparecen
 * siempre, con array vacío las que no tengan a nadie. Así quien consume el
 * reporte nunca se encuentra un `undefined`.
 *
 * @param candidates Candidatos a agrupar.
 * @returns Un objeto con los cinco niveles como claves.
 */
export function groupCandidatesBySeniority(candidates) {
    const grouped = {
        Junior: [],
        "Semi-Senior": [],
        Senior: [],
        Lead: [],
        Executive: [],
    };
    for (const candidate of candidates) {
        grouped[candidate.seniority].push(candidate);
    }
    return grouped;
}
/**
 * Cuenta cuántos candidatos hay en cada estado.
 *
 * Igual que la agrupación: los cuatro estados de `CANDIDATE_STATUSES` salen
 * siempre, a 0 los que no tengan a nadie.
 *
 * @param candidates Candidatos a contar.
 * @returns Un objeto con los cuatro estados como claves.
 */
export function countCandidatesByStatus(candidates) {
    const statusCounts = {
        Active: 0,
        "In process": 0,
        Hired: 0,
        Inactive: 0,
    };
    for (const candidate of candidates) {
        statusCounts[candidate.status]++;
    }
    return statusCounts;
    throw new Error("Sin implementar: countCandidatesByStatus");
}
/**
 * Salario esperado medio del conjunto.
 *
 * @param candidates Candidatos a promediar.
 * @returns La media de `expectedSalary` redondeada a 2 decimales, o 0 si no
 *   hay candidatos — dividir entre cero daría `NaN` y contaminaría el reporte.
 */
export function calculateAverageSalary(candidates) {
    if (candidates.length === 0)
        return 0;
    const totalSalary = candidates.reduce((sum, candidate) => sum + candidate.expectedSalary, 0);
    return parseFloat((totalSalary / candidates.length).toFixed(2));
}
/**
 * Las habilidades más frecuentes en la base de talento.
 *
 * - `count` es **cuántos candidatos** declaran la habilidad, no cuántas veces
 *   aparece: si alguien la repite en su ficha, sigue sumando 1.
 * - Las habilidades se agrupan con `normalizeSkill`, de modo que "TypeScript"
 *   y "typescript" son la misma. Se reporta la primera grafía encontrada.
 * - Orden: frecuencia descendente; a igual frecuencia, alfabético por la
 *   habilidad normalizada, para que el resultado sea siempre el mismo.
 * - Con `topN` menor o igual que 0, devuelve un array vacío.
 *
 * @param candidates Candidatos de los que extraer habilidades.
 * @param topN Cuántas habilidades devolver como máximo.
 * @returns Array nuevo de `{ skill, count }`.
 */
export function findTopSkills(candidates, topN) {
    if (topN <= 0)
        return [];
    // Clave: la habilidad normalizada. Valor: la primera grafía vista y cuántos
    // candidatos la declaran.
    const tally = new Map();
    for (const candidate of candidates) {
        // Una ficha que repite la misma habilidad sigue sumando 1.
        const counted = new Set();
        for (const skill of candidate.skills) {
            const key = normalizeSkill(skill);
            if (counted.has(key))
                continue;
            counted.add(key);
            const entry = tally.get(key);
            if (entry === undefined) {
                tally.set(key, { skill, count: 1 });
            }
            else {
                entry.count += 1;
            }
        }
    }
    return [...tally]
        .sort(([keyA, a], [keyB, b]) => {
        if (a.count !== b.count)
            return b.count - a.count;
        // Desempate alfabético por la forma normalizada: sin él, dos ejecuciones
        // con los mismos datos podrían dar reportes distintos.
        return keyA < keyB ? -1 : keyA > keyB ? 1 : 0;
    })
        .slice(0, topN)
        .map(([, entry]) => entry);
}
/**
 * Porcentaje de procesos de selección que acabaron en contratación.
 *
 * @param processes Procesos a medir.
 * @returns Porcentaje de procesos en etapa `"Hired"` entre 0 y 100,
 *   redondeado a 2 decimales; 0 si no hay procesos.
 */
export function calculateVacancyFillRate(processes) {
    if (processes.length === 0)
        return 0;
    const hiredCount = processes.filter((p) => p.stage === "Hired").length;
    return parseFloat(((hiredCount / processes.length) * 100).toFixed(2));
}
