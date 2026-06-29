# Marketing OS — Arquitectura de implementación

**Versión:** 1.0 · Sprint 2 cerrado  
**Estado:** ✅ Aprobado — implementación por pilares post-GO  
**Capa documental:** 4 de 6 (post Domain Model)  
**Dominio:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) v1.0  
**Persistencia:** [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md)  
**Constitución:** [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md)

> Cómo el **código** implementa el dominio. No redefine producto ni entidades.

**Nota:** [EMACCION_ARCHITECTURE.md](EMACCION_ARCHITECTURE.md) describe flujo comercial histórico (engines E–P). Este documento gobierna **estructura de código** del Marketing OS.

---

## 1. Principio rector

```
El dominio gobierna; el código implementa el dominio.
```

Todo módulo nuevo sigue el **Vertical Slice** probado en MarketingPlan. Legacy se estrangula con adapters, no se extiende.

---

## 2. Capas

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation                                               │
│  Marketing Console · plan_slice · dashboard · static/       │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼────────────────────────────────┐
│  API                                                        │
│  marketing_plan_api/ · future: memory_api, publication_api  │
│  /api/v1/tenants/{tenant_id}/apps/{app_id}/…                │
│  Legacy: app.py → /accio/{tenant_id}/… (convivencia)        │
└────────────────────────────┬────────────────────────────────┘
                             │ DTO · ApplicationContext
┌────────────────────────────▼────────────────────────────────┐
│  Application                                                │
│  use_cases/commands · use_cases/queries                     │
│  RBAC · orquestación · DomainEventPublisher                 │
└────────────────────────────┬────────────────────────────────┘
                             │ Commands / domain API
┌────────────────────────────▼────────────────────────────────┐
│  Domain                                                     │
│  model · service · ports · events · validators              │
│  SIN: HTTP, SQL, JSON, IA, Flask                          │
└────────────────────────────┬────────────────────────────────┘
                             │ Ports (interfaces)
┌────────────────────────────▼────────────────────────────────┐
│  Infrastructure                                             │
│  json_repository · sqlite_repository · mappers              │
│  ai_provider/ · connector clients · file storage            │
└────────────────────────────┬────────────────────────────────┘
                             │
                    marketing_os.db · Marketing/tenants/
```

### Reglas por capa

| Capa | Puede | No puede |
|------|-------|----------|
| **Presentation** | UI, navegación shell | Lógica de negocio, SQL |
| **API** | Validar HTTP, auth, DTO | Llamar Domain Service directo |
| **Application** | Use cases, RBAC, publicar eventos | Reglas de negocio duplicadas |
| **Domain** | Invariantes, estados, eventos | I/O, frameworks |
| **Infrastructure** | Persistencia, LLM, OAuth | Reglas de dominio |

---

## 3. Estructura de módulos objetivo

Base: `Motor_Tecnico/accio_engine/`

```
accio_engine/
├── app.py                          # Legacy gateway — solo registra blueprints, no crece
├── marketing_plan_{domain,application,infrastructure,api}/   # ✅ referencia
│
├── platform_domain/                # Shared kernel (futuro cercano)
│   ├── ports.py                    # TenantContext, Clock, IdGenerator
│   └── events.py                   # DomainEvent envelope
│
├── memory_{domain,application,infrastructure,api}/           # M1 Corporate Memory
├── knowledge_{domain,application,infrastructure,api}/        # M2 Brain + KB
├── brand_{domain,application,infrastructure,api}/            # M3 Brand Center
├── publication_{domain,application,infrastructure,api}/      # M4 cola
├── campaign_{domain,application,infrastructure,api}/         # M7
│
├── platform_infrastructure/
│   ├── db.py                       # marketing_os.db connection
│   ├── sqlite_memory_repository.py
│   └── event_bus.py                # → CorporateMemoryService
│
├── ai_provider/                    # Infra IA (existente)
├── tenant.py · marketing_app.py    # Legacy — envueltos por adapters M3
└── static/                         # Marketing Console UI
```

**Convención nombre:** `{aggregate}_{layer}/` — cuatro carpetas por bounded context maduro.

---

## 4. Patrón referencia: MarketingPlan

| Pieza | Archivo actual | Replicar en |
|-------|----------------|-------------|
| Modelo | `marketing_plan_domain/model.py` | `{agg}_domain/model.py` |
| Reglas | `marketing_plan_domain/service.py` | `{agg}_domain/service.py` |
| Port repo | `marketing_plan_domain/ports.py` | `{agg}_domain/ports.py` |
| Use case | `marketing_plan_application/use_cases/commands/*.py` | `{agg}_application/use_cases/` |
| JSON adapter | `marketing_plan_infrastructure/json_repository.py` | `{agg}_infrastructure/json_repository.py` |
| SQL adapter | *(pendiente)* | `{agg}_infrastructure/sqlite_repository.py` |
| Routes | `marketing_plan_api/routes.py` | `{agg}_api/routes.py` |
| Wiring | `marketing_plan_api/composition.py` | `{agg}_api/composition.py` |

**Flujo obligatorio:**

```
POST /api/v1/tenants/{t}/apps/{a}/marketing-plans
  → CreateMarketingPlan (application)
  → MarketingPlanDomainService.create(...)
  → JsonMarketingPlanRepository.save(...)
  → DomainEventPublisher.publish(PlanActivated)
  → (futuro) SqliteMemoryRepository.record(...)
```

---

## 5. Ports transversales

| Port | Implementaciones | Uso |
|------|------------------|-----|
| `Clock` | `SystemClock` | timestamps UTC |
| `IdGenerator` | `UuidIdGenerator` | ids opacos |
| `TenantAppValidator` | `MarketingTenantAppValidator` | tenant + app existen |
| `AuthorizationPort` | `RbacAuthorizationAdapter` | permisos |
| `DomainEventPublisher` | `CollectingDomainEventPublisher` / `NoOp` | tests |
| `CorporateMemoryPort` | `SqliteMemoryRepository` | append events |
| `BrandResolver` | adapter sobre `marketing_app` | `app_id` → `brand_id` |

---

## 6. Corporate Memory — integración eventos

Todo use case que muta estado core debe publicar evento alineado a [DOMAIN_EVENTS](MARKETING_OS_DOMAIN_EVENTS.md).

```python
# application layer (patrón)
event = CampaignPublished(
    tenant_id=ctx.tenant_id,
    brand_id=ctx.brand_id,
    campaign_id=campaign.id,
    ...
)
self._events.publish(event)
# infrastructure subscriber
memory.record(event.to_envelope())
```

**Envelope** → tabla `memory_events` ([PERSISTENCE](MARKETING_OS_DOMAIN_PERSISTENCE.md)).

Legacy `assistant_audit.jsonl` queda cubierto por fase **M1** ([MIGRATION_PLAN](MARKETING_OS_MIGRATION_PLAN.md)).

---

## 7. API pública

**Contrato base:** [API_CONTRACT_V1.md](API_CONTRACT_V1.md) — sin cambiar prefijo `/api/v1`.

**Recursos planificados:** [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md)

| API | Estado |
|-----|--------|
| `/api/v1/.../marketing-plans` | ✅ Implementado |
| `/api/v1/.../memory/events` | 📋 M1 |
| `/api/v1/.../company-brain` | 📋 M2 |
| `/api/v1/.../publications` | 📋 M4 |
| `/api/v1/.../campaigns` | 📋 M7 |
| `/accio/{tenant}/content/queue` | 🔄 Legacy hasta M4 |

**Regla HTTP:** `tenant_id` + `app_id` en path; servidor resuelve `brand_id` internamente.

---

## 8. Multi-tenant y seguridad

1. `ApplicationContext` lleva `tenant_id`, `app_id`, `actor`, `permissions`.
2. Repositorios reciben `tenant_id` en cada operación — **nunca** confiar solo en id de recurso.
3. Queries SQL siempre `WHERE tenant_id = ?`.
4. RBAC en application layer antes de domain (como MarketingPlan).
5. API key Bearer (`app.py`) delega a mismo RBAC que sesión UI.

---

## 9. IA (AI Provider)

Capa **infraestructura** — `ai_provider/manager.py`.

```
Application use case
  → construye context_refs (brain_id, article_ids, asset_ids)
  → AIProviderService.complete(prompt, context_refs)
  → LiteLLM / CODITO
```

Dominio **no** importa `ai_provider`. Principio 3: `KnowledgeService.searchBeforeCreate` antes de llamar IA.

---

## 10. Marketing Console (UI)

[WORKSPACE_SHELL.md](WORKSPACE_SHELL.md) — shell único.

| Área Console | Módulo static | API futura |
|--------------|---------------|------------|
| Inicio / Roadmap | `plan_slice.js` navigateTo | recommendations |
| Plan | plan wizard | marketing-plans ✅ |
| Publicaciones | dashboard legacy | publications |
| Knowledge | dashboard tab | company-brain, articles |
| Operaciones | embedded dashboard | legacy `/accio/` |

Nuevas pantallas consumen `/api/v1`, no JSON directo.

---

## 11. Mapa pilar → módulos

| Pilar | Bounded contexts | Fase migración |
|-------|------------------|----------------|
| 1 Company Brain | knowledge_domain (brain) | M2 |
| 2 Corporate Memory | memory_domain | M1 |
| 3 Product KB | knowledge_domain (articles) | M6 |
| 4 Brand Center | brand_domain | M3 |
| 5 Asset Manager | asset_domain | M8 |
| 6 Marketing Brain | analytics + roadmap | M10 |
| 7 Roadmap Engine | recommendation_domain | M10 |
| 8 AI Provider | ai_provider/ | infra |
| 9 Automation Engine | automation_domain | post-M4 |
| 10 ROI Engine | analytics_domain | post-M7 |
| Console | static/ + APIs | transversal |

---

## 12. Implementación — orden de pilares (Sprint 3+)

Requiere **GO explícito** por fase:

```
1. M0  platform_infrastructure + marketing_os.db
2. M1  Corporate Memory (desbloquea todo aprendizaje)
3. M2  Company Brain
4. M3  Brands
5. M4  Publications (cola editorial)
6. M5–M9  según MIGRATION_PLAN
7. M10 Roadmap + Recommendations
```

**Principio 19** obligatorio en cada PR de implementación.

---

## 13. Deuda técnica conocida

| Item | Acción |
|------|--------|
| `app.py` monolito | Registrar blueprints; no añadir lógica |
| `*_store.py` flat | Envolver con ports; deprecar gradualmente |
| OpenAI en tenant_secrets | Deprecar; solo `ai_provider` servidor |
| `assistant_audit.jsonl` | M1 → memory_events |
| Dual API `/accio` + `/api/v1` | Documentado; converger en v1 |

---

## 14. Criterio de aceptación Sprint 2

| # | Pregunta | Sección |
|---|----------|---------|
| 1 | ¿Capas y responsabilidades? | §2 |
| 2 | ¿Patrón a copiar? | §3–4 |
| 3 | ¿Cómo llegan eventos a Memory? | §6 |
| 4 | ¿API nueva vs legacy? | §7 |
| 5 | ¿Orden migración? | §12 + MIGRATION_PLAN |
| 6 | ¿Dónde va la IA? | §9 |

---

## Referencias

- [adr/0003-marketing-os-layered-architecture.md](adr/0003-marketing-os-layered-architecture.md)
- [MARKETING_OS_MIGRATION_PLAN.md](MARKETING_OS_MIGRATION_PLAN.md)
- [MARKETING_OS_API_RESOURCES.md](MARKETING_OS_API_RESOURCES.md)
- [MARKETING_PLAN_APPLICATION_LAYER.md](MARKETING_PLAN_APPLICATION_LAYER.md)
