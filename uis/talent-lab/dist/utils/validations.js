/**
 * Validaciones de negocio.
 *
 * Nada entra al motor de scoring sin pasar por aquí: una vacante con el rango
 * salarial invertido o un candidato sin habilidades producirían puntuaciones
 * sin sentido en lugar de un error visible.
 *
 * Las reglas son las del contexto del hito, ni una más. Los mensajes van en
 * español —los leen los consultores— y citan el campo con su nombre real en
 * inglés, para que buscarlo en el código sea inmediato.
 */
/** Experiencia mínima admitida, en años. */
export const MIN_YEARS_OF_EXPERIENCE = 0;
/** Experiencia máxima admitida, en años. */
export const MAX_YEARS_OF_EXPERIENCE = 50;
/**
 * Comprueba si un texto es un email plausible.
 *
 * Validación deliberadamente básica, como pide el contexto: exige `@` y un
 * punto en posiciones coherentes, no cubre el RFC 5322. La verificación real
 * de que un email existe es enviarle un correo.
 */
export function isValidEmail(email) {
    const trimmed = email.trim();
    // Un solo `@`, y ni al principio ni al final.
    const atIndex = trimmed.indexOf("@");
    if (atIndex <= 0 || atIndex !== trimmed.lastIndexOf("@"))
        return false;
    if (atIndex === trimmed.length - 1)
        return false;
    // Los espacios descartan la dirección antes de mirar el dominio.
    if (/\s/.test(trimmed))
        return false;
    // El dominio necesita un punto que separe dos partes no vacías.
    const domain = trimmed.slice(atIndex + 1);
    const dotIndex = domain.indexOf(".");
    return dotIndex > 0 && dotIndex < domain.length - 1;
}
/**
 * Valida un candidato contra las reglas de negocio de Nexova.
 *
 * Recorre todas las reglas en lugar de parar en el primer fallo: el consultor
 * necesita ver de una vez todo lo que le falta a la ficha.
 */
export function validateCandidate(candidate) {
    const errors = [];
    if (!Number.isFinite(candidate.yearsOfExperience) ||
        candidate.yearsOfExperience < MIN_YEARS_OF_EXPERIENCE ||
        candidate.yearsOfExperience > MAX_YEARS_OF_EXPERIENCE) {
        errors.push(`yearsOfExperience debe estar entre ${MIN_YEARS_OF_EXPERIENCE} y ${MAX_YEARS_OF_EXPERIENCE}`);
    }
    if (!Number.isFinite(candidate.currentSalary) || candidate.currentSalary <= 0) {
        errors.push("currentSalary debe ser mayor que 0");
    }
    if (!Number.isFinite(candidate.expectedSalary) || candidate.expectedSalary <= 0) {
        errors.push("expectedSalary debe ser mayor que 0");
    }
    if (candidate.skills.length === 0) {
        errors.push("skills debe contener al menos 1 habilidad");
    }
    if (!isValidEmail(candidate.email)) {
        errors.push("email no tiene un formato válido (ejemplo: nombre@empresa.com)");
    }
    if (candidate.phone.trim() === "") {
        errors.push("phone no puede estar vacío");
    }
    return { valid: errors.length === 0, errors };
}
/**
 * Valida una vacante contra las reglas de negocio de Nexova.
 *
 * Igual que con los candidatos, acumula todos los errores antes de responder.
 */
export function validateVacancy(vacancy) {
    const errors = [];
    if (vacancy.requiredSkills.length === 0) {
        errors.push("requiredSkills debe contener al menos 1 habilidad");
    }
    if (!Number.isFinite(vacancy.minYearsExperience) ||
        vacancy.minYearsExperience < MIN_YEARS_OF_EXPERIENCE) {
        errors.push(`minYearsExperience debe ser mayor o igual que ${MIN_YEARS_OF_EXPERIENCE}`);
    }
    if (!Number.isFinite(vacancy.maxYearsExperience) ||
        vacancy.maxYearsExperience < vacancy.minYearsExperience) {
        errors.push("maxYearsExperience debe ser mayor o igual que minYearsExperience");
    }
    if (!Number.isFinite(vacancy.salaryRangeMin) || vacancy.salaryRangeMin <= 0) {
        errors.push("salaryRangeMin debe ser mayor que 0");
    }
    if (!Number.isFinite(vacancy.salaryRangeMax) || vacancy.salaryRangeMax <= 0) {
        errors.push("salaryRangeMax debe ser mayor que 0");
    }
    if (Number.isFinite(vacancy.salaryRangeMin) &&
        Number.isFinite(vacancy.salaryRangeMax) &&
        vacancy.salaryRangeMax < vacancy.salaryRangeMin) {
        errors.push("salaryRangeMax debe ser mayor o igual que salaryRangeMin");
    }
    return { valid: errors.length === 0, errors };
}
