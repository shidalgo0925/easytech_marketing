# Marketing OS — Persistencia conceptual

**Versión:** 0.1 (borrador Sprint 1)  
**Estado:** 🔄 Entregable Sprint 1 — completar hacia v1.0  
**Domain Model:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)  
**Constitución:** [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md) (Principios 9, 12, 16)

> Esquema lógico — **no optimizar** en Sprint 1. Asegurar consistencia y multi-tenant.

---

## Principios de persistencia

1. **`tenant_id`** en toda fila persistente
2. **`brand_id`** en entidades de marketing (≈ `app_id` legacy)
3. **Corporate Memory** append-only — no DELETE, solo archive flag
4. **Conocimiento exportable** (Principio 16) — schema documentado, sin lock-in opaco
5. **Empresa Viva** — `valid_from`, `source`, `last_synced_at` en entidades de conocimiento

---

## Agregados core (borrador)

| Agregado | Persistencia propuesta | Notas |
|----------|------------------------|-------|
| Tenant | `tenants` | registry existente evoluciona |
| Marca (Brand) | `brands` | mapping desde `apps/registry` |
| CompanyBrain | `company_profiles` | JSON estructurado o columnas |
| CorporateMemory | `memory_events` | append-only, index by entity |
| ProductKnowledge | `product_knowledge` + sections | por brand/product |
| BrandCenter | `brand_assets`, `brand_guidelines` | |
| Asset | `media_assets` + metadata JSON | |
| Campaign | `campaigns` | existe parcialmente |
| Publication | `publications` | evolución content_queue |
| Recommendation | `recommendations` + `daily_roadmaps` | nuevo |
| Lead / Customer | `leads`, `customers` | |
| Approval | `approvals` | audit trail |
| Metric / ROI | `metrics`, `roi_assessments` | |

---

## Relaciones lógicas (FK)

```
tenants 1──N brands 1──N products 1──N campaigns 1──N publications
tenants 1──N memory_events
brands 1──1 company_profiles (o tenant-level)
brands 1──N product_knowledge
publications 1──N metrics
recommendations N──1 daily_roadmaps
```

*Completar cardinalidad y ON DELETE rules en v1.0.*

---

## Mapping legacy → objetivo

| Legacy | Tabla/agregado objetivo |
|--------|-------------------------|
| `Marketing/tenants/{id}/` | tenant scope |
| `apps/{app_id}/` | brand scope |
| `business_context.json` | `company_profiles` |
| `content_queue.json` posts | `publications` |
| `assistant_audit.jsonl` | `memory_events` |
| `marketing_plans/*.json` | subdominio Plan (sin mezclar ops) |

---

## Índices lógicos (sin motor)

- `memory_events(tenant_id, event_type, timestamp)`
- `memory_events(entity_type, entity_id)`
- `publications(tenant_id, brand_id, status)`
- `recommendations(tenant_id, status, assignee)`

---

## Pendiente Sprint 1

- [ ] DDL conceptual completo por entidad
- [ ] Decisión JSON files vs SQLite vs Postgres (ADR-0002)
- [ ] Estrategia migración legacy sin downtime
- [ ] Revisión alineada a Domain Model v1.0

---

## Referencias

- [MARKETING_OS_SPRINT1_DOMAIN_MODEL.md](MARKETING_OS_SPRINT1_DOMAIN_MODEL.md)
- [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md)
