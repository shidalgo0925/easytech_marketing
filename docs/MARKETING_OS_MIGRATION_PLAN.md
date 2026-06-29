# Marketing OS — Plan de migración legacy → plataforma

**Versión:** 1.0 · Sprint 2  
**Arquitectura:** [MARKETING_OS_ARCHITECTURE.md](MARKETING_OS_ARCHITECTURE.md)  
**Persistencia:** [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md) · [ADR-0002](adr/0002-marketing-os-persistence-store.md)

> Migración **por agregado**, sin downtime. Dual-read/dual-write solo donde se documente.

---

## Principios

1. **Strangler fig** — nuevo código en capas; legacy se delega desde adapters hasta retirar ruta.
2. **Tenant primero** — toda migración valida aislamiento `tenant_id`.
3. **Memory primero** — Corporate Memory habilita trazabilidad del resto.
4. **Sin big-bang** — cada fase tiene criterio de cierre y rollback (seguir leyendo JSON).

---

## Fases de migración

| Fase | Agregado | Legacy | Objetivo | Criterio cierre |
|------|----------|--------|----------|-----------------|
| **M0** | — | — | Infra: `marketing_os.db`, módulo `platform_infrastructure/` | DB creada; tests smoke |
| **M1** | CorporateMemory | `assistant_audit.jsonl` | `memory_events` + `CorporateMemoryService` | Nuevos eventos en DB; audit JSON append paralelo opcional |
| **M2** | CompanyBrain | `business_context.json` | `company_profiles` | API lee Brain desde repo; JSON sync export |
| **M3** | Brand | `apps/registry.json` | `brands` + `legacy_app_id` | Registry ↔ brands bidireccional |
| **M4** | Publication | `content_queue.json` | `publications` | Cola nueva escribe DB; publisher lee DB o JSON (flag) |
| **M5** | Product | `products.json` | `products` | KB y campañas referencian product_id |
| **M6** | ProductKnowledge | `knowledge/*.md` | `knowledge_articles` | Import por slug |
| **M7** | Campaign | `campaigns.json` | `campaigns` | Vinculado a publications |
| **M8** | MediaAsset | `flyers/` | `media_assets` | Manifest flyers → assets |
| **M9** | Lead | `leads.json` | `leads` | Dashboard métricas desde DB |
| **M10** | Recommendation | — (nuevo) | `recommendations` | Roadmap Engine V1 |
| **M11** | MarketingPlan | `marketing_plans/*.json` | Mantener JSON o tabla dedicada | Decisión en M11 — dominio congelado |

**Orden obligatorio M1→M2→M3** antes de M4 (publications necesitan brand scope). M4–M9 pueden solaparse por pilar con GO explícito.

---

## Detalle por fase

### M1 — Corporate Memory

```
assistant_service / executor / marketing_plan events
        → DomainEventPublisher
        → SqliteMemoryRepository.append()
        → (opcional) seguir escribiendo assistant_audit.jsonl 90 días
```

**Script:** `scripts/migrate_audit_to_memory.py` — import histórico jsonl → `memory_events`.

### M2 — Company Brain

```
business_context.json  →  CompanyBrainMapper  →  company_profiles
```

Lectura: `KnowledgeService.getCompanyBrain` → adapter elige JSON o SQL según `ACCIO_BRAIN_STORE=sql|json`.

### M3 — Brands

```
apps/registry.json  →  brands (brand_id = slug, legacy_app_id = app_id)
```

`marketing_app.get_app()` delega a `BrandRepository.resolve(legacy_app_id)`.

### M4 — Publications

```
content_queue posts  →  publications
legacy_queue_id      →  id post cola original
```

Publisher (`executor.py`) migra último: lee `PublicationRepository.list_scheduled()`.

### M5–M9

Import one-shot + dual-write en comandos de aplicación. Sin eliminar JSON hasta flag `ACCIO_LEGACY_JSON=false` por tenant.

---

## Flags de entorno (propuestos)

| Variable | Valores | Default |
|----------|---------|---------|
| `ACCIO_PLATFORM_DB` | path SQLite | `Marketing/platform/marketing_os.db` |
| `ACCIO_MEMORY_STORE` | jsonl \| sql \| dual | jsonl |
| `ACCIO_BRAIN_STORE` | json \| sql | json |
| `ACCIO_PUBLICATION_STORE` | json \| sql \| dual | json |
| `ACCIO_LEGACY_JSON` | true \| false | true |

---

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Regresión publisher LinkedIn | M4 dual-read; tests integración cola |
| Pérdida audit histórico | M1 import + no DELETE memory_events |
| `app.py` monolito | Nuevas rutas solo en `*_api/routes.py` |
| Plan v1.1 roto | M11 fuera de scope hasta dominio Plan abra v1.2 |

---

## Referencias

- [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md)
- [MARKETING_PLAN_JSON_ADAPTER.md](MARKETING_PLAN_JSON_ADAPTER.md)
