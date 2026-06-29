# Marketing OS — Recursos API (`/api/v1`)

**Versión:** 1.0 · Sprint 2  
**Contrato global:** [API_CONTRACT_V1.md](API_CONTRACT_V1.md)  
**Dominio:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)

> Segunda ola de recursos REST — misma versión URL `/api/v1`. `app_id` en path = `brand_id` en dominio.

---

## Convenciones (heredadas)

- Base: `/api/v1/tenants/{tenant_id}/apps/{app_id}/`
- Auth: sesión UI o Bearer API key con RBAC
- Respuestas: JSON snake_case, fechas UTC `Z`
- Errores: formato global API_CONTRACT_V1 §6

---

## Recursos implementados

### MarketingPlan ✅

| Método | Ruta | Use case |
|--------|------|----------|
| GET | `.../marketing-plans` | ListMarketingPlans |
| POST | `.../marketing-plans` | CreateMarketingPlan |
| GET | `.../marketing-plans/{id}` | GetMarketingPlan |
| PATCH | `.../marketing-plans/{id}` | UpdateMarketingPlan |
| POST | `.../marketing-plans/{id}/activate` | ActivateMarketingPlan |
| POST | `.../marketing-plans/{id}/pause` | PauseMarketingPlan |
| POST | `.../marketing-plans/{id}/complete` | CompleteMarketingPlan |
| GET | `.../marketing-plans/active` | GetActiveMarketingPlan |

Dominio congelado v1.1 — sin expandir campos.

---

## Recursos planificados

### Company Brain (M2)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../company-brain` | ✅ M2 Sprint 4 |
| PATCH | `.../company-brain` | ✅ M2 — actualización parcial |
| GET | `tenants/{tenant_id}/company-brain` | ✅ alias tenant scope |

### Corporate Memory (M1)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `tenants/{tenant_id}/memory/events` | ✅ Sprint 3 — query con filtros |
| GET | `tenants/{tenant_id}/memory/events/{id}` | ✅ Sprint 3 — detalle |
| POST | *(interno)* | Solo vía DomainEventPublisher — no público |

### Publications (M4)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../publications` | Lista cola (`status`, `channel`) |
| POST | `.../publications` | Crear borrador |
| GET | `.../publications/{id}` | Detalle |
| PATCH | `.../publications/{id}` | Editar borrador |
| POST | `.../publications/{id}/submit` | → pending_approval |
| POST | `.../publications/{id}/approve` | → approved |
| POST | `.../publications/{id}/schedule` | body: `scheduled_at` |
| POST | `.../publications/{id}/publish` | Marca publicado + external_post_id |

### Campaigns (M7)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../campaigns` | Lista |
| POST | `.../campaigns` | Crear draft |
| GET | `.../campaigns/{id}` | Detalle + publications summary |
| PATCH | `.../campaigns/{id}` | Editar |
| POST | `.../campaigns/{id}/submit` | in_review |
| POST | `.../campaigns/{id}/approve` | approved |
| POST | `.../campaigns/{id}/complete` | completed + metrics |

### Products (M5)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../products` | Catálogo marca |
| POST | `.../products` | Alta |
| GET | `.../products/{id}` | Detalle |
| PATCH | `.../products/{id}` | Actualizar |

### Knowledge (M6)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../knowledge/articles` | Lista artículos |
| POST | `.../knowledge/articles` | Crear |
| GET | `.../knowledge/articles/{slug}` | Por slug |
| PATCH | `.../knowledge/articles/{slug}` | Editar |
| POST | `.../knowledge/articles/{slug}/publish` | published |

### Brands / Marcas (M3) ✅

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `tenants/{tenant_id}/brands` | Lista marcas |
| GET | `tenants/{tenant_id}/brands/{brand_id}` | Detalle (`brand_id` = `app_id`) |

### Brand Guide (Brand Center — futuro)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../brand-guide` | Manual + colores + tipografía |
| PATCH | `.../brand-guide` | Actualizar |

### Assets (M8)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `.../assets` | Búsqueda `type`, `tags`, `campaign_id` |
| POST | `.../assets` | Registrar metadata (+ upload separado) |
| GET | `.../assets/{id}` | Detalle |
| POST | `.../assets/{id}/approve` | approved |

### Decision Engine (M10)

Roadmap diario + recomendaciones priorizadas. Spec: [MARKETING_OS_SPRINT12_DECISION_ENGINE.md](MARKETING_OS_SPRINT12_DECISION_ENGINE.md)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `tenants/{tenant_id}/roadmaps/{date}/generate` | Generar roadmap (reglas) |
| GET | `tenants/{tenant_id}/roadmaps/{date}` | DailyRoadmap + recommendations |
| GET | `tenants/{tenant_id}/roadmaps/today` | Alias fecha tenant |
| GET | `tenants/{tenant_id}/recommendations` | Inbox (`status`, `brand_id`) |
| GET | `tenants/{tenant_id}/recommendations/{id}` | Detalle |
| POST | `tenants/{tenant_id}/recommendations/{id}/approve` | M10.5 |
| POST | `tenants/{tenant_id}/recommendations/{id}/reject` | body: `reason` |
| POST | `tenants/{tenant_id}/recommendations/{id}/snooze` | body: `until` |

### Leads (M9)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `tenants/{tenant_id}/leads` | Lista |
| POST | `tenants/{tenant_id}/leads` | Ingesta |
| PATCH | `tenants/{tenant_id}/leads/{id}` | Asignar / estado |

---

## Legacy no duplicar en v1

Estos permanecen en `/accio/{tenant_id}/` hasta migración:

| Legacy | Reemplazo API |
|--------|---------------|
| `GET/POST .../content/queue` | publications |
| `POST .../assistant/chat` | assistant (futuro `/api/v1/.../assistant`) |
| `POST .../tick` | automation interna |
| `GET .../dashboard/api/*` | recursos específicos v1 |

---

## OpenAPI

Generar `docs/openapi/marketing_os_v1.yaml` en Sprint 3 cuando primer recurso post-Plan esté implementado. Hasta entonces: este doc + API_CONTRACT_V1.

---

## Referencias

- [MARKETING_OS_ARCHITECTURE.md](MARKETING_OS_ARCHITECTURE.md)
- [MARKETING_OS_MIGRATION_PLAN.md](MARKETING_OS_MIGRATION_PLAN.md)
