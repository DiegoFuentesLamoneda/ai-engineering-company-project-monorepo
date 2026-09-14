---
description: Convenciones de la web pública — CSS generado por el CLI de Tailwind, sin dependencias en el navegador y con el presupuesto de rendimiento y accesibilidad intacto.
globs: ["uis/website/**"]
alwaysApply: false
---

# Web pública de Nexova

**Ámbito: por patrón de archivo.** Se carga al tocar cualquier archivo bajo `uis/website/**`.

HTML5, Tailwind 4 compilado con el CLI y JavaScript sin dependencias. Sin framework, a propósito.

## Lo primero: esto es producción

Todo cambio que llega a `main` bajo `uis/website/**` **se despliega solo** a GitHub Pages mediante [`deploy-website.yml`](../../.github/workflows/deploy-website.yml). No hay entorno de pruebas intermedio. Es la cara pública de la empresa.

## 1. `styles.css` es generado — no se edita a mano

Se edita [`src/input.css`](../../uis/website/src/input.css) y se recompila:

```bash
npm run build:css     # una vez
npm run watch:css     # mientras se desarrolla
```

`styles.css` **se versiona** a propósito: el sitio es estático y debe funcionar al clonarlo, sin pasos de build. Cuando se toca `src/input.css`, el `styles.css` recompilado entra **en el mismo commit**, o el HTML publicado queda desfasado respecto a sus estilos.

Los colores de marca son tokens en `src/input.css`, que es la forma que tiene Tailwind 4 de configurar el tema. Nada de valores sueltos como `bg-[#0a1c33]`.

## 2. Nunca el CDN de Tailwind

El Play CDN descarga ~120 KB de compilador y genera el CSS **en el navegador** durante la carga: dispara el Total Blocking Time y provoca un parpadeo sin estilos. Compilado con el CLI son 19 KB de CSS y cero JavaScript de Tailwind.

Esta decisión es la que sostiene el 100 de Lighthouse. Ya está discutida; no se revierte por comodidad.

## 3. El presupuesto de rendimiento no se toca

Estado actual, medido con Lighthouse 12 en `index.html` y `application.html`:

| Categoría | Valor |
| --- | --- |
| Rendimiento | 100 |
| Accesibilidad | 100 |
| Buenas prácticas | 100 |
| SEO | 100 |

Mínimo exigido: **90 en las cuatro**. En la práctica, eso significa:

- **Cero dependencias de terceros en el navegador.** Ni fuentes remotas, ni analytics, ni librerías por CDN. Todo se sirve desde el propio dominio.
- Las imágenes son **SVG propios** en `assets/`. Un JPG sin optimizar se lleva por delante el LCP.
- Nada de JavaScript bloqueante. La validación del formulario es JS plano, sin dependencias.

## 4. HTML semántico y accesible

`header`, `nav`, `main`, `section`, `footer`, con un solo `h1` por página y jerarquía de encabezados sin saltos. Todo `img` con `alt` descriptivo (o `alt=""` si es decorativa), todo `input` con su `<label>`, contraste suficiente y foco visible.

## 5. SEO

Cada página lleva `title` y `meta description` propios, Open Graph y marcado `schema.org`. Al **añadir una página** hay que actualizar [`sitemap.xml`](../../uis/website/sitemap.xml) en el mismo commit, y revisar [`robots.txt`](../../uis/website/robots.txt) si cambia lo que debe indexarse.

## 6. Los textos son los de `CONTEXT.md`

Servicios, líneas de negocio, sedes y cifras salen del briefing. No se escribe *copy* inventado sobre lo que Nexova hace.

## Cómo se verifica

```bash
npm run build:css     # el CSS queda regenerado
npm run dev           # http-server en :3000
```

Y en el navegador:

- Las páginas cargan con estilos, sin parpadeo.
- El formulario valida sus once campos.
- Lighthouse sigue en 90 o más en las cuatro categorías.

> El aviso *"Page prevented back/forward cache restoration"* solo aparece en local: lo causa la cabecera `no-store` que envía `http-server` con `-c-1`. No puntúa y no se da en producción.
