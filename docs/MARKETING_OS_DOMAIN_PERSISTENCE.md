# Marketing OS — Persistencia conceptual

**Versión:** 1.0 · Sprint 1 cerrado  
**Estado:** ✅ Aprobado — implementar solo post-Arquitectura (capa 4)  
**Domain Model:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)  
**ADR motor:** [adr/0002-marketing-os-persistence-store.md](adr/0002-marketing-os-persistence-store.md)  
**Constitución:** Principios 9, 12, 16

> Esquema lógico portable SQLite → PostgreSQL. No optimizar índices físicos en esta fase.

---

## Principios

1. **`tenant_id`** NOT NULL en toda fila
2. **`brand_id`** en entidades de marketing (≈ `app_id` legacy)
3. **`memory_events`** append-only — sin DELETE
4. Conocimiento exportable — columnas documentadas, JSON en `payload` solo para extensiones
5. **Empresa Viva:** `valid_from`, `source`, `last_synced_at` en tablas de conocimiento

---

## Diagrama lógico

```
tenants
  ├── companies
  │     ├── company_profiles (1:1 CompanyBrain)
  │     └── brands
  │           ├── brand_guidelines
  │           ├── products
  │           ├── product_knowledge
  │           ├── campaigns
  │           │     └── publications → metrics
  │           ├── media_assets
  │           └── recommendations → daily_roadmaps
  ├── memory_events (tenant + optional brand)
  ├── leads / customers / opportunities
  └── approvals
```

---

## DDL conceptual

Tipos: `TEXT` para IDs y enums; `JSON` para blobs estructurados; timestamps ISO-8601 UTC.

### Organización

```sql
-- tenants: registry SaaS (evolución de registry.json)
CREATE TABLE tenants (
  tenant_id       TEXT PRIMARY KEY,
  display_name    TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'active',  -- active|suspended|provisioning
  settings_json   JSON,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

-- companies: organización operativa (1:1 con tenant en PYME común)
CREATE TABLE companies (
  company_id      TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  legal_name      TEXT,
  country         TEXT,
  timezone        TEXT DEFAULT 'America/Panama',
  status          TEXT NOT NULL DEFAULT 'active',  -- active|archived
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  UNIQUE (tenant_id, company_id)
);

-- brands: ≈ app_id legacy
CREATE TABLE brands (
  brand_id        TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  company_id      TEXT NOT NULL REFERENCES companies(company_id),
  slug            TEXT NOT NULL,
  name            TEXT NOT NULL,
  tone            TEXT,
  target_audience TEXT,
  status          TEXT NOT NULL DEFAULT 'active',  -- active|paused|archived
  legacy_app_id   TEXT,  -- mapping apps/{app_id}
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  UNIQUE (tenant_id, slug)
);

-- users: identidad; auth en auth.db hoy — unificar en capa 4
CREATE TABLE users (
  user_id         TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  email           TEXT NOT NULL,
  display_name    TEXT,
  status          TEXT NOT NULL DEFAULT 'active',
  created_at      TEXT NOT NULL,
  UNIQUE (tenant_id, email)
);

CREATE TABLE roles (
  role_id         TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  name            TEXT NOT NULL,  -- director|marketing|sales|community|designer
  permissions_json JSON NOT NULL
);

CREATE TABLE user_roles (
  user_id         TEXT NOT NULL REFERENCES users(user_id),
  role_id         TEXT NOT NULL REFERENCES roles(role_id),
  PRIMARY KEY (user_id, role_id)
);
```

### Conocimiento

```sql
CREATE TABLE company_profiles (
  company_id      TEXT PRIMARY KEY REFERENCES companies(company_id),
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  history         TEXT,
  mission         TEXT,
  vision          TEXT,
  values_json     JSON,
  market_json     JSON,
  competitors_json JSON,
  branches_json   JSON,
  team_json       JSON,
  objectives_json JSON,
  status          TEXT NOT NULL DEFAULT 'draft',  -- draft|published
  valid_from      TEXT,
  source          TEXT,
  last_synced_at  TEXT,
  updated_at      TEXT NOT NULL
);

-- memory_events: Corporate Memory — APPEND ONLY
CREATE TABLE memory_events (
  event_id        TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  brand_id        TEXT REFERENCES brands(brand_id),
  event_type      TEXT NOT NULL,
  actor_type      TEXT NOT NULL,  -- user|system
  actor_id        TEXT,
  timestamp       TEXT NOT NULL,
  entity_refs_json JSON NOT NULL,  -- [{type,id}]
  payload_json    JSON,
  summary         TEXT,
  correlation_id  TEXT
);
-- PROHIBIDO: DELETE FROM memory_events

CREATE TABLE product_knowledge (
  knowledge_id    TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  brand_id        TEXT NOT NULL REFERENCES brands(brand_id),
  product_id      TEXT,
  title           TEXT NOT NULL,
  body_markdown   TEXT,
  status          TEXT NOT NULL DEFAULT 'draft',
  valid_from      TEXT,
  source          TEXT,
  last_synced_at  TEXT,
  updated_at      TEXT NOT NULL
);

CREATE TABLE knowledge_articles (
  article_id      TEXT PRIMARY KEY,
  knowledge_id    TEXT NOT NULL REFERENCES product_knowledge(knowledge_id),
  tenant_id       TEXT NOT NULL,
  slug            TEXT NOT NULL,
  title           TEXT NOT NULL,
  content_md      TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'draft',
  published_at    TEXT,
  UNIQUE (tenant_id, slug)
);

CREATE TABLE faqs (
  faq_id          TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  product_id      TEXT,
  question        TEXT NOT NULL,
  answer          TEXT NOT NULL,
  sort_order      INTEGER DEFAULT 0
);

CREATE TABLE competitors (
  competitor_id   TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  name            TEXT NOT NULL,
  intel_json      JSON,
  valid_from      TEXT,
  last_synced_at  TEXT
);

CREATE TABLE case_studies (
  case_id         TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  product_id      TEXT,
  title           TEXT NOT NULL,
  metrics_json    JSON,
  cta             TEXT,
  status          TEXT NOT NULL DEFAULT 'draft'
);
```

### Brand Center

```sql
CREATE TABLE brand_guidelines (
  brand_id        TEXT PRIMARY KEY REFERENCES brands(brand_id),
  tenant_id       TEXT NOT NULL,
  manual_md       TEXT,
  logo_uri        TEXT,
  colors_json     JSON,
  typography_json JSON,
  templates_json  JSON,
  valid_from      TEXT,
  last_synced_at  TEXT,
  updated_at      TEXT NOT NULL
);
```

### Activos y productos

```sql
CREATE TABLE products (
  product_id      TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  brand_id        TEXT NOT NULL REFERENCES brands(brand_id),
  slug            TEXT NOT NULL,
  name            TEXT NOT NULL,
  category_id     TEXT,
  description     TEXT,
  status          TEXT NOT NULL DEFAULT 'active',
  UNIQUE (tenant_id, brand_id, slug)
);

CREATE TABLE product_categories (
  category_id     TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  name            TEXT NOT NULL
);

CREATE TABLE media_assets (
  asset_id        TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  product_id      TEXT REFERENCES products(product_id),
  campaign_id     TEXT,
  asset_type      TEXT NOT NULL,  -- image|video|pdf|flyer|presentation|landing
  uri             TEXT NOT NULL,
  language        TEXT DEFAULT 'es',
  author_id       TEXT,
  version         INTEGER DEFAULT 1,
  status          TEXT NOT NULL DEFAULT 'draft',
  tags_json       JSON,
  channel         TEXT,
  created_at      TEXT NOT NULL
);

CREATE TABLE promotions (
  promotion_id    TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  product_id      TEXT NOT NULL,
  name            TEXT NOT NULL,
  starts_at       TEXT,
  ends_at         TEXT,
  status          TEXT NOT NULL DEFAULT 'scheduled'
);

CREATE TABLE offers (
  offer_id        TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  product_id      TEXT NOT NULL,
  price           TEXT,
  currency        TEXT DEFAULT 'USD',
  cta_text        TEXT,
  valid_from      TEXT
);
```

### Marketing

```sql
CREATE TABLE campaigns (
  campaign_id     TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL REFERENCES tenants(tenant_id),
  brand_id        TEXT NOT NULL REFERENCES brands(brand_id),
  product_id      TEXT REFERENCES products(product_id),
  name            TEXT NOT NULL,
  objective       TEXT,
  channel         TEXT,
  budget          REAL,
  start_at        TEXT,
  end_at          TEXT,
  status          TEXT NOT NULL DEFAULT 'draft',
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

CREATE TABLE publications (
  publication_id  TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  campaign_id     TEXT REFERENCES campaigns(campaign_id),
  product_id      TEXT,
  channel         TEXT NOT NULL,
  title           TEXT,
  body            TEXT,
  flyer_asset_id  TEXT REFERENCES media_assets(asset_id),
  scheduled_at    TEXT,
  published_at    TEXT,
  external_post_id TEXT,
  status          TEXT NOT NULL DEFAULT 'draft',
  legacy_queue_id TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

CREATE TABLE editorial_calendars (
  calendar_id     TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  period_start    TEXT NOT NULL,
  period_end      TEXT NOT NULL,
  entries_json    JSON
);
```

### Comercial

```sql
CREATE TABLE leads (
  lead_id         TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT,
  source          TEXT,
  contact_json    JSON,
  status          TEXT NOT NULL DEFAULT 'new',
  assigned_to     TEXT,
  created_at      TEXT NOT NULL
);

CREATE TABLE customers (
  customer_id     TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  lead_id         TEXT REFERENCES leads(lead_id),
  name            TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'active',
  converted_at    TEXT
);

CREATE TABLE opportunities (
  opportunity_id  TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT,
  lead_id         TEXT,
  stage           TEXT NOT NULL,
  value           REAL,
  status          TEXT NOT NULL DEFAULT 'open'
);
```

### Roadmap y analítica

```sql
CREATE TABLE daily_roadmaps (
  roadmap_id      TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  company_id      TEXT NOT NULL,
  roadmap_date    TEXT NOT NULL,
  generated_at    TEXT NOT NULL,
  UNIQUE (tenant_id, company_id, roadmap_date)
);

CREATE TABLE recommendations (
  recommendation_id TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  roadmap_id      TEXT REFERENCES daily_roadmaps(roadmap_id),
  action          TEXT NOT NULL,
  assignee_role   TEXT NOT NULL,
  priority        TEXT NOT NULL,  -- high|medium|low
  expected_impact TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',
  dependencies_json JSON,
  justification_refs_json JSON,
  due_at          TEXT,
  created_at      TEXT NOT NULL
);

CREATE TABLE metrics (
  metric_id       TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT,
  source_type     TEXT NOT NULL,  -- publication|campaign|lead
  source_id       TEXT NOT NULL,
  metric_name     TEXT NOT NULL,
  value           REAL NOT NULL,
  recorded_at     TEXT NOT NULL
);

CREATE TABLE roi_assessments (
  assessment_id   TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  scope_type      TEXT NOT NULL,  -- campaign|brand|product
  scope_id        TEXT NOT NULL,
  score_json      JSON,
  assessed_at     TEXT NOT NULL
);

CREATE TABLE insights (
  insight_id      TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT,
  summary         TEXT NOT NULL,
  refs_json       JSON,
  created_at      TEXT NOT NULL
);

CREATE TABLE experiments (
  experiment_id   TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  hypothesis      TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'planned',
  started_at      TEXT,
  concluded_at    TEXT
);
```

### Automatización

```sql
CREATE TABLE workflows (
  workflow_id     TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  name            TEXT NOT NULL,
  definition_json JSON NOT NULL,
  status          TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE approvals (
  approval_id     TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  target_type     TEXT NOT NULL,  -- publication|campaign|action
  target_id       TEXT NOT NULL,
  requested_by    TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'requested',
  decided_by      TEXT,
  decided_at      TEXT,
  reason          TEXT,
  created_at      TEXT NOT NULL
);

CREATE TABLE tasks (
  task_id         TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  assignee_id     TEXT,
  title           TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'open',
  due_at          TEXT,
  ref_type        TEXT,
  ref_id          TEXT
);
```

### Subdominio Plan (convivencia — JSON legacy)

`marketing_plans/*.json` — sin tabla en v1.0. Mapping futuro:

| Campo Plan v1.1 | Destino lógico |
|-----------------|----------------|
| `tenant_id` | tenants |
| `app_id` | brands.legacy_app_id |
| `id` | plan_id externo |

---

## Índices lógicos

```sql
CREATE INDEX idx_memory_tenant_time ON memory_events(tenant_id, timestamp DESC);
CREATE INDEX idx_memory_entity ON memory_events(tenant_id, event_type);
CREATE INDEX idx_memory_refs ON memory_events(tenant_id);  -- + JSON index en capa 4

CREATE INDEX idx_publications_queue ON publications(tenant_id, brand_id, status, scheduled_at);
CREATE INDEX idx_recommendations_inbox ON recommendations(tenant_id, assignee_role, status);
CREATE INDEX idx_campaigns_brand ON campaigns(tenant_id, brand_id, status);
CREATE INDEX idx_leads_status ON leads(tenant_id, status, created_at);
```

---

## Mapping legacy → tablas

| Legacy | Tabla objetivo | Estrategia migración |
|--------|----------------|----------------------|
| `registry.json` | `tenants` | Seed inicial |
| `apps/{app_id}/` | `brands` | `legacy_app_id` |
| `business_context.json` | `company_profiles` | Import one-shot |
| `content_queue.json` | `publications` | `legacy_queue_id` |
| `assistant_audit.jsonl` | `memory_events` | Línea → fila |
| `knowledge/*.md` | `knowledge_articles` | Por slug |
| `products.json` | `products` | Por slug |
| `campaigns/` | `campaigns` | Parcial existente |
| `marketing_plans/*.json` | *(sin tabla v1)* | Mantener JSON |

---

## Multi-tenant

- Toda query de aplicación incluye `WHERE tenant_id = ?`
- `brand_id` opcional en memory_events para eventos tenant-wide
- Ningún JOIN cruza tenants — validar en capa repositorio (Arquitectura §4)

---

## Checklist Sprint 1

- [x] DDL conceptual por agregado core
- [x] FKs y cardinalidad documentadas
- [x] ADR-0002 motor y fases
- [x] Mapping legacy
- [x] Índices lógicos
- [x] Reglas append-only Memory

---

## Referencias

- [MARKETING_OS_SPRINT1_DOMAIN_MODEL.md](MARKETING_OS_SPRINT1_DOMAIN_MODEL.md)
- [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md)
- [MARKETING_PLAN_DOMAIN_v1.1.md](MARKETING_PLAN_DOMAIN_v1.1.md)
