# Propuesta de arquitectura del backend — Nexova Solutions

| | |
| --- | --- |
| **Documento** | Propuesta de arquitectura · primer borrador para revisión |
| **Destinatario** | Sergio Molina (CTO) · equipo de Tecnología |
| **Autor** | Equipo de AI Engineering |
| **Fecha** | 16 de septiembre de 2026 |
| **Estado** | Borrador — abierto a discusión antes del inicio del sprint |
| **Ámbito** | El servicio backend de Nexova que vivirá en [`services/`](../services/) |

> Este documento no describe lo que hay construido, sino **lo que proponemos construir y por qué**. Las decisiones ya tomadas en hitos anteriores están en [`memory-bank/techContext.md`](../memory-bank/techContext.md); las que aquí se proponen se trasladarán allí una vez aprobadas.

---

## 0. Resumen de decisiones

Para quien solo tenga cinco minutos:

| # | Decisión | En una línea |
| --- | --- | --- |
| 1 | **Monolito modular por dominios** sobre FastAPI | Un solo servicio desplegable, dividido por dentro en dominios de negocio con fronteras explícitas |
| 2 | **Un servicio: `services/nexova-api/`** | Una carpeta por servicio, como manda la plantilla del monorepo; dentro, paquetes por dominio, no por tipo de archivo |
| 3 | **Tres capas por dominio**: `router` → `service` → `models` | El router habla HTTP, el service decide, los modelos persisten. La dependencia va en un solo sentido |
| 4 | **Un `APIRouter` por dominio**, con `prefix` y `tags` | `main.py` solo compone; ninguna ruta se define ahí |
| 5 | **Frontend y backend son dos despliegues** en un solo repositorio | Contrato por HTTP y OpenAPI, CORS explícito, variables de entorno separadas por lado |
| 6 | **Schemas de respuesta siempre distintos de los modelos de tabla** | Es lo que impide que una nota interna salga por la API |
| 7 | **El motor de scoring se porta a Python** | `talent-core` (TypeScript) no es consumible desde FastAPI; se reimplementa con sus 112 pruebas como especificación |

---

## 1. Contexto: qué sistema estamos diseñando

Un patrón arquitectónico no se elige en abstracto. Se elige para **este** sistema, **este** equipo y **este** negocio. Estos son los hechos que condicionan la decisión, todos verificables en [`memory-bank/projectbrief.md`](../memory-bank/projectbrief.md) y [`CONTEXT.md`](../CONTEXT.md).

### 1.1 Qué existe hoy

| Pieza | Qué es | Consume |
| --- | --- | --- |
| [`uis/website/`](../uis/website/) | Web pública. HTML estático desplegado en GitHub Pages | Nada |
| [`uis/backoffice/`](../uis/backoffice/) | Aplicación interna en Next.js: seguimiento de candidaturas | La API mock del curso, a través de [`lib/api.ts`](../uis/backoffice/lib/api.ts) |
| [`packages/talent-core/`](../packages/talent-core/) | Motor de scoring y matching en TypeScript, 18 funciones puras, 112 pruebas | Nada |
| [`services/`](../services/) | **Vacío a propósito.** Este documento es lo que lo llena | — |

No hay backend propio. Todo lo que el backoffice muestra viene de una API mock compartida del curso (`playground.4geeks.com/tracker/api/v1`), sin autenticación y escrita también por terceros.

### 1.2 Quién va a usarlo

No son consumidores anónimos. Son **equipos profesionales que trabajan ocho horas al día con la herramienta**:

| Usuario | Volumen | Uso previsto |
| --- | --- | --- |
| Consultores de selección | 40 | Uso intensivo diario: candidaturas, notas, scoring |
| Agentes de soporte | 30 | Consulta de base de conocimiento, tickets |
| Equipo de formación | 12 | Catálogo, inscripciones |
| Ventas | 18 | Pipeline, seguimiento |
| IT y operaciones | ~6 | Inventario de equipos, altas y bajas |
| Dirección | ~8 | Lectura de indicadores |
| Clientes B2B y candidatos | Cientos | Portales externos, lectura mayoritaria |

**Orden de magnitud: cientos de usuarios, no millones.** Ninguna hipótesis de escala debe construirse sobre tráfico que no vamos a tener.

### 1.3 Restricciones que pesan sobre la decisión

1. **El equipo de Tecnología son 6 personas**, y este backend no es su única responsabilidad.
2. **No hay telemetría, ni logs centralizados, ni despliegues automatizados.** La observabilidad llega en el hito 6. Hoy, si algo falla en producción, nos enteramos porque alguien llama por teléfono.
3. **Los dominios comparten entidades.** Una misma persona es candidato en selección, alumno en formación y contacto en soporte.
4. **Dos sedes: Valencia y Miami.** Ninguna decisión puede cerrar la puerta a una versión en inglés ni a datos segmentados por oficina.
5. **Se manejan datos de personas.** Las notas internas de los consultores **no son visibles para el candidato, nunca**. Esto es un requisito de arquitectura, no una preferencia de interfaz.
6. **La IA es el producto.** Scoring, RAG y agentes son entregables centrales y llegarán en hitos 7 a 9. El backend tiene que poder alojarlos sin rehacerse.

### 1.4 Qué queda fuera de este documento

Para que nadie espere aquí lo que no está: infraestructura de despliegue y contenedores, estrategia de observabilidad (hito 6), arquitectura del RAG y los embeddings (hito 7), modelo de autenticación definitivo y esquema de base de datos campo a campo. Se nombran cuando condicionan una decisión de hoy; no se resuelven.

---

## 2. Patrón arquitectónico: monolito modular por dominios

### 2.1 La decisión

**Proponemos un monolito modular organizado por dominios de negocio, con separación en capas dentro de cada dominio.**

Desglosado, porque cada palabra carga peso:

- **Monolito**: una sola aplicación FastAPI, un solo proceso, un solo despliegue, una sola base de datos.
- **Modular**: por dentro está dividido en dominios (`inventory`, `recruitment`, `training`, `support`…) con fronteras declaradas, no en un archivo gigante.
- **Por dominios**: la unidad de organización es el **área de negocio**, no el tipo técnico de archivo.
- **En capas dentro de cada dominio**: `router` (HTTP) → `service` (reglas de negocio) → `models` (persistencia), con la dependencia siempre en ese sentido.

### 2.2 Por qué, atado a Nexova

| Hecho de Nexova | Consecuencia arquitectónica |
| --- | --- |
| 6 personas en Tecnología | Microservicios exigen infraestructura, despliegues coordinados y guardias. No hay equipo para eso. Un monolito lo despliega una persona |
| Sin telemetría ni logs centralizados | En un sistema distribuido, un fallo se persigue entre servicios. Sin trazas distribuidas eso es a ciegas. En un monolito, la traza de la excepción es toda la historia |
| Los dominios comparten entidades | Un candidato aparece en selección, formación y soporte. Entre microservicios eso son llamadas de red y consistencia eventual; dentro del proceso es un `import` y una transacción |
| Cientos de usuarios internos, no millones | No hay ningún componente que necesite escalar por separado. Escalar el monolito entero es más barato que operar seis servicios |
| Hitos cada dos semanas, requisitos que cambian | Mover una frontera entre dominios dentro del mismo proceso es refactorizar. Entre servicios desplegados, es una migración |
| La IA llega en los hitos 7-9 | El RAG necesita conexiones persistentes a la base de datos vectorial y procesos largos. Encaja mal con funciones efímeras |
| Notas internas confidenciales | Una sola frontera de salida —la capa de schemas— es auditable. Seis servicios exponiendo datos son seis sitios donde revisar la fuga |

### 2.3 Alternativas evaluadas y por qué se descartan

| Patrón | Qué aportaría | Por qué no, **aquí** |
| --- | --- | --- |
| **MVC clásico** | Familiar, rápido de arrancar | MVC nació para aplicaciones donde el servidor renderiza vistas HTML. Nuestro frontend es Next.js: el backend **no tiene vistas**. La "V" sobra y la "C" acaba acumulando la lógica de negocio que debería estar en servicios |
| **Arquitectura en capas pura** (todos los routers juntos, todos los modelos juntos) | Estructura obvia, es lo que dibuja el ticket NXV-0201 | Funciona con uno o dos dominios. Con seis, `models.py` se convierte en un archivo de mil líneas que toca todo el equipo a la vez: conflictos constantes y ninguna frontera real. **La adoptamos como capas *dentro* de cada dominio, no como organización del proyecto** |
| **Microservicios** | Despliegue y escalado independientes, aislamiento de fallos | Paga costes de operación (red, despliegue, observabilidad, consistencia) a cambio de beneficios que Nexova hoy no necesita. Con 6 personas y sin telemetría, es cambiar un problema manejable por uno que no sabemos diagnosticar |
| **Serverless** (funciones) | Cero servidores que mantener, coste por uso | Tres choques concretos: arranques en frío incompatibles con los tiempos del RAG del hito 7; conexiones a base de datos persistentes que las funciones efímeras agotan; y procesos largos (indexar CVs) que no caben en el límite de ejecución |
| **Hexagonal / puertos y adaptadores** | Dominio aislado de la infraestructura, muy testeable | Buena arquitectura, pero su coste de indirección (interfaces y adaptadores por cada acceso externo) no se amortiza con este tamaño de equipo. Recogemos su idea útil —que el negocio no dependa del framework— en la capa `service` |

### 2.4 La regla que sostiene todo: dirección única de dependencias

```
HTTP  →  router.py      valida la petición, traduce a tipos de negocio, devuelve schemas
             ↓
         service.py     reglas de negocio. No sabe qué es una petición HTTP
             ↓
         models.py      tablas y consultas. No sabe qué es una regla de negocio
             ↓
           Base de datos
```

Tres prohibiciones, cortas y verificables en revisión de código:

1. **Un `service` nunca importa `fastapi`.** Si necesita señalar un error, lanza una excepción propia del dominio que el router traduce a HTTP. Así el mismo servicio se podrá llamar desde un agente, desde un worker o desde un script sin arrastrar el framework.
2. **Un `router` nunca calcula.** Si en un router aparece una suma, una resta o un `if` de negocio, está en el sitio equivocado.
3. **Un dominio nunca importa los modelos de otro dominio.** Solo puede llamar a su `service`, que es su contrato público. Esta es la frontera que permitiría, el día que haga falta, extraer un dominio a su propio servicio sin arqueología.

> **Ejemplo concreto del hito siguiente.** El ticket NXV-0201 dice: *"El stock siempre es el resultado neto de entradas menos salidas — no se puede establecer directamente"*. Esa frase es una regla de negocio, y por tanto vive en `inventory/service.py`. Si viviera en el router, el día que un agente de IA o un informe nocturno necesiten el stock, alguien la copiaría y las dos copias empezarían a divergir.

---

## 3. Estructura de carpetas y módulos

### 3.1 Criterio de separación: por dominio, no por tipo de archivo

Hay dos formas de repartir los archivos de un backend:

- **Por capa** (*package by layer*): todos los routers en una carpeta, todos los modelos en otra. Para tocar el inventario abres cuatro carpetas.
- **Por dominio** (*package by feature*): todo lo de inventario en una carpeta. Para tocar el inventario abres una.

Elegimos **por dominio**, y no es una opinión propia: es la conclusión a la que llegó la comunidad de FastAPI al pasar de proyectos pequeños a monolitos con varios dominios. La guía [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) lo formula así: la organización por tipo de archivo *"no encaja bien en monolitos con muchos dominios y módulos"*, y su estructura está **inspirada en [Netflix Dispatch](https://github.com/Netflix/dispatch)**, una aplicación FastAPI real en producción.

El criterio en una frase: **la carpeta responde a "¿de qué parte del negocio es esto?", no a "¿qué tipo de archivo es esto?"**.

### 3.2 Estructura propuesta

```
services/
└─ nexova-api/                    un servicio = una carpeta (convención del monorepo)
   ├─ app/
   │  ├─ main.py                  crea la app, monta middlewares e incluye routers. Nada más
   │  ├─ config.py                configuración tipada leída del entorno (pydantic-settings)
   │  ├─ database.py              motor, sesión y dependencia get_db
   │  ├─ exceptions.py            excepciones base y su traducción a respuestas HTTP
   │  ├─ dependencies.py          dependencias transversales (paginación, oficina, usuario)
   │  │
   │  ├─ domains/
   │  │  ├─ inventory/            ← primer dominio a implementar (ticket NXV-0201)
   │  │  │  ├─ router.py          APIRouter(prefix="/inventory", tags=["inventory"])
   │  │  │  ├─ schemas.py         Pydantic: qué entra y qué sale
   │  │  │  ├─ models.py          SQLModel: Asset, AssetEntry, AssetExit
   │  │  │  ├─ service.py         reglas: stock neto, validación de salidas
   │  │  │  ├─ constants.py       categorías, tipos de salida, oficinas
   │  │  │  └─ exceptions.py      InsufficientStockError…
   │  │  │
   │  │  ├─ recruitment/          candidaturas, procesos, notas internas, scoring
   │  │  ├─ training/             catálogo de formación e inscripciones
   │  │  ├─ support/              tickets y base de conocimiento
   │  │  └─ analytics/            indicadores agregados para dirección
   │  │
   │  └─ shared/                  utilidades sin dueño: fechas, paginación, texto
   │
   ├─ tests/
   │  ├─ conftest.py              base de datos de pruebas y cliente
   │  └─ inventory/               un paquete de pruebas por dominio
   │
   ├─ seed.py                     datos semilla de desarrollo
   ├─ requirements.txt
   ├─ .env.example                variables necesarias, sin valores reales
   └─ README.md                   qué es, cómo se arranca, cómo se prueba
```

**Solo `inventory` se crea ahora.** Los demás dominios aparecen en el árbol para fijar el criterio, no para crearse vacíos: [`techContext.md`](../memory-bank/techContext.md) ya recoge que en este repositorio no se crean carpetas "por si acaso".

### 3.3 Qué va en cada archivo de un dominio

Nomenclatura tomada de [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices), para que cualquiera que llegue del ecosistema Python la reconozca sin explicación:

| Archivo | Responsabilidad | Prohibido |
| --- | --- | --- |
| `router.py` | Declarar rutas, validar entrada, elegir código HTTP, devolver schemas | Calcular nada; tocar la base de datos directamente |
| `schemas.py` | Contratos de entrada y de salida (Pydantic) | Tener lógica de negocio |
| `models.py` | Tablas y relaciones (SQLModel) | Conocer HTTP |
| `service.py` | Reglas de negocio, consultas y transacciones | Importar `fastapi` |
| `constants.py` | Valores de dominio cerrados y mensajes de error | Configuración por entorno |
| `exceptions.py` | Errores propios del dominio | Depender de `HTTPException` |
| `dependencies.py` | Dependencias específicas del dominio | Duplicar las globales |

### 3.4 Equivalencia con la estructura del ticket NXV-0201

El ticket dibuja esta estructura de archivos dentro de `services/`:

```
services/
├── main.py
├── database.py
├── models.py
├── schemas.py
└── routers/
    └── inventory.py
```

Es la estructura del tutorial oficial de FastAPI, [*Bigger Applications – Multiple Files*](https://fastapi.tiangolo.com/tutorial/bigger-applications/), y **es correcta para un proyecto de un solo dominio**. Nuestra propuesta no la contradice: la **extiende para seis dominios** y la coloca dentro de una carpeta de servicio, porque [el README de `services/`](../services/README.md) reserva cada subcarpeta para un servicio distinto y en hitos posteriores habrá workers además de la API.

La correspondencia, archivo a archivo:

| Ticket NXV-0201 | Propuesta | Por qué |
| --- | --- | --- |
| `services/main.py` | `services/nexova-api/app/main.py` | Igual de plano, dentro del servicio |
| `services/database.py` | `services/nexova-api/app/database.py` | Sin cambios: el acceso a datos es transversal |
| `services/models.py` | `app/domains/<dominio>/models.py` | Un `models.py` global mezclaría inventario con selección |
| `services/schemas.py` | `app/domains/<dominio>/schemas.py` | Mismo motivo |
| `services/routers/inventory.py` | `app/domains/inventory/router.py` | El router se guarda junto a lo que enruta |

**Lo que no cambia:** los nombres de las entidades (`Asset`, `AssetEntry`, `AssetExit`), sus campos y las rutas expuestas son **exactamente** los del ticket. La estructura interna es nuestra; el contrato público es suyo.

---

## 4. Endpoints y routers

### 4.1 Cómo se compone la API

Un `APIRouter` por dominio, declarando su propio `prefix` y sus `tags`, tal como documenta [el tutorial oficial](https://fastapi.tiangolo.com/tutorial/bigger-applications/). `main.py` no define ni una sola ruta: solo compone.

```python
# app/main.py — ilustrativo
from fastapi import FastAPI
from app.domains.inventory import router as inventory

app = FastAPI(title="Nexova API")
app.include_router(inventory.router)
```

```python
# app/domains/inventory/router.py — ilustrativo
router = APIRouter(prefix="/inventory", tags=["inventory"])
```

Esto da tres cosas gratis: las rutas relativas dentro del router no repiten el prefijo; la documentación interactiva de `/docs` queda agrupada por dominio, legible para quien no escribió el código; y añadir un dominio es añadir dos líneas a `main.py`, sin tocar nada existente.

### 4.2 Criterio de agrupación de rutas

1. **Un router por dominio de negocio.** La primera parte de la ruta es siempre el dominio: `/inventory/...`, `/recruitment/...`.
2. **Recursos en plural y en inglés**, como el resto del código del repositorio.
3. **Anidamiento de un solo nivel.** `/recruitment/candidates/{id}/notes` es legible; tres niveles ya no.
4. **Sin verbos en la URL.** El verbo es el método HTTP. La excepción son acciones de negocio que no son un CRUD, y entonces se nombran como sustantivo del acto: `POST /recruitment/vacancies/{id}/ranking`.
5. **Filtros por query string, nunca por ruta.** `?office=Valencia&status=in_progress`, no `/valencia/in_progress`.

### 4.3 Rutas del dominio `inventory`

Literalmente las del ticket NXV-0201. No se renombran, no se reordenan:

| Método | Ruta | Qué hace | Regla de negocio implicada |
| --- | --- | --- | --- |
| `GET` | `/inventory/products` | Lista activos con `current_stock` | Stock calculado al vuelo, nunca leído de una columna |
| `POST` | `/inventory/products` | Registra un activo | `sku` único |
| `GET` | `/inventory/products/{id}` | Un activo con su stock | 404 si no existe |
| `POST` | `/inventory/orders/inbound` | Registra una entrada (`AssetEntry`) | `quantity` positiva |
| `POST` | `/inventory/orders/outbound` | Registra una salida (`AssetExit`) | Rechazar con **400** si supera el stock; `assigned_to` obligatorio si `exit_type = "allocation"` y nulo si es `"consumption"` |
| `GET` | `/inventory/orders` | Entradas y salidas con datos del activo | — |

> ⚠️ **Punto de atención para quien implemente.** Las rutas dicen `products` y `orders`, pero las entidades se llaman `Asset`, `AssetEntry` y `AssetExit`. La discrepancia viene del enunciado —las rutas son genéricas, las entidades están adaptadas a Nexova— y **se respeta tal cual**: el evaluador llama a esas rutas literales. La traducción ocurre en el router; los modelos, los schemas y el vocabulario interno usan `Asset*`. Anotarlo en el `README.md` del servicio evita que alguien "arregle" la incoherencia y rompa la entrega.

### 4.4 Rutas previstas para los demás dominios

Esbozo del criterio, no contrato cerrado. **Los campos concretos se fijarán cuando el hito correspondiente los defina; aquí no se inventa vocabulario de negocio.**

| Dominio | Rutas previstas | Notas |
| --- | --- | --- |
| `recruitment` | `GET/POST /recruitment/candidates` · `GET/PATCH /recruitment/candidates/{id}` · `GET/POST /recruitment/candidates/{id}/notes` · `GET /recruitment/processes` · `POST /recruitment/vacancies/{id}/ranking` | Usa el vocabulario ya fijado: **candidatura**, **estado**, **etapa**, **nota interna**. Las notas internas exigen autorización: nunca se sirven a un portal de candidato |
| `training` | `GET /training/courses` · `POST /training/enrollments` | Sustituye al catálogo en PDF y al Google Form |
| `support` | `GET/POST /support/tickets` · `GET /support/knowledge-base` | La búsqueda semántica se añade en el hito 7 sobre estas mismas rutas |
| `analytics` | `GET /analytics/overview` | Solo lectura y agregados; no escribe nada |

### 4.5 Versionado de la API

**Decisión: se despliega sin prefijo de versión y se introduce `/api/v1` cuando exista el primer consumidor que no controlemos.**

El motivo es concreto: el ticket NXV-0201 exige *"todos los endpoints bajo el prefijo `/inventory`"*, y anteponer `/api/v1` rompería esa exigencia literal. Mientras los únicos consumidores sean nuestras propias interfaces, que se despliegan a la vez que la API, el versionado no compra nada y añade ruido.

Cuando haga falta —portal de cliente, integración externa—, la transición no es traumática: el mismo objeto `APIRouter` puede incluirse dos veces con prefijos distintos, sirviendo `/inventory` y `/api/v1/inventory` a la vez durante el periodo de migración. La técnica está soportada de serie: los parámetros pasados en `include_router` complementan a los del router sin modificarlo.

### 4.6 Errores: un formato, y solo uno

El backoffice ya tiene que lidiar hoy con **dos formatos de error distintos** devueltos por la API mock del curso — se ve en [`lib/api.ts`](../uis/backoffice/lib/api.ts), que traduce tanto `{ error, details }` como el `{ detail: [...] }` de FastAPI. No repitamos ese error en casa.

| Situación | Código | Origen |
| --- | --- | --- |
| El cuerpo no cumple el schema | `422` | Automático de Pydantic. Formato `{ detail: [{ loc, msg }] }` |
| Regla de negocio incumplida (stock insuficiente) | `400` | Lanzado por el `service`, traducido por el router. Mensaje literal del ticket |
| Recurso inexistente | `404` | — |
| Sin permiso sobre el recurso | `403` | Cuando exista autenticación |

`422` para "está mal escrito" y `400` para "está bien escrito pero no se puede hacer" es la línea que separa validación de negocio. Que `assigned_to` sea obligatorio cuando `exit_type = "allocation"` es validación de forma → va en el schema → `422`. Que no haya stock suficiente solo se sabe consultando la base de datos → es negocio → va en el service → `400`.

---

## 5. Convenciones estándar de FastAPI: qué encontramos y qué adoptamos

Esta sección recoge la investigación previa que pedía el encargo. Cada convención, con su origen y nuestra decisión.

| Convención encontrada | Fuente | Decisión para Nexova |
| --- | --- | --- |
| Estructura `app/` con `main.py`, `dependencies.py` y `routers/` | [FastAPI · Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) (documentación oficial) | **Adoptada** como base; `routers/` se sustituye por `domains/` al pasar de uno a varios dominios |
| `APIRouter` con `prefix`, `tags`, `dependencies` y `responses` comunes | [FastAPI · Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) | **Adoptada** íntegra. Es la pieza que hace que las rutas no acaben en un solo archivo |
| Paquete por dominio con `router / schemas / models / service / dependencies / constants / exceptions / utils` | [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices), inspirado en [Netflix Dispatch](https://github.com/Netflix/dispatch) | **Adoptada**, recortando `utils.py` y `config.py` por dominio hasta que hagan falta |
| Importar entre dominios con alias explícito (`from app.domains.inventory import constants as inventory_constants`) | [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) | **Adoptada**: hace visible en el propio `import` cuándo se cruza una frontera de dominio |
| FastAPI ejecuta las rutas `def` (síncronas) en un *threadpool*; una ruta `async def` con una llamada bloqueante **bloquea el bucle de eventos entero** | [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) | **Adoptada como regla**: rutas `def` mientras el acceso a datos sea síncrono. `async def` solo cuando todo lo que hay dentro sea esperable. Es el error de rendimiento más común en FastAPI y el más difícil de diagnosticar sin telemetría |
| Resultados de dependencias cacheados dentro de una misma petición | [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) | **Adoptada**: permite trocear dependencias sin pagar cada una dos veces |
| Convenciones de nombres en base de datos: `snake_case`, tablas en singular, sufijo `_at` para fechas | [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) | **Adoptada**. Encaja con el `created_at` que ya fija el ticket |
| Stack de referencia: FastAPI + SQLModel + Pydantic + PostgreSQL, backend y frontend en carpetas separadas | [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (plantilla oficial del autor de FastAPI) | **Adoptada** en cuanto al stack y a la separación de carpetas. No adoptamos su despliegue conjunto ni su proxy inverso: exceden el hito |
| Migraciones con Alembic desde el primer día | [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | **Aplazada.** Mientras el esquema se recree en desarrollo, añade ceremonia sin beneficio. Se adopta en cuanto haya datos reales que no se puedan perder, y esa frontera se anota en `techContext.md` |

---

## 6. Frontend y backend como sistemas separados

Next.js y FastAPI son **dos aplicaciones distintas, en dos procesos distintos, con dos ciclos de despliegue distintos**, aunque vivan en el mismo repositorio. Esa separación tiene consecuencias que hay que gestionar explícitamente.

### 6.1 Un repositorio, dos despliegues

Mantenemos el monorepo: el frontend en [`uis/`](../uis/), el backend en [`services/`](../services/). Motivos: un cambio que toca contrato y consumidor cabe en una sola rama y una sola PR, y la CI ya está acotada por rutas, de modo que tocar el backend no dispara la verificación del backoffice.

Lo que **no** compartimos es el despliegue. El backoffice es una aplicación Next.js; la API es un proceso Python. Se despliegan por separado, y por tanto **puede haber momentos en que las versiones no coincidan**. De ahí la regla: los cambios de contrato son aditivos (se añaden campos, no se renombran); retirar un campo es una operación en dos pasos, separados por un despliegue.

### 6.2 El contrato: OpenAPI

FastAPI genera el esquema OpenAPI de la API sin que haya que escribirlo. Eso nos da documentación navegable en `/docs` —útil para el equipo no técnico— y, sobre todo, **una fuente de la que derivar los tipos de TypeScript del frontend** en lugar de escribirlos a mano y esperar que coincidan. La generación automática de tipos se evaluará cuando el número de endpoints lo justifique; el principio, desde hoy, es que **el backend es la fuente de verdad del contrato**.

### 6.3 CORS: el problema que vamos a tener el primer día

Cuando el navegador ejecuta el backoffice servido desde `http://localhost:3000` y este pide datos a `http://localhost:8000`, está haciendo una petición **entre orígenes distintos**. Un origen es la terna **protocolo + dominio + puerto**: si cambia cualquiera de los tres, es otro origen y el navegador bloquea la respuesta salvo que el servidor la autorice explícitamente.

Dos detalles que nos van a morder, y no son hipotéticos:

1. **`localhost` y `127.0.0.1` son orígenes distintos**, aunque apunten a la misma máquina: la comparación es textual, no de red. La [documentación de FastAPI](https://fastapi.tiangolo.com/tutorial/cors/) lo dice explícitamente. **Ya nos ocurrió en el hito 4** con `allowedDevOrigins` de Next: la página no se hidrataba y los componentes se quedaban colgados en carga *sin ningún error visible*. Con el backend propio el síntoma será igual de mudo: el navegador bloquea la respuesta, `fetch` lanza sin código HTTP, y [`lib/api.ts`](../uis/backoffice/lib/api.ts) lo reporta como "No se ha podido conectar con el servidor" — un mensaje que apunta a la red cuando el problema es de cabeceras. **Ambas variantes van en la lista de orígenes permitidos.**
2. **`allow_origins=["*"]` es incompatible con `allow_credentials=True`.** La documentación de FastAPI es tajante: con credenciales activadas hay que enumerar orígenes, métodos y cabeceras. Como la autenticación llegará, empezamos ya con **lista explícita**: evita descubrirlo el día que se añada el login.

Configuración prevista, con los orígenes leídos de la configuración y no escritos en el código:

| Entorno | Orígenes permitidos |
| --- | --- |
| Desarrollo | `http://localhost:3000`, `http://127.0.0.1:3000` |
| Producción | El dominio del backoffice y el de la web pública. Nada más |

### 6.4 Alternativa a CORS: proxy desde Next

Existe una segunda opción que conviene conocer aunque no la adoptemos ahora. Next.js permite [reescribir rutas](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites) hacia un destino externo: el navegador pide `/api/inventory/products` al propio Next, y este lo reenvía a la API. Para el navegador **todo es el mismo origen**, así que no hay CORS ni peticiones *preflight*.

**Decisión:** CORS explícito, por ahora. El proxy oculta el hecho de que son dos sistemas —cómodo hasta que falla y nadie sabe de qué lado— y añade un salto de red. Queda anotado como salida si la configuración de CORS en producción se vuelve difícil de mantener.

### 6.5 Variables de entorno: dos lados, dos reglas

Este es el punto donde un despiste se convierte en un incidente de seguridad.

**En el frontend**, la [documentación de Next.js](https://nextjs.org/docs/app/guides/environment-variables) es clara: las variables con prefijo `NEXT_PUBLIC_` se **incrustan en el paquete JavaScript durante el `build`**, sustituyendo cada referencia por su valor literal. Tres consecuencias:

- **Son públicas.** Cualquiera puede leerlas abriendo las herramientas de desarrollo. Nunca una credencial ahí.
- **Quedan congeladas en el momento de compilar.** Cambiar la variable en el servidor no cambia nada: hay que reconstruir.
- Las variables **sin** ese prefijo solo existen en el servidor de Next, y ahí sí pueden guardar secretos.

**En el backend**, la configuración se lee una sola vez, en un objeto tipado (`app/config.py`) que valida al arrancar. Si falta la URL de la base de datos, el servicio **falla al arrancar con un mensaje claro**, en lugar de fallar en la primera petición de un usuario. Nada de `os.environ` disperso por el código.

| Variable | Dónde vive | ¿Pública? |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Frontend, en build | **Sí.** Es solo la URL de la API |
| `DATABASE_URL` | Backend | No. Solo en el entorno del servidor |
| `CORS_ORIGINS` | Backend | No, aunque su contenido no sea secreto |
| Claves de proveedores de IA | Backend, a partir del hito 7 | **Nunca** en el frontend |

Se mantiene la regla ya vigente: `.env*` no se versiona; sí se versiona `.env.example` con las claves y sin los valores.

### 6.6 Autenticación: lo que decidimos hoy y lo que no

El hito de inventario no lleva autenticación —el ticket dice que `user_uuid` referencia usuarios de TinyDB y que no se cree un modelo de usuario—, así que **no la implementamos ahora**. Pero dejamos fijado lo que condiciona la estructura:

- La identidad se resolverá en una **dependencia transversal** (`app/dependencies.py`), no en cada router. Cuando llegue, se activa en un sitio.
- El dominio `recruitment` **no podrá servirse sin autorización**: contiene notas internas sobre personas.
- Se decidirá entonces entre token en cabecera o sesión por cookie. La cookie entre dominios distintos arrastra requisitos adicionales de CORS y de configuración; el token en cabecera no. Es un argumento a tener presente, no una decisión tomada.

---

## 7. Decisiones técnicas iniciales

Registradas en formato corto —decisión, motivo, consecuencia— para que se puedan discutir una por una.

| # | Decisión | Motivo | Consecuencia asumida |
| --- | --- | --- | --- |
| **D-01** | **SQLModel** como ORM | Una sola definición sirve de tabla y de base para los schemas; es lo que usa la plantilla oficial de FastAPI y lo que pide el ticket | Menos flexibilidad que SQLAlchemy puro en consultas complejas. Aceptable en este dominio |
| **D-02** | **Schemas de respuesta siempre distintos del modelo de tabla** | Devolver el modelo expone cualquier columna que se añada después, sin que nadie lo decida | Algo de repetición entre modelo y schema. Es el precio de que una nota interna no pueda salir por accidente |
| **D-03** | **Configuración tipada y validada al arrancar** (`pydantic-settings`) | Un fallo de configuración debe romper el despliegue, no la primera petición de un usuario | Un archivo más; ninguna lectura de entorno fuera de él |
| **D-04** | **Campos calculados, nunca almacenados**, cuando se derivan de otros datos | `current_stock` derivado de entradas menos salidas no puede desincronizarse | Coste de cálculo en cada consulta. Con este volumen es irrelevante; si dejara de serlo, se cachea |
| **D-05** | **El motor de scoring se porta a Python** dentro de `recruitment` | `talent-core` es TypeScript: un proceso Python **no puede importarlo**. La alternativa —exponerlo como servicio Node— introduciría el primer microservicio justo donde argumentamos no tenerlos | Lógica en dos lenguajes. Se mitiga con D-06 |
| **D-06** | Las **112 pruebas de `talent-core` son la especificación** del port | El comportamiento esperado ya está escrito y verificado; portar los casos de prueba antes que el código convierte una reescritura en una traducción verificable | Hay que traducir también las pruebas. Es trabajo, pero es trabajo con red |
| **D-07** | **La API mock del curso convive; no se envuelve** | Envolverla en nuestro backend solo añadiría un salto de red y un punto de fallo sobre datos que no controlamos | El backoffice apuntará a una u otra según la variable de entorno, dominio por dominio |
| **D-08** | **Pruebas con `pytest` y el cliente de pruebas de FastAPI**, sobre base de datos efímera | Probar el router prueba de paso schemas, dependencias y servicio | Las pruebas tardan más que las unitarias puras de `talent-core` |
| **D-09** | **CI acotada a la carpeta del servicio**, igual que los demás workflows | Es la convención ya establecida: cada workflow se dispara solo con su carpeta | Un workflow más que mantener |
| **D-10** | **Código y nombres en inglés; documentación, comentarios y commits en español** | Regla vigente del repositorio. Los nombres de dominio del ticket (`Asset`, `office`, `exit_type`) se respetan literalmente | Ninguna. Es continuidad |

> **D-05 corrige una decisión anterior.** [`techContext.md`](../memory-bank/techContext.md) afirma que `talent-core` "se consumirá desde `services/`". Se escribió antes de decidir el lenguaje del backend y **dejó de ser cierta** al elegir FastAPI. Se corrige en el banco de memoria en el mismo cambio que aprueba este documento, con su motivo.

---

## 8. Riesgos y puntos de atención

Qué puede salir mal si el equipo no sigue la estructura propuesta, ordenado por probabilidad.

### R-01 · La lógica de negocio se instala en los routers

**El riesgo más probable, con diferencia.** Es más rápido escribir el cálculo del stock dentro de la función de la ruta que crear un `service.py`. Funciona. Y el día que el informe nocturno, un agente de IA o un segundo endpoint necesiten el mismo cálculo, se copia y pega. A partir de ahí hay dos versiones de "cuánto stock hay" y solo una se corrige cuando aparece el fallo.

**Síntomas:** routers de más de 200 líneas; consultas a la base de datos dentro de una función de ruta; la misma operación aritmética en dos archivos.
**Mitigación:** la regla "el router no calcula" se verifica en revisión de PR. Toda regla del ticket NXV-0201 nace en `service.py`.

### R-02 · El monolito modular degenera en monolito a secas

Los dominios están separados por convención, no por el compilador. Nada impide que `training/service.py` importe `recruitment/models.py` un martes por la tarde. Bastan unos pocos atajos así para que las fronteras dejen de existir: entonces ya no se puede extraer nada, ni probar nada aisladamente, y tenemos el sistema que este documento pretendía evitar.

**Mitigación:** un dominio solo importa el `service` de otro, nunca sus modelos, y los imports entre dominios llevan alias explícito para que se vean en revisión. Si dos dominios se necesitan mutuamente, la frontera está mal trazada y se rediscute antes de escribir más código.

### R-03 · CORS y orígenes: fallo silencioso y diagnóstico erróneo

Ya descrito en §6.3. Merece estar aquí porque **el síntoma engaña**: el usuario ve "no se ha podido conectar con el servidor" y el equipo mira la red, cuando el problema es una lista de orígenes. Se pierde una tarde.

**Mitigación:** ambas variantes (`localhost` y `127.0.0.1`) en la lista desde el primer commit; el `README.md` del servicio documenta el síntoma; lista explícita en lugar de comodín desde el principio.

### R-04 · Un secreto en una variable `NEXT_PUBLIC_`

Basta con que alguien necesite una clave de API en el frontend y la añada al `.env.local` con el prefijo que ve en el resto de variables. Esa clave queda **incrustada en el JavaScript** que se sirve a todos los navegadores, y además **congelada en el paquete compilado**: rotarla exige reconstruir y redesplegar.

**Mitigación:** ninguna credencial cruza al frontend. Lo que necesite una clave se hace en el backend y se expone como endpoint. Es una regla de una línea, y conviene que esté escrita antes de que haga falta.

### R-05 · El scoring se duplica y las dos versiones divergen

Consecuencia directa y conocida de D-05: la misma lógica en TypeScript y en Python. Si el criterio de puntuación cambia y solo se actualiza un lado, el backoffice y la API darán puntuaciones distintas para el mismo candidato. En un producto que vende **scoring explicable**, eso destruye la confianza del cliente de una manera difícil de recuperar.

**Mitigación:** una única implementación autoritativa —la del backend— en cuanto el port esté completo; `talent-core` queda como librería del banco de pruebas y del frontend, y se marca como tal en su README. Las 112 pruebas portadas actúan de detector de divergencia.

### R-06 · Una nota interna sale por la API

El riesgo con peor consecuencia, aunque sea el menos probable. Basta con devolver el modelo de tabla en lugar del schema de salida en un endpoint que un portal de candidato consuma, y una anotación privada de un consultor sobre una persona se vuelve pública. No es un fallo técnico recuperable: es información sobre personas, en dos jurisdicciones con normativas distintas (España y Florida).

**Mitigación:** D-02 sin excepciones —ningún endpoint devuelve un modelo de tabla—, las notas internas viven en un recurso separado con su propia autorización, y ningún endpoint pensado para consumo externo las incluye en su schema de respuesta. Cuando llegue el portal del candidato, este punto se revisa expresamente antes de desplegar.

### R-07 · El vocabulario de dominio se erosiona

El repositorio ya fija qué significa **candidatura**, **estado**, **etapa** y **nota interna**, y la regla de que los valores crudos de la API no aparecen nunca en la interfaz. Un backend nuevo es la ocasión perfecta para introducir un sinónimo —`application` en vez de `candidate`, `phase` en vez de `stage`— y romper el lenguaje común con el cliente.

**Mitigación:** los nombres de campo del ticket y del glosario se usan literalmente; cualquier término nuevo se pregunta antes de escribirse, no después.

---

## 9. Preguntas abiertas para el CTO

Lo que este documento **no** decide, porque no le corresponde:

1. **Base de datos de producción.** El ticket menciona Supabase para las tablas y TinyDB para usuarios. ¿Es TinyDB solo de desarrollo o se queda? De la respuesta depende cómo se resuelve la identidad del usuario en el resto de dominios.
2. **Autenticación y roles.** ¿Cuántos perfiles distintos? Consultor, responsable de área, cliente y candidato tienen visibilidades muy diferentes sobre los mismos datos.
3. **Momento de introducir el versionado de la API** (§4.5): ¿lo ata la primera integración con un cliente externo?
4. **Responsable de Ventas.** [`CONTEXT.md`](../CONTEXT.md) da dos nombres distintos —Megan Clarke y Marcos Ibáñez— para el mismo puesto. Sigue sin resolverse y bloqueará el dominio de ventas cuando llegue.

---

## 10. Fuentes consultadas

Documentación oficial y proyectos de referencia revisados para esta propuesta:

- [FastAPI · Bigger Applications – Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — estructura `app/`, `APIRouter` con `prefix` y `tags`, composición en `main.py`.
- [FastAPI · CORS (Cross-Origin Resource Sharing)](https://fastapi.tiangolo.com/tutorial/cors/) — definición de origen, `CORSMiddleware` e incompatibilidad entre comodín y credenciales.
- [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) — plantilla oficial del autor de FastAPI: stack SQLModel + Pydantic + PostgreSQL y separación de backend y frontend.
- [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) — estructura por dominios, nomenclatura de archivos, rutas síncronas frente a asíncronas y convenciones de base de datos.
- [Netflix/dispatch](https://github.com/Netflix/dispatch) — aplicación FastAPI en producción, origen de la estructura por dominios.
- [Next.js · Environment Variables](https://nextjs.org/docs/app/guides/environment-variables) — el prefijo `NEXT_PUBLIC_` y su incrustación en el paquete durante el build.
- [Next.js · rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites) — proxy hacia un destino externo como alternativa a CORS.

Contexto interno: [`CONTEXT.md`](../CONTEXT.md) · [`docs/contexts/05-backend-development.es.md`](./contexts/05-backend-development.es.md) (ticket NXV-0201) · [`memory-bank/`](../memory-bank/) · [`services/README.md`](../services/README.md).
