# Contexto de negocio — Nexova Solutions

> Qué empresa es, quién decide, qué problema resolvemos y con qué palabras se nombra cada cosa.
> Fuente de verdad: [`CONTEXT.md`](../CONTEXT.md). Si algo aquí lo contradice, manda `CONTEXT.md`.

## La empresa

Nexova Solutions es una **consultora B2B de recursos humanos y selección de talento**, fundada en 2011.

| Dato | Valor |
| --- | --- |
| Sedes | Valencia (España) — sede central · Miami (Florida) — expansión |
| Plantilla | 120 empleados |
| Facturación | ~8 M$ anuales |
| Líneas de negocio | Headhunting de mandos medios y directivos · Outsourcing de soporte al cliente · Formación corporativa |
| Clientes | Medianas empresas de tecnología, retail y servicios financieros |
| CEO | Laura Mendoza (fundadora) |

Sus clientes **no son consumidores anónimos**: son equipos profesionales con flujos de trabajo y expectativas concretas. Todo lo que construimos se diseña para un usuario que trabaja con la herramienta ocho horas al día, no para un visitante ocasional.

## El problema de fondo

Nexova tiene reputación, red de contactos y experiencia. Lo que no tiene es **infraestructura**. Doce años de herramientas introducidas una a una y nunca conectadas: un ATS hecho a medida en los 2010, HubSpot, un Zendesk legacy, Google Workspace de pegamento y hojas de cálculo haciendo de sistemas de gestión. Sin telemetría, sin logs centralizados, sin una imagen del negocio en tiempo real.

La consecuencia medible: los consultores dedican la mayor parte del tiempo a tareas manuales, los clientes no ven el estado de sus procesos, soporte incumple su SLA y la dirección decide con datos de hace una semana.

Laura ha montado un equipo de AI Engineering para cerrar esa brecha. **Este monorepo es el trabajo de ese equipo.**

## Quién pide qué

| Área | Responsable | Dolor actual | Qué necesita |
| --- | --- | --- | --- |
| **Operaciones de Selección** (negocio principal) | Javier Almeida · 40 consultores | Criba manual de 30-80 CVs por proceso; sin estado en tiempo real; matching por intuición | Scoring y ranking de CVs, RAG sobre la base de candidatos, portal de candidato, agente de comunicación |
| **Formación Corporativa** | Elena Vargas · 12 personas | Catálogo en PDF trimestral, inscripciones por Google Form, cero personalización | Catálogo con búsqueda e inscripción, recomendador, portal del alumno, chatbot formativo |
| **Soporte al Cliente** (externalizado) | Roberto Díaz · 30 agentes | Sin base de conocimiento; resolución media 48 h frente a un SLA de 24 h | Chatbot de primera línea con RAG (objetivo: 40 % sin humano), KB con búsqueda semántica, dashboard en vivo, análisis de sentimiento |
| **Ventas y Desarrollo de Negocio** | 18 personas (6 account managers, 12 SDRs) | CRM usado por el 40 % del equipo; prospección manual; deals perdidos por falta de seguimiento | Dashboard de pipeline, secuencias automatizadas, alertas de inactividad, agente que sugiera el ángulo de propuesta |
| **Marketing y Comunicación** | Carmen Ruiz | Web de 2019 lenta y no accesible; sin medición de conversión | Web nueva con SEO/GEO y schema.org, pipeline de contenido con IA, dashboard de marketing |
| **Recursos Humanos** (interno) | Patricia Solís · 4 personas | Vacaciones y consultas por email y hoja de cálculo; onboarding manual | Portal interno, onboarding automatizado, KPIs de RRHH, agente de políticas |
| **Tecnología** | Sergio Molina (CTO) · 6 personas | Stack desconectado, sin telemetría, despliegues manuales | Telemetría y logging, pipeline de datos, monitorización con alertas, agente de arquitectura |
| **Dirección** | Laura Mendoza (CEO) | Informe semanal en PDF que cuesta 4-8 h por manager y llega caducado | Dashboard ejecutivo unificado, informe automático, alertas por umbral, asistente en lenguaje natural |

**Sergio Molina (CTO) es nuestro interlocutor técnico directo.** Los encargos llegan por correo suyo o con copia a él.

## Qué se está construyendo

Un único sistema que crece hito a hito. Lo entregado hasta hoy y lo que viene está en [`progress.md`](./progress.md); el stack y las decisiones, en [`techContext.md`](./techContext.md).

El eje del proyecto es **Operaciones de Selección**, porque es el negocio principal de Nexova y porque la propia herramienta es una demostración de lo que la empresa vende: encontrar a las personas adecuadas.

## Vocabulario de dominio

El código y la interfaz usan estas palabras, y solo estas. Cambiarlas rompe el lenguaje común con el cliente.

| Término | Qué significa aquí |
| --- | --- |
| **Candidatura** | La postulación de una persona a un puesto concreto. No "solicitud" ni "aplicación". |
| **Estado** (`status`) | En qué punto de la decisión está la candidatura: Recibida, En proceso, Seleccionada, Descartada |
| **Etapa** (`stage`) | En qué punto del circuito está: Pendiente de revisión, En revisión, Entrevista personal, Entrevista técnica, Oferta presentada |
| **Proceso de selección** | El encargo completo de cubrir una vacante para un cliente, de principio a fin |
| **Consultor** | La persona de Nexova que lleva un proceso de selección |
| **Nota interna** | Anotación del consultor tras una llamada o entrevista. **Nunca visible para el candidato.** |
| **Scoring** | Puntuación de un candidato frente a una vacante. Debe ser **explicable**: si no se puede justificar, no sirve. |
| **SLA** | Compromiso de tiempo de respuesta con el cliente. En soporte son 24 h. |

### Vocabulario de inventario — a partir del hito 5

Lo fija el ticket **NXV-0201** ([`docs/contexts/05-backend-development.es.md`](../docs/contexts/05-backend-development.es.md)). Se usa literalmente:

| Término | Qué significa aquí | Nombre en el código |
| --- | --- | --- |
| **Activo** | Equipo o material de la empresa: portátiles, periféricos, material de oficina, materiales de formación | `Asset` |
| **Entrada de activos** | Una compra o entrega de proveedor recibida por Nexova | `AssetEntry` |
| **Salida de activos** | Una asignación a un empleado (`allocation`) o un consumo (`consumption`) | `AssetExit` |
| **Stock** | Resultado neto de entradas menos salidas. **Se calcula, nunca se almacena ni se establece a mano** | `current_stock` |
| **Oficina** | `"Valencia"` o `"Miami"`. Ambas conviven en las mismas tablas y se filtran por este campo | `office` |

### Etiquetas de dominio — regla dura

Los valores crudos de la API (`in_progress`, `personal_interview`, `offer_presented`…) **no aparecen nunca en la interfaz**. La traducción vive en un único mapa por aplicación. El detalle y la verificación, en [`.agents/rules/backoffice-nextjs.md`](../.agents/rules/backoffice-nextjs.md) y en la skill [`verificar-etiquetas-de-dominio`](../.agents/skills/verificar-etiquetas-de-dominio/SKILL.md).

## Proceso de selección activo

Es el caso real que soportan las herramientas construidas hasta ahora:

| Campo | Valor |
| --- | --- |
| Puesto | Asistente de Dirección |
| Sede | Valencia |
| Perfil | Asistencia ejecutiva, gestión de agenda y viajes, inglés y español profesionales |
| Volumen | Más de 100 candidaturas |
| Origen del encargo | Elena Vargas, por correo a Sergio Molina |

## Restricciones de negocio

- **Idioma de trabajo: español.** Documentación, commits y textos de interfaz en español. El código, los nombres de variables y las carpetas, en inglés.
- **Dos sedes, dos idiomas a futuro.** Miami existe. Ninguna decisión debe cerrar la puerta a una versión en inglés.
- **La IA es el producto, no un adorno.** En Nexova el scoring, el matching, el RAG y los agentes son entregables centrales. No son "mejoras opcionales" que se recortan si falta tiempo.
- **Las notas internas no salen nunca del ámbito interno.** Es información sobre personas.

## Ambigüedades conocidas

Anotadas para que nadie invente una respuesta:

- `CONTEXT.md` nombra a **Megan Clarke** como responsable de Ventas en la descripción de la organización y a **Marcos Ibáñez** en la ficha del departamento. No está resuelto cuál es el vigente. Si un entregable necesita ese nombre, hay que preguntar antes de elegir.
