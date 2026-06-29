# SPRINT 1 — Modelo del Dominio (Domain Model)

## EM+Acción Marketing Operating System

**Estado:** 📋 **GO** — sprint activo  
**Precede:** [MARKETING_OS_DOMAIN_SPRINT0.md](MARKETING_OS_DOMAIN_SPRINT0.md) · [ADR-0001](adr/0001-marketing-os-domain-sprint0.md)  
**North star:** [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md)

---

## Objetivo

Definir el **modelo de negocio** del Marketing OS antes de continuar con funcionalidades.

**No** desarrollar pantallas ni lógica de negocio compleja. Definir correctamente entidades, relaciones y responsabilidades.

---

## Objetivos del Sprint

Al finalizar debe existir un **modelo de dominio estable** que represente cómo funciona una empresa desde la perspectiva del marketing.

---

# 1. Catálogo de Entidades

Para cada entidad documentar: nombre, descripción, responsabilidad, propietario, relaciones, campos principales, estado, eventos relevantes.

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)

### Organización

Tenant · Empresa · Marca · Usuario · Rol · Equipo

### Conocimiento

CompanyBrain · CorporateMemory · KnowledgeArticle · ProductKnowledge · FAQ · Competitor · CaseStudy

### Branding

Brand · BrandGuide · Logo · ColorPalette · Typography · Template

### Activos

Asset · Image · Video · PDF · Flyer · Presentation · LandingAsset

### Productos

Product · ProductCategory · Promotion · Offer · CTA

### Marketing

Campaign · CampaignObjective · CampaignStage · Channel · Content · Publication · EditorialCalendar

### Comercial

Lead · Opportunity · Customer · Contact · SalesPipeline

### Automatización

Workflow · Trigger · Action · Approval · Task · Scheduler

### Analítica

KPI · Metric · ROI · Insight · Experiment · Recommendation

---

# 2. Relaciones

Cadena principal:

```
Tenant → Empresa → Marca → Producto → Campaña → Contenido → Resultados → Corporate Memory
```

Cada relación documentada en [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Relaciones.

---

# 3. Ciclo del Marketing OS

Matriz entidad × fase (Observar · Analizar · Planificar · Crear · Ejecutar · Medir · Aprender).

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Ciclo.

---

# 4. Eventos del Dominio

**Entregable:** [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md)

Ejemplos: Lead creado · Campaña aprobada · Campaña publicada · Flyer generado · Comentario recibido · Cliente convertido · Contenido rechazado · Nuevo caso de éxito · Cambio de branding · Producto actualizado.

Todo evento alimenta **Corporate Memory**.

---

# 5. Ownership

Por entidad: quién crea · modifica · aprueba · consume · aprende.

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Ownership.

---

# 6. Estados

Ciclo de vida por agregado (ej. Campaña: Borrador → En revisión → Aprobada → Programada → Publicada → Finalizada → Archivada).

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Estados.

---

# 7. Auditoría

Registrar: usuario · fecha · acción · resultado · motivo · origen → Corporate Memory.

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Auditoría.

---

# 8. APIs del Dominio

Solo contratos — **no implementar**.

**Entregable:** [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md)

CampaignService · KnowledgeService · AssetService · RoadmapService · RecommendationService · AutomationService · CorporateMemoryService · …

---

# 9. Base de Datos

Esquema conceptual — consistencia, no optimización.

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Persistencia.

---

# 10. Reglas de Negocio

**Entregable:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) § Reglas.

---

# Entregables Sprint 1

| # | Documento | Estado |
|---|-----------|--------|
| 1 | [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) | 🔄 v0.1 |
| 2 | Diagrama ER (en domain model) | 🔄 |
| 3 | [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md) | 🔄 v0.1 |
| 4 | [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md) | 🔄 v0.1 |
| 5 | [MARKETING_OS_GLOSSARY.md](MARKETING_OS_GLOSSARY.md) | 🔄 v0.1 |
| 6 | ADR actualizado si aplica | ⏳ |

---

# Restricciones

- ❌ No crear nuevas pantallas
- ❌ No implementar IA
- ❌ No desarrollar automatizaciones
- ❌ No modificar interfaz actual
- ❌ No cambiar funcionalidades existentes

---

# Criterio de aceptación

Cualquier desarrollador nuevo comprende el dominio **solo leyendo la documentación**, sin revisar código.

Debe responder:

1. ¿Cuáles son las entidades?
2. ¿Cómo se relacionan?
3. ¿Dónde vive el conocimiento vs la memoria?
4. ¿Cómo fluye una recomendación de Observar a Aprender?

---

# Regla del Sprint

**Prohibido** crear funcionalidades nuevas sin entidad de dominio que las represente.

> El dominio gobierna el producto; el código implementa el dominio.

**Framework operativo (5 preguntas):** [MARKETING_OS_DEV_FRAMEWORK.md](MARKETING_OS_DEV_FRAMEWORK.md)

1. ¿A qué **pilar** pertenece?
2. ¿Qué **entidad** del dominio afecta?
3. ¿Qué **evento** genera?
4. ¿Qué registra en **Corporate Memory**?
5. ¿Cómo ayuda a **vender más**?

---

## Secuencia de sprints

| Sprint | Foco |
|--------|------|
| **0** | Arquitectura del dominio (ADR, alcance) — ✅ spec |
| **1** | Modelo del dominio ← *activo* |
| **2+** | Implementación por pilares (post-cierre Sprint 1) |
