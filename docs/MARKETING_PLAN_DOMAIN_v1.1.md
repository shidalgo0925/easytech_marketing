# Pieza 1 — Documento Fundacional del Dominio de Marketing

**Versión:** 1.1  
**Estado:** ✅ APROBADO · CONGELADO  
**Alcance:** Solo dominio conceptual. Sin persistencia, schema, API, UI ni código.

> **Regla de gobierno.** Este documento define el dominio de marketing de EM+Acción. Ninguna decisión de implementación (schema, persistencia, API, UI, IA o infraestructura) podrá modificar estas reglas sin una **nueva versión aprobada** del dominio.

**Gobernanza:** Toda pieza futura se adapta al dominio; el dominio no se adapta a implementaciones.

### Disciplina del proyecto (desde aprobación v1.1)

Toda nueva pieza debe responder:

1. **¿Respeta el dominio?** → Si no, **NO GO**.
2. **¿Introduce acoplamiento innecesario?** → Si sí, **NO GO**.
3. **¿Puede evolucionar sin romper el dominio?** → Si no, **NO GO**.
4. **¿Pertenece a esta capa?** → Si pertenece a otra, se mueve de pieza; **no se modifica el dominio**.

**Terminología:** a partir de aquí se habla de **Arquitectura del Dominio de Marketing** (el Plan es una entidad dentro del dominio, no el centro del sistema).

---

## 1. Objetivo de EM+Acción

**EM+Acción no es un gestor de publicaciones.**

EM+Acción es un **Asistente Ejecutivo de Marketing**: un sistema que alinea y ejecuta **decisiones estratégicas de marketing** bajo control del administrador del tenant.

- El **administrador** define el enfoque, aprueba, corrige y autoriza la ejecución.
- La **IA** actúa como **asesor estratégico y generador de propuestas**. La ejecución siempre requiere un proceso explícito del sistema y, cuando corresponda, **aprobación humana**.
- La IA **no publica**, **no modifica el Plan**, **no activa campañas**, **no cambia presupuestos**. Solo propone.

---

## 2. Principios fundacionales del dominio

### Principio 1 — El Plan es declarativo, nunca imperativo

El **Marketing Plan** describe la **intención estratégica**; nunca describe **cómo ejecutarla**.

| Pertenece al Plan | No pertenece al Plan |
|-------------------|----------------------|
| Aumentar ventas | Publicar los lunes |
| Captar leads | Usar Facebook |
| Posicionar marca | Crear flyer X |
| North star metric | Ejecutar campaña Y |

Esa separación evita que el Plan se convierta en un «plan de trabajo». La ejecución pertenece a capas operativas (cola, campañas, calendario, conectores).

### Principio 2 — La IA propone; el sistema y el humano ejecutan

La IA es miembro del equipo en rol **consultivo y generativo**, no ejecutivo autónomo.

Toda acción con efecto en el mundo real (publicar, encolar definitivo, activar campaña, gastar presupuesto) pasa por:

1. Propuesta (IA u otro origen)
2. Proceso explícito del sistema
3. Aprobación humana cuando aplique

### Principio 3 — Trazabilidad de recomendaciones

Toda recomendación relevante de la IA **deberá poder explicar** en qué parte del contexto se basó.

Ejemplo conceptual:

- Plan activo
- Knowledge Base
- Historial de publicaciones
- Métricas recientes
- Instrucción de sesión del administrador

No es requisito de implementación en Pieza 1. Es **principio de dominio** documentado desde el inicio para auditoría y confianza.

### Principio 4 — El Plan es un activo institucional del Tenant

El Plan **no pertenece a la IA**.

- No se escribe «la IA consume el Plan».
- Se escribe: **el Plan es un activo institucional del Tenant**, dentro del ámbito de una App.
- Consumidores del Plan (sin que el Plan los conozca): Context Builder, asistentes IA, dashboard, reportes, campañas futuras, calendario futuro, automatizaciones, analytics.

El Plan **publica** estrategia. No conoce consumidores.

### Principio 5 — El dominio sobrevive a cualquier proveedor de IA

**Ninguna decisión del modelo de dominio podrá depender de un proveedor específico de IA ni de un modelo concreto.**

Hoy puede ser OpenAI; mañana GPT, Claude o un modelo propio. El dominio (Plan, reglas, eventos, Workspace) funciona igual.

---

## 3. Arquitectura conceptual

### 3.1 Workspace (concepto, no entidad)

El **Workspace** es un **concepto arquitectónico**, no una entidad de dominio, tabla ni JSON dedicado.

Representa el **ámbito operativo de una App** dentro de un Tenant. Hoy existe implícitamente:

```
Tenant
 └── App
      ├── Marketing Plan          (estrategia — esta Pieza 1)
      ├── Knowledge Base
      ├── Content Queue
      ├── Campaigns               (operativo — evolución futura)
      ├── Calendar
      ├── Assets / Flyers
      ├── Leads
      ├── Metrics
      ├── AI Context              (compuesto — ver Context Builder)
      └── Reports                 (futuro)
```

**No crear** entidad `MarketingWorkspace`. Documentar el concepto; materializarlo hoy como `tenant_id` + `app_id` + servicios/carpetas existentes.

El patrón Workspace es **reutilizable** (Sales, Support, HR…) en evolución futura del producto. Esta Pieza 1 define solo el **Plan de marketing** dentro del workspace de marketing de la App.

### 3.2 Marketing Plan (entidad de dominio)

Entidad: **`MarketingPlan`**

Responde una única pregunta:

> **¿Qué estamos intentando lograr en este momento para esta App?**

No coordina el sistema. No es la raíz. Es la **estrategia vigente** (como máximo una activa) dentro del Workspace.

### 3.3 Marketing Context Builder (pieza arquitectónica — no implementar en Pieza 1)

Responsable de **ensamblar** el contexto que consumen IA, dashboard, reportes y automatizaciones.

Orden de composición conceptual:

```
Business Context
→ App Profile / Branding
→ Knowledge Base
→ Marketing Plan (activo, si existe)
→ Campañas (futuro)
→ Cola / historial reciente
→ Métricas / Leads
→ Instrucción de sesión (override táctico del administrador)
→ Contexto entregado al consumidor
```

- El Context Builder **no** es parte del Plan.
- El Plan **no** conoce el Context Builder.
- Múltiples asistentes futuros (Planner, Copywriter, Campaign, Designer, Analytics, Sales) consumirán el **mismo Plan** vía Context Builder.

---

## 4. Modelo de la entidad MarketingPlan

### 4.1 Atributos estructurados (V1.1)

| Atributo | Obligatorio | Descripción |
|----------|-------------|-------------|
| `id` | Sí | Identificador único del plan |
| `tenant_id` | Sí | Tenant propietario (activo institucional) |
| `app_id` | Sí | App de marketing objetivo |
| `nombre` | Sí | Etiqueta humana (ej. «Segundo semestre Payroll 2026») |
| `objetivo_general` | Sí | Intención estratégica en lenguaje natural |
| `strategy_type` | Sí | Tipo de estrategia (enum, ver §4.2) |
| `north_star_metric` | Sí | Métrica norte única (ej. «Generar 50 demos») |
| `success_criteria` | Sí | Metas medibles de éxito (lista o texto estructurado mínimo) |
| `publico_objetivo` | Sí | Audiencia objetivo (V1: texto o lista; evolutivo a Buyer Persona) |
| `marketing_brief` | Sí | Texto largo libre: competencia, propuesta de valor, dolores, canales, mensajes, restricciones, promociones, notas, buyer persona |
| `fecha_inicio` | Sí | Inicio del periodo |
| `fecha_fin` | Sí | Fin del periodo |
| `estado` | Sí | Ciclo de vida (ver §5) |
| `prioridad` | Sí | `alta` · `media` · `baja` |
| `budget` | Sí | Presupuesto (default 0) |
| `currency` | Sí | Moneda (ej. USD, PAB) |
| `observaciones` | No | Notas administrativas breves |
| `created_at` | Sí | Auditoría |
| `updated_at` | Sí | Auditoría |
| `created_by` | Sí | Usuario creador |
| `activated_at` | No | Timestamp al pasar a `activo` |

**Regla de campos:** no agregar campos estructurados para todo lo narrativo. Competencia, propuesta de valor, buyer persona detallado, etc. viven en **`marketing_brief`**.

### 4.2 `strategy_type` (enum V1.1)

- `lead_generation`
- `brand_awareness`
- `remarketing`
- `launch`
- `upselling`
- `cross_selling`
- `retention`

### 4.3 Atributos documentados para evolución (no V1 implementación)

| Atributo | Propósito |
|----------|-----------|
| `version` | Número de versión del plan (Plan v1, v2, v3…) |
| `supersedes_plan_id` | Referencia al plan anterior si aplica |

Permite comparar resultados históricos sin mutar eternamente el mismo registro. Decisión de persistencia en fase posterior.

### 4.4 Lo que el Plan NO contiene

- Publicaciones / posts
- Campañas operativas
- Entradas de calendario
- Flyers / assets
- Prompts, modelos, configuración de IA
- Leads concretos
- Métricas acumuladas
- Instrucciones de ejecución (días, canales, creativos)

---

## 5. Ciclo de vida y estados

| Estado | Significado |
|--------|-------------|
| `borrador` | En elaboración; no orienta la plataforma |
| `activo` | Estrategia vigente para la App |
| `pausado` | Suspendido temporalmente |
| `finalizado` | Cerrado; no reactivable (crear plan nuevo) |

**Sin estados adicionales en V1.1.**

### Transiciones permitidas

| Desde | Hacia |
|-------|-------|
| `borrador` | `activo` |
| `activo` | `pausado`, `finalizado` |
| `pausado` | `activo`, `finalizado` |
| `finalizado` | *(terminal)* |

---

## 6. Reglas de negocio

### R1 — Un Plan activo por App

En `(tenant_id, app_id)` puede existir **como máximo un** plan en estado `activo`.

Pueden coexistir: múltiples `borrador`, `pausado`, `finalizado`.

### R2 — Activación con conflicto

Al activar un plan si ya existe otro `activo` en la misma App:

1. Bloquear activación automática.
2. Preguntar al administrador: **¿Finalizar o pausar el plan activo actual?**
3. Tras resolver, activar el nuevo plan.

### R3 — Plan declarativo

Validación conceptual: el Plan no debe contener verbos ni datos de ejecución operativa (ver Principio 1). Revisión humana al crear/editar.

### R4 — Enfoque principal y cross-selling

- El Plan activo define el **enfoque principal** de propuestas y priorización.
- La IA **puede** recomendar cross-sell/upsell de otras Apps si detecta oportunidad, como **recomendación secundaria**, sin bloquearla arquitectónicamente.
- No confundir con desvío del Plan: debe quedar explícito en la propuesta.

### R5 — Plan vs. instrucción de sesión

- El Plan = estrategia **institucional** persistente.
- Instrucción explícita del administrador en chat = override **táctico** para la sesión actual.
- La instrucción de sesión **no modifica** el Plan salvo acción explícita de «actualizar plan».

### R6 — Periodo válido

Conceptual: `fecha_fin` ≥ `fecha_inicio`. Plan `activo` fuera de periodo: en fase futura, alertar o sugerir pausar/finalizar (sin definir lógica aquí).

### R7 — Permisos

- Crear, editar, activar, pausar, finalizar: **administrador del tenant** (roles equivalentes a `tenant_admin` / permiso `config` o `admin`).
- Consultar plan activo: operadores de marketing (lectura).

### R8 — El Plan no ejecuta

Ninguna transición de estado del Plan dispara publicación, encolado, gasto publicitario ni cambio en conectores.

### R9 — Agnosticismo de IA

El schema del Plan no incluye campos de proveedor, modelo, prompt ni consumidor.

---

## 7. Relaciones conceptuales (sin modificar entidades existentes)

| Entidad existente | Relación | Pieza 1 |
|-------------------|----------|---------|
| **Tenant** | Plan ∈ Tenant | Directa |
| **App** | Plan ∈ App | Directa |
| **Knowledge Base** | Paralela; KB = producto, Plan = enfoque temporal | Sin enlace |
| **Publicaciones / Cola** | Futuro: `plan_id` opcional en post | Sin enlace |
| **Campañas** | Futuro: campaña ∈ plan | Sin enlace |
| **Calendario** | Futuro: actividades dentro del periodo del plan | Sin enlace |
| **Conectores** | Sin relación | — |
| **Leads** | Futuro: atribución al plan activo | Sin enlace |
| **Métricas** | Futuro: comparar real vs. `success_criteria` / north star | Sin enlace |
| **IA / Asistentes** | Consumen Plan vía Context Builder | Sin enlace |

**Contrato futuro:** entidades operativas del Workspace podrán llevar **`plan_id`** cuando nazca cada pieza. Posts existentes permanecen sin `plan_id` hasta migración explícita (GO aparte).

---

## 8. Eventos de dominio (documentados — no implementar)

| Evento | Cuándo |
|--------|--------|
| `PlanCreated` | Plan registrado en `borrador` |
| `PlanActivated` | Pasa a `activo` (puede implicar resolución R2) |
| `PlanPaused` | Pasa a `pausado` desde `activo` |
| `PlanCompleted` | Pasa a `finalizado` |

Eventos para auditoría, métricas y automatizaciones futuras. El Plan emite eventos; no conoce sus suscriptores.

---

## 9. Reutilización del sistema actual (sin cambios)

| Componente | Rol respecto al Plan |
|------------|----------------------|
| Tenant + registry | Contenedor institucional |
| Apps + paths por `app_id` | Ámbito del Workspace implícito |
| Knowledge Base | Input del Context Builder |
| Cola / publicaciones | Operación; futuro `plan_id` |
| Estados editoriales de posts | Independientes del ciclo de vida del Plan |
| Conectores / publishers | Ejecución; agnósticos al Plan |
| Asistente IA V1 | Antecedente parcial de Context Builder |
| RBAC / auth | Permisos sobre el Plan |
| Leads / métricas | Futura atribución al plan |

---

## 10. Componentes nuevos (fases posteriores — enumeración)

1. Persistencia del MarketingPlan (convención por App)
2. Validaciones de dominio (R1–R9, declarative check)
3. Servicio de dominio (CRUD + transiciones + R2)
4. Emisión de eventos de dominio
5. API REST del Plan
6. UI del Plan en dashboard
7. **Marketing Context Builder** (formal)
8. Integración Context Builder ↔ asistentes IA
9. Campo `plan_id` en publicaciones, campañas, leads, métricas
10. Trazabilidad de recomendaciones IA (Principio 3)
11. Versionado explícito de planes (`version`, `supersedes_plan_id`)

**Orden obligatorio post-aprobación:**

1. ~~Especificación v1.1 (este documento)~~
2. Revisión y aprobación final
3. Schema del dominio
4. Servicio de dominio
5. API
6. UI
7. Integración con IA
8. Automatizaciones

---

## 11. Flujo conceptual del sistema

```
Administrador del Tenant
        │
        ▼
Define intención estratégica (MarketingPlan en borrador)
        │
        ▼
Aprueba → Plan pasa a ACTIVO (R1, R2)
        │
        ▼
Context Builder ensambla contexto (Plan + KB + perfil + …)
        │
        ▼
IA y otros consumidores proponen (nunca ejecutan solos)
        │
        ▼
Administrador aprueba propuestas operativas
        │
        ▼
Sistema ejecuta (cola, conectores, campañas futuras)
        │
        ▼
Métricas y leads se comparan con north star y success criteria
        │
        ▼
IA analiza y propone ajustes (trazables — Principio 3)
        │
        ▼
Administrador: continuar, pausar o finalizar el Plan
```

Pieza 1 cubre **solo la definición del MarketingPlan y sus reglas**. El flujo completo se implementa en piezas sucesivas.

---

## 12. Criterio de aprobación de este documento

**Estado: APROBADO** (2026-06-28).

- [x] Principios 1–5 aceptados
- [x] Modelo de atributos §4.1 aceptado (campos estructurados + `marketing_brief`)
- [x] Workspace como concepto (sin entidad) aceptado
- [x] Context Builder documentado como pieza futura
- [x] Reglas R1–R9 aceptadas
- [x] Eventos de dominio §8 aceptados
- [x] Gobernanza: dominio congelado; implementaciones se adaptan al dominio

**Siguiente acción autorizada:** Pieza 2 — Schema del Dominio (`docs/MARKETING_PLAN_DOMAIN_SCHEMA_v1.md`). Sin código hasta aprobación del schema.

---

## 13. Referencias

- Schema del dominio (Pieza 2): [`MARKETING_PLAN_DOMAIN_SCHEMA_v1.md`](MARKETING_PLAN_DOMAIN_SCHEMA_v1.md)
- Servicio de dominio (Pieza 3 diseño): [`MARKETING_PLAN_DOMAIN_SERVICE.md`](MARKETING_PLAN_DOMAIN_SERVICE.md)
- Inventario verificable: conversación Acción 1 (dashboard, tenant, apps, IA, estados, APIs)
- Arquitectura tenant/app: `docs/EMACCION_TENANT_VS_APP.md`
- Contexto operativo: `docs/EMACCION_CONTEXTO_OPERATIVO.md`

---

*Documento fundacional del dominio de marketing — EM+Acción · Pieza 1 v1.1*
