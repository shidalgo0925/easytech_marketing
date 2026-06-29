# M10 — Decision Engine V1 (Sprint 12)

**Estado:** 🟢 GO documental · **Sin código hasta cierre M10.1**  
**Versión:** 1.0 · 2026-06-26  
**Dominio:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) §1.9 · [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md) RoadmapService  
**Precede:** Capa de conocimiento M0–M9 (implementada localmente, sin commit)

---

## Decisión de producto (congelada)

> **Detener la creación de agregados “de datos”.** M0–M9 cerraron la materia prima.  
> **M10 no es una tabla más.** Es el primer **Decision Engine** del Marketing OS: transforma conocimiento en decisiones accionables, priorizadas, justificadas y medibles.

**Pregunta gate** (obligatoria antes de cualquier tabla o módulo nuevo):

| Pregunta | Si “sí” → | Si “no” → |
|----------|-----------|-----------|
| ¿Almacena **conocimiento**? | Capa M* / dominio curado | — |
| ¿Registra o toma una **decisión**? | Decision Engine M10+ | No implementar |

A partir de M10 el valor del producto deja de estar en **almacenar** y pasa a estar en **recomendar con responsable**.

---

## Qué NO es M10

- ❌ CRUD de `recommendations` sin motor
- ❌ Texto libre “Buenos días…” guardado en BD
- ❌ IA generativa (eso es **M11 Marketing Brain**)
- ❌ Ejecución automática sin aprobación (Automation Engine, post-M10.5)

---

## Qué SÍ es M10 — Decision Engine

Bounded context compuesto por:

| Componente | Rol |
|------------|-----|
| **Roadmap Builder** (M10.1) | Lee agregados M0–M9, detecta oportunidades/gaps |
| **Priority Engine** (M10.2) | Ordena por ROI, urgencia, objetivos, tiempo |
| **Recommendation Engine** (M10.3) | Materializa objetos `Recommendation` |
| **Daily Planner** (M10.4) | Crea `DailyRoadmap` con referencias, no prosa |
| **Approval Queue** (M10.5) | Humano aprueba/rechaza antes de Automation |

### Flujo objetivo (V1)

```
Corporate Memory + Company Brain + Products + Campaigns
        + Publications + Assets + Leads + Knowledge
                          ↓
              Decision Engine (reglas, sin IA)
                          ↓
              DailyRoadmap (2026-06-26)
                    ├── Recommendation #381  (publish EN1)
                    ├── Recommendation #382  (…)
                    └── Recommendation #383  (…)
                          ↓
              Approval Queue  →  [Aprobar] [Rechazar]
                          ↓
              Automation Engine (futuro) → LinkedIn / Meta
```

### Experiencia Console (target)

```
Buenos días.

Hoy recomiendo:

  Prioridad Alta — Publicar EN1
  Motivo: Sin publicaciones en 9 días
  Impacto esperado: ~3 500 personas (alcance histórico marca)
  Responsable: Marketing
  [Aprobar]  [Rechazar]  [Posponer]
```

La UI renderiza objetos; **no** persiste ese párrafo como fuente de verdad.

---

## Entidades (corazón del sistema)

### Recommendation

Unidad atómica de decisión. Campos V1:

| Campo | Tipo | Notas |
|-------|------|-------|
| `recommendation_id` | TEXT | PK |
| `tenant_id` | TEXT | |
| `company_id` | TEXT | = tenant en fase actual |
| `brand_id` | TEXT | Marca / `app_id` |
| `roadmap_id` | TEXT | FK opcional hasta asignar al día |
| `title` | TEXT | Ej. "Publicar EN1" |
| `description` | TEXT | Detalle accionable |
| `action` | TEXT | Verbo dominio: `publish`, `create_campaign`, `follow_up_lead` |
| `reason` | TEXT | Justificación humana |
| `expected_roi` | TEXT/JSON | Impacto esperado (V1: texto + número opcional) |
| `priority` | TEXT | `high` \| `medium` \| `low` |
| `priority_score` | REAL | Salida Priority Engine (M10.2) |
| `owner_role` | TEXT | Ej. `marketing`, `community_manager` |
| `owner_id` | TEXT | Usuario opcional |
| `due_at` | TEXT | ISO-8601 |
| `status` | TEXT | Ver máquina de estados |
| `source` | TEXT | `rule:brand_inactivity` |
| `confidence` | REAL | V1 reglas: `1.0`; M11 puede bajar/subir |
| `justification_refs` | JSON | refs a publication, campaign, memory_event… |
| `dependencies_json` | JSON | otras recommendation_ids |
| `created_by` | TEXT | `system` \| user_id |
| `approved_by` | TEXT | |
| `rejected_by` | TEXT | |
| `executed_at` | TEXT | |
| `result_json` | JSON | outcome post-ejecución |
| `created_at` | TEXT | |
| `updated_at` | TEXT | |

**Estados** (dominio §5, extendido para aprobación):

```
draft → pending_approval → approved → in_progress → done
                        ↘ rejected
                        ↘ snoozed
```

M10.5 introduce `pending_approval` como estado inicial tras generación automática.

### DailyRoadmap

Contenedor persistido — permite comparar días y aprender.

| Campo | Tipo |
|-------|------|
| `roadmap_id` | TEXT PK |
| `tenant_id` | TEXT |
| `company_id` | TEXT |
| `roadmap_date` | TEXT (YYYY-MM-DD, timezone tenant) |
| `generated_at` | TEXT |
| `generator_version` | TEXT | Ej. `decision_engine_v1` |
| `summary_json` | JSON | Contadores: high/medium/low, por marca |

**Relación:** `DailyRoadmap` 1→N `Recommendation` vía `roadmap_id`.  
El roadmap **no guarda texto**; guarda referencias ordenadas.

### DecisionRule (M10.1 — configuración)

Reglas explícitas en código o tabla `decision_rules` (V1: código + tests).

| Campo | Ejemplo |
|-------|---------|
| `rule_id` | `brand_publication_gap` |
| `enabled` | true |
| `condition` | `days_since_last_published(brand) >= 7` |
| `action_template` | `publish` |
| `priority_default` | `high` |

### Goal · KPI (V1 mínimo)

Leídos de Company Brain / MarketingPlan activo (solo lectura).  
Priority Engine usa pesos configurables; no mutan Plan v1.1.

---

## Fuentes de lectura (adapters M0–M9)

| Fuente | Uso en Decision Engine |
|--------|------------------------|
| `memory_events` | Última actividad, auditoría |
| `company_profiles` | Objetivos, CTA, audiencia |
| `brands` | Marcas activas, default |
| `products` | Catálogo por marca |
| `publications` | Última publicación, cola pendiente |
| `campaigns` | Definiciones + `post_id` |
| `media_assets` | Flyer disponible por número |
| `knowledge_articles` | Contexto producto |
| `leads` | Leads recientes sin seguimiento |
| MarketingPlan v1.1 JSON | Contexto estratégico (read-only) |

**Sin escribir** en agregados de conocimiento desde M10 (Principio: Roadmap lee Plan, no lo muta).

---

## Sub-fases de implementación

### M10.1 — Roadmap Builder ✅ criterio primero

**Entregable:** `decision_engine/` slice + `KnowledgeSnapshot` por tenant  
**IA:** No

- Port `KnowledgeReader` — compone snapshot desde repos M1–M9
- Regla V1: **`brand_publication_gap`**
  - Input: `brand_id`, umbral días (default 7)
  - Lee: `publications` última `published_at` o `scheduled_at` pendiente
  - Output: candidatos `Recommendation` en estado `draft`

**Cierre:** test integración easytech — detecta EN1 sin post en N días.

### M10.2 — Priority Engine

**Entregable:** `PriorityScorer`  
**IA:** No

Factores V1 (pesos en config):

| Factor | Peso inicial |
|--------|--------------|
| Días sin actividad marca | 40% |
| Alineación producto prioritario (Brain) | 25% |
| Leads recientes sin contacto | 20% |
| Proximidad editorial (3 valor + 1 venta) | 15% |

Output: `priority_score` + `priority` enum.

**Cierre:** misma lista de candidatos ordenada de forma determinista.

### M10.3 — Recommendation Engine

**Entregable:** persistencia `recommendations` + domain service  
**IA:** No

- `createFromCandidate()` — objeto completo con `justification_refs`
- Emite `RecommendationCreated` → `memory_events`

**Cierre:** objeto JSON API cumple contrato § Entidades.

### M10.4 — Daily Planner

**Entregable:** `daily_roadmaps` + `generateDailyRoadmap(tenant, date)`  
**IA:** No

- Idempotente por `(tenant_id, company_id, roadmap_date)`
- Asigna `roadmap_id` a recommendations del día
- Emite `DailyRoadmapGenerated`

**Cierre:** `GET /roadmaps/{date}` devuelve roadmap + N recommendations ordenadas.

### M10.5 — Approval Queue

**Entregable:** transiciones + API approve/reject/snooze  
**IA:** No

- `pending_approval` → `approved` \| `rejected` \| `snoozed`
- Rechazo exige `reason` (Constitución / dominio §6)
- Emite `RecommendationAccepted`, `RecommendationRejected` → Memory
- **No ejecuta** publisher — solo deja listo para Automation

**Cierre:** flujo UI “Aprobar” cambia estado y registra evento; publisher sigue manual o M-futuro.

---

## Schema SQLite (v10 — solo decisión)

```sql
-- M10 — Decision Engine
CREATE TABLE daily_roadmaps (
  tenant_id       TEXT NOT NULL,
  roadmap_id      TEXT NOT NULL,
  company_id      TEXT NOT NULL,
  roadmap_date    TEXT NOT NULL,
  generated_at    TEXT NOT NULL,
  generator_version TEXT NOT NULL DEFAULT 'decision_engine_v1',
  summary_json    TEXT,
  PRIMARY KEY (tenant_id, roadmap_id),
  UNIQUE (tenant_id, company_id, roadmap_date)
);

CREATE TABLE recommendations (
  tenant_id           TEXT NOT NULL,
  recommendation_id   TEXT NOT NULL,
  company_id          TEXT NOT NULL,
  brand_id            TEXT NOT NULL,
  roadmap_id          TEXT,
  title               TEXT NOT NULL,
  description         TEXT,
  action              TEXT NOT NULL,
  reason              TEXT NOT NULL,
  expected_roi        TEXT,
  priority            TEXT NOT NULL,
  priority_score      REAL,
  owner_role          TEXT NOT NULL,
  owner_id            TEXT,
  due_at              TEXT,
  status              TEXT NOT NULL DEFAULT 'pending_approval',
  source              TEXT NOT NULL,
  confidence          REAL NOT NULL DEFAULT 1.0,
  justification_refs_json TEXT,
  dependencies_json   TEXT,
  created_by          TEXT NOT NULL,
  approved_by         TEXT,
  rejected_by         TEXT,
  executed_at         TEXT,
  result_json         TEXT,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  PRIMARY KEY (tenant_id, recommendation_id)
);

CREATE INDEX idx_recommendations_inbox
  ON recommendations(tenant_id, owner_role, status, priority_score DESC);

CREATE INDEX idx_recommendations_roadmap
  ON recommendations(tenant_id, roadmap_id);
```

---

## API `/api/v1` (M10)

| Método | Ruta | Fase |
|--------|------|------|
| POST | `tenants/{id}/roadmaps/{date}/generate` | M10.4 |
| GET | `tenants/{id}/roadmaps/{date}` | M10.4 |
| GET | `tenants/{id}/roadmaps/today` | M10.4 alias |
| GET | `tenants/{id}/recommendations` | M10.3 (`?status=&brand_id=`) |
| GET | `tenants/{id}/recommendations/{id}` | M10.3 |
| POST | `tenants/{id}/recommendations/{id}/approve` | M10.5 |
| POST | `tenants/{id}/recommendations/{id}/reject` | M10.5 body: `reason` |
| POST | `tenants/{id}/recommendations/{id}/snooze` | M10.5 body: `until` |

---

## Módulos código (patrón slice)

```
decision_engine_domain/       # Recommendation, DailyRoadmap, Rule
decision_engine_application/  # GenerateDailyRoadmap, ApproveRecommendation
decision_engine_infrastructure/
  knowledge_snapshot.py       # Lee M1–M9
  rules/                      # brand_publication_gap.py …
  priority_scorer.py
  sqlite_repository.py
decision_engine_api/
```

**Sin facade legacy** — primer módulo 100% nativo plataforma.

---

## Eventos Corporate Memory

| Evento | Cuándo |
|--------|--------|
| `DailyRoadmapGenerated` | M10.4 |
| `RecommendationCreated` | M10.3 |
| `RecommendationAccepted` | M10.5 approve |
| `RecommendationRejected` | M10.5 reject |
| `RecommendationCompleted` | post-Automation (futuro) |

---

## Regla de negocio V1 (caso piloto)

**ID:** `brand_publication_gap`

```
SI última publicación publicada de brand_id > N días
Y existe al menos 1 publication scheduled/pending en cola
ENTONCES Recommendation:
  action: publish
  title: "Publicar {brand_name}"
  reason: "Sin publicaciones en {N} días"
  priority: high (si N >= 7)
  owner_role: marketing
  justification_refs: [publication_id, brand_id, memory_event?]
```

**Tenant piloto:** `easytech` · **Marca piloto:** `en1`

---

## Criterios de cierre Sprint 12 (M10 completo)

| # | Criterio |
|---|----------|
| 1 | `generate` para hoy crea `DailyRoadmap` idempotente |
| 2 | ≥1 `Recommendation` con regla `brand_publication_gap` en easytech |
| 3 | Priority determinista documentada en tests |
| 4 | Approve/Reject persisten + `memory_events` |
| 5 | Console puede listar inbox sin leer JSON legacy |
| 6 | **Cero** llamadas LLM en el path M10 |

---

## M11 — Marketing Brain (siguiente, fuera M10)

- Enriquece `reason`, `description`, `confidence` con IA
- **No** sustituye estructura Recommendation / DailyRoadmap
- Lee Decision Engine output como input
- Requiere GO separado

---

## Relación con commit pendiente M4–M9

M10 **depende** de adapters M1–M9 en runtime.  
Recomendación operativa:

1. Commit **“M4–M9 knowledge layer”** (sin runtime tenant)
2. Migraciones prod + flags `ACCIO_*_STORE=dual`
3. GO implementación **M10.1** únicamente

---

## Referencias

- [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) — §8 flujo Recomendación
- [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md)
- [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md) — Recommendations
- [adr/0001-marketing-os-domain-sprint0.md](adr/0001-marketing-os-domain-sprint0.md) — Recomendación como entidad central
