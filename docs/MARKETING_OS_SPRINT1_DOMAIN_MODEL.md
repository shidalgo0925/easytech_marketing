# SPRINT 1 — Domain Model + Persistencia Conceptual

## EM+Acción Marketing OS — sprint 100% técnico

**Estado:** ✅ **Cerrado** (2026-06-26)  
**Pre-requisito:** [Constitución v1.0](MARKETING_OS_CONSTITUTION.md) ✅  
**Visión (referencia):** [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md) — **no modificar**  
**Precede técnico:** [Sprint 0](MARKETING_OS_DOMAIN_SPRINT0.md) · [ADR-0001](adr/0001-marketing-os-domain-sprint0.md)

---

## Objetivo

Diseñar el **Domain Model v1.0** y la **base de datos conceptual** del Marketing OS.

Este es el punto donde la **visión se convierte en plataforma real**.

---

## Entregables — checklist

| # | Entregable | Archivo | Estado |
|---|------------|---------|--------|
| 1 | Domain Model v1.0 | [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) | ✅ |
| 2 | Diagrama ER + cardinalidad | Domain Model §2 | ✅ |
| 3 | Eventos v1.0 + envelope | [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md) | ✅ |
| 4 | Servicios dominio v1.0 | [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md) | ✅ |
| 5 | BD conceptual + DDL | [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md) | ✅ |
| 6 | ADR persistencia | [adr/0002-marketing-os-persistence-store.md](adr/0002-marketing-os-persistence-store.md) | ✅ |
| 7 | Glosario v1.0 | [MARKETING_OS_GLOSSARY.md](MARKETING_OS_GLOSSARY.md) | ✅ |
| 8 | Matriz ciclo × entidad | Domain Model §3 | ✅ |
| 9 | Ownership completa | Domain Model §4 | ✅ |
| 10 | Reglas de negocio | Domain Model §9 | ✅ |
| 11 | Flujo recomendación | Domain Model §8 | ✅ |
| 12 | Código · UI · IA | — | ❌ Prohibido (correcto) |

---

## Criterio de aceptación — verificado

| # | Pregunta | Dónde responder |
|---|----------|-----------------|
| 1 | ¿Entidades del Marketing OS? | Domain Model §1 |
| 2 | ¿Relaciones? | Domain Model §2 |
| 3 | ¿Conocimiento vs memoria? | Domain Model §7 |
| 4 | ¿Flujo recomendación Observar→Aprender? | Domain Model §8 |
| 5 | ¿Tablas por entidad? | DOMAIN_PERSISTENCE DDL |
| 6 | ¿Multi-tenant? | `tenant_id` + Domain Model §9.10 |

---

## Siguiente: Sprint 2 — Arquitectura

Capa 4 de la jerarquía documental:

- Capas aplicación / dominio / infra
- Adapters legacy JSON → repositorios
- APIs REST v2 propuestas
- Estrategia migración por agregado
- **Después** de Arquitectura aprobada → código pilares (Sprint 3+)

---

## Referencias

- [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md)
- [ROADMAP.md](ROADMAP.md)
