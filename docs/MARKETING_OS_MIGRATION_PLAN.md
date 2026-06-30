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
| **—** | *Fin capa conocimiento* | — | — | M0–M9 completos |
| **M10** | **Decision Engine** | — (nuevo) | `daily_roadmaps` + `recommendations` | Roadmap diario + aprobación; **reglas, sin IA** |
| **M11** | Marketing Brain | — | — | IA enriquece Decision Engine; no reemplaza estructura |
| **M12** | Business Intelligence | — | — | Analytics + BI gerencial; alimenta Brain |
| **M13** | Automation Brain | — | — | Ejecuta acciones post-aprobación |

**Orden obligatorio M1→M2→M3** antes de M4 (publications necesitan brand scope). M4–M9 cierran conocimiento. **M10+ = decisiones.**

**Prioridad de mercado (Plan Maestro v3):** M10.5 → AI Provider → M11 → Opportunity → … → M12 → M13. Ver [EMACCION_PLAN_MAESTRO_v3.md](EMACCION_PLAN_MAESTRO_v3.md).

### Gate post-M9

Antes de cualquier tabla o módulo nuevo:

> ¿Almacena **conocimiento** o registra/toma una **decisión**?

Si es conocimiento → no iniciar (capa M0–M9 cerrada). Si es decisión → Decision Engine M10+.

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

### M10 — Decision Engine (no es migración legacy)

Ver [MARKETING_OS_SPRINT12_DECISION_ENGINE.md](MARKETING_OS_SPRINT12_DECISION_ENGINE.md).

```
KnowledgeSnapshot (M1–M9 repos)
        → Roadmap Builder (reglas)
        → Priority Engine
        → Recommendation + DailyRoadmap (persist)
        → Approval Queue → Memory events
        → (futuro) Automation Engine
```

Sub-fases: M10.1 Builder → M10.2 Priority → M10.3 Recommendation → M10.4 Daily Planner → M10.5 Approval.

**Caso piloto:** `brand_publication_gap` en easytech / en1.

### M11 — Marketing Brain

IA sobre salida M10. MarketingPlan v1.1 sigue congelado; Brain lee, no muta.

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
| M10 parece “otra tabla” | Gate conocimiento vs decisión; spec Sprint 12 |

---

## Referencias

- [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md)
- [MARKETING_PLAN_JSON_ADAPTER.md](MARKETING_PLAN_JSON_ADAPTER.md)
