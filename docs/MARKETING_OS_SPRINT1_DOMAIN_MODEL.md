# SPRINT 1 — Domain Model + Persistencia Conceptual

## EM+Acción Marketing OS — sprint 100% técnico

**Estado:** 📋 GO activo  
**Pre-requisito:** [Constitución v1.0](MARKETING_OS_CONSTITUTION.md) commiteada  
**Visión (referencia):** [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md) — **no modificar**  
**Precede técnico:** [Sprint 0](MARKETING_OS_DOMAIN_SPRINT0.md) · [ADR-0001](adr/0001-marketing-os-domain-sprint0.md)

---

## Objetivo

Diseñar el **Domain Model v1.0** y la **base de datos conceptual** del Marketing OS.

Este es el punto donde la **visión se convierte en plataforma real**.

**No:**

- Documentos conceptuales nuevos
- Redefinir el producto
- Pantallas, IA, automatizaciones, código

**Sí:**

- Entidades completas (campos, estados, eventos, ownership)
- ER con cardinalidad
- Esquema conceptual de persistencia
- Contratos de servicios de dominio
- Criterios de aceptación verificables

---

## Entregables verificables

| # | Entregable | Archivo | Done cuando… |
|---|------------|---------|--------------|
| 1 | Domain Model v1.0 | [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) | Catálogo completo §1 Sprint 0 |
| 2 | Diagrama ER | Domain Model §2 | Cardinalidad aprobada |
| 3 | Eventos v1.0 | [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md) | Cada evento con envelope Memory |
| 4 | Servicios dominio | [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md) | Ops por agregado core |
| 5 | **BD conceptual** | [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md) | Tablas, FKs, tenant_id, índices lógicos |
| 6 | Glosario v1.0 | [MARKETING_OS_GLOSSARY.md](MARKETING_OS_GLOSSARY.md) | 1:1 término ↔ entidad |
| 7 | Matriz ciclo × entidad | Domain Model §3 | Completa |
| 8 | Reglas de negocio v1.0 | Domain Model §8 | Alineadas a Constitución |

---

## Alcance BD conceptual

- Agregados y tablas lógicas (no optimizar aún)
- `tenant_id` obligatorio; `brand_id` donde aplique
- Corporate Memory: append-only (`memory_events`)
- Mapping legacy → tablas objetivo (`app_id` → `brand_id`)
- Convivencia `MarketingPlan` v1.1 (tabla/subdominio separado)
- **Sin** elegir motor definitivo si bloquea diseño — documentar opciones

---

## Criterio de aceptación

Un desarrollador nuevo, **solo con documentación**, responde:

1. ¿Cuáles son las entidades del Marketing OS?
2. ¿Cómo se relacionan?
3. ¿Dónde se almacena el conocimiento vs la memoria?
4. ¿Cómo fluye una recomendación de Observar a Aprender?
5. ¿Qué tablas/agregados persisten cada entidad core?
6. ¿Cómo se aísla multi-tenant?

**Si no puede → Sprint 1 no cerrado.**

---

## Regla del sprint

- **Prohibido** feature sin entidad documentada ([Constitución](MARKETING_OS_CONSTITUTION.md) Principio 19).
- **Prohibido** nuevo documento de visión o producto.
- Cada PR de doc debe incrementar versión **v0.x → v1.0** con checklist.

---

## Secuencia post Sprint 1

| Sprint | Entregable |
|--------|------------|
| **1** | Domain Model + BD conceptual ← *ahora* |
| **2** | Arquitectura de implementación (capas, APIs, adapters) |
| **3+** | Implementación por pilares (Company Brain, Memory, …) |

---

## Referencias

- [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md)
- [ROADMAP.md](ROADMAP.md)
