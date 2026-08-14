# Sitio web público de Nexova Solutions

Entregable del **hito 1 — Sitio Web Público**. Landing corporativa y formulario de registro de talento, en HTML, Tailwind CSS y JavaScript sin dependencias.

Especificación de referencia: [`CONTEXT.md`](../../CONTEXT.md) (apéndice del hito) y su original en [`docs/contexts/01-web-fundamentals.es.md`](../../docs/contexts/01-web-fundamentals.es.md).

## Ejecutar

Un solo comando desde la **raíz del repositorio**, sin instalar nada:

```bash
npx http-server uis/website -p 3000 -a 0.0.0.0
```

Y se abre en <http://localhost:3000>. En Codespaces, expón el puerto 3000 como **Public** en la pestaña *Ports* para obtener la URL pública.

Equivalente desde esta carpeta: `npm run dev`.

## Archivos

| Archivo                                | Contenido                                                    |
| -------------------------------------- | ------------------------------------------------------------ |
| [`index.html`](./index.html)           | Landing: header, hero, servicios, por qué Nexova, contacto y footer |
| [`application.html`](./application.html) | Formulario de registro de talento                            |
| [`validation.js`](./validation.js)     | Validación de los once campos                                 |
| [`styles.css`](./styles.css)           | **Generado por Tailwind — no editar a mano**                  |
| [`src/input.css`](./src/input.css)     | Entrada del compilador: tokens de marca                       |
| `assets/`                              | Logotipo, favicon e ilustración, todo SVG propio              |
| `robots.txt` · `sitemap.xml`           | Indexación                                                    |

## Tailwind compilado, no por CDN

El enunciado sugiere el CDN de Tailwind, pero el criterio de evaluación exige **PageSpeed ≥ 80, idealmente por encima de 90**. El Play CDN descarga ~120 KB de compilador y genera el CSS *en el navegador* durante la carga, lo que dispara el Total Blocking Time y provoca un parpadeo sin estilos.

Compilando con el CLI oficial el resultado son **19 KB de CSS** con solo las utilidades que se usan, y **cero JavaScript** de Tailwind:

```bash
npm install        # solo la primera vez
npm run build:css  # o npm run watch:css mientras se desarrolla
```

Sigue siendo *"solo Tailwind"*: `styles.css` lo produce la herramienta y no contiene ni una regla escrita a mano. Los colores de marca se declaran como tokens en `src/input.css`, que es la forma que tiene Tailwind 4 de configurar el tema.

`styles.css` se versiona a propósito: el sitio es estático y debe funcionar al clonarlo, sin pasos de build.

## Resultados medidos

Lighthouse 12, ambas páginas:

| Categoría        | `index.html` | `application.html` |
| ---------------- | ------------ | ------------------ |
| Rendimiento      | 100          | 100                |
| Accesibilidad    | 100          | 100                |
| Buenas prácticas | 100          | 100                |
| SEO              | 100          | 100                |

FCP 0,9 s · LCP 1,2 s · TBT 0 ms · CLS 0. Página completa: 44 KB.

> El diagnóstico *"Page prevented back/forward cache restoration"* aparece solo en local: lo causa la cabecera `no-store` que envía `http-server` con `-c-1` para desactivar la caché durante el desarrollo. No puntúa y no se da en producción.

Contraste de la paleta, con el mínimo AA en 4,5:1 — el par más justo es 6,47:1 (mensajes de error) y el resto va de 7,4:1 a 14,1:1.

## Accesibilidad

- Enlace de salto al contenido, landmarks (`header`, `nav`, `main`, `footer`, `address`) y un solo `h1` por página.
- Todas las `<img>` llevan `alt` descriptivo. Los iconos decorativos son SVG en línea con `aria-hidden="true"`, que es lo correcto: anunciarlos solo añadiría ruido.
- Menú móvil con `aria-expanded` y `aria-controls`; el panel usa `hidden`, de modo que sale del árbol de accesibilidad al cerrarse. Se cierra con `Escape` y devuelve el foco al botón.
- Cada campo tiene su `<label for>`; los grupos van en `fieldset` con `legend`. Los errores se enlazan con `aria-describedby` y marcan `aria-invalid`.
- El error nunca se comunica solo con color: siempre hay texto, y el resumen de envío fallido es un `role="alert"`.
- Foco visible en todo elemento interactivo, con `focus-visible` para no molestar al ratón.

## Decisiones de implementación

**Nombres de campo.** El enunciado da las etiquetas ("Nivel de inglés") pero no los atributos. Se fijan en `snake_case` y los valores en slug (`nivel_ingles` con `basico|intermedio|avanzado|nativo`) para que estos datos entren sin traducción en la API y el CRM de los hitos siguientes.

**El textarea no lleva `maxlength`.** Con él, el navegador impediría teclear el carácter 501 y la validación de longitud —y su mensaje de error, que el enunciado exige literalmente— nunca podrían dispararse. El límite se controla en `validation.js`, con un contador en vivo que se pone en rojo al superarlo.

**El formulario lleva `novalidate`, los campos conservan `required`.** Así no aparecen los bocadillos nativos, que no se pueden estilar ni traducir, pero el HTML sigue describiendo sus restricciones para los lectores de pantalla.

**Validación al salir del campo, no al teclear.** Se revalida mientras se escribe solo si el campo ya estaba marcado como erróneo, para no señalar en rojo algo que aún se está escribiendo.

**El botón de limpiar hace más que el `reset` nativo.** El reset vacía los valores pero deja intactos los mensajes de error, los `aria-invalid` y los bordes de color; un listener los retira.

**Mensaje de comentarios.** La plantilla del enunciado es `"...(quedan X)"`. Como el error solo salta al superar el límite, X vale siempre 0; el contador en vivo es el que indica cuántos caracteres sobran.

**Tipografía del sistema.** Sin fuentes web: cada petición externa cuesta puntos de rendimiento y el listón estaba en 90.

## Desviaciones respecto al enunciado

El documento del hito tiene incoherencias internas. Se corrigen para que el sitio sea coherente en 2026:

| Enunciado                                                  | En el sitio                                                   | Motivo                                                              |
| ---------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------- |
| «más de 10 años» (hero) y «12 años» (bullets)              | «más de 15 años» / «15 años»                                  | Fundada en 2011: en 2026 son 15. Las dos cifras del original ya discrepaban entre sí |
| «12 años de experiencia en el **mercado latinoamericano**» | «15 años de experiencia en selección y desarrollo de talento» | Nexova opera en España y EE. UU.; el bullet siguiente lo contradecía |
| «Presencia **regional**: España y Estados Unidos»          | «Presencia **internacional**»                                 | Son dos continentes, no una región                                   |
| «© **2025** Nexova»                                        | «© **2026** Nexova»                                           | Año en curso                                                         |

Se mantienen **literales** el titular del hero, las tres tarjetas de servicios, «+500 procesos exitosos», «Especialización sectorial», los datos de contacto, los once mensajes de error, el mensaje de éxito y el aviso para empresas.

Al JSON-LD de `Organization` que fija el enunciado se le añade `logo`, que el original omitía. Nada más.

## Pruebas

La validación tiene un banco de **45 pruebas automáticas** que comprueba los once mensajes carácter a carácter contra el enunciado, los límites (0, 50 y exactamente 500 caracteres), el foco al primer campo inválido, el envío correcto y el borrado de estados al limpiar.

No se versiona porque no forma parte del entregable. Para reconstruirlo, carga `application.html` en un `iframe`, rellena los campos y dispara los eventos: al ser mismo origen se puede leer el documento del `iframe` desde la página contenedora.

> Para revisar tamaños de pantalla, renderiza dentro de un `iframe` con el ancho deseado. Chrome headless en Windows impone un ancho mínimo de ventana: `--window-size=390` renderiza más ancho y recorta la captura, lo que simula un desbordamiento que no existe.
