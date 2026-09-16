---
description: Documentación, comentarios, interfaz y commits en español; código, carpetas y ramas en inglés. Cada carpeta lleva README.
alwaysApply: true
---

# Idioma y documentación

**Ámbito: siempre activa.** Aplica a todo el repositorio, en toda sesión.

## Qué va en cada idioma

| En español | En inglés |
| --- | --- |
| Documentación y READMEs | Nombres de variables, funciones y tipos |
| Comentarios del código | Nombres de carpetas y archivos |
| Textos visibles en la interfaz | Nombres de rama (`feature/agent-memory-bank`) |
| Mensajes de commit y descripciones de PR | Claves de configuración que leen las herramientas |

```ts
// Devuelve la etiqueta visible de una etapa del proceso de selección.
export function stageLabel(stage: Stage): string {
  return STAGE_LABELS[stage];
}
```

Función y tipo en inglés; comentario y valor devuelto, en español. Es la mezcla correcta, no una inconsistencia: el código lo lee quien programa, la interfaz la lee Elena.

## Cada carpeta lleva README

Toda aplicación, servicio o paquete nuevo va en su subcarpeta **con su propio `README.md`**: qué es, qué hito lo pide, cómo se ejecuta y qué decisiones se tomaron. Las carpetas de primer nivel ya traen el suyo de la plantilla, y se lee antes de escribir código ahí.

**No se dejan archivos de implementación en la raíz del repositorio.**

## Cómo se escribe la documentación aquí

El repositorio ya tiene un estilo y se mantiene:

- **Tablas para lo que se consulta, prosa para lo que se razona.** Una lista de comandos es una tabla; el motivo de una decisión es un párrafo.
- **Se explica el porqué, no solo el qué.** El qué está en el código. Un README que repite la estructura de carpetas no aporta; uno que explica por qué Tailwind se compila con el CLI y no por CDN evita que alguien lo revierta dentro de tres meses.
- **Enlaces relativos siempre**, para que funcionen en GitHub y en el editor.
- **Sin adornos.** Nada de "¡Bienvenido a nuestro increíble proyecto!". Se va al grano.
- Los datos medidos se escriben con su cifra (112 pruebas, 19 KB de CSS, Lighthouse 100), no como "muchas" o "muy rápido".

## Cómo se verifica

- Todo texto nuevo visible en la interfaz está en español y usa el vocabulario de [`memory-bank/projectbrief.md`](../../memory-bank/projectbrief.md).
- Todo identificador nuevo del código está en inglés.
- Toda carpeta nueva tiene `README.md`.
- La raíz del repositorio no ha ganado ningún archivo de implementación.
