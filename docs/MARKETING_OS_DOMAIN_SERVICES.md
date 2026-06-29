# Marketing OS — Servicios de Dominio (contratos)

**Versión:** 0.1 · Sprint 1  
**Regla:** contratos only — **no implementar** en este sprint

Patrón: Application → **Domain Service** → agregados. Sin llamadas directas a IA, HTTP o UI desde dominio.

---

## CampaignService

| Operación | Descripción |
|-----------|-------------|
| `createCampaign(brandId, spec)` | Borrador campaña |
| `submitForReview(campaignId)` | → in_review |
| `approve(campaignId, actor)` | Requiere Approval |
| `schedule(campaignId, at)` | Programar |
| `recordPublication(campaignId, publicationId)` | Vincula publicación |
| `complete(campaignId, metrics)` | Cierra campaña |

**Emite:** `CampaignCreated`, `CampaignApproved`, `CampaignPublished`, …

---

## KnowledgeService

| Operación | Descripción |
|-----------|-------------|
| `getCompanyBrain(companyId)` | Lectura CompanyBrain |
| `updateCompanyBrain(companyId, patch, actor)` | Empresa Viva |
| `getProductKnowledge(brandId, productId)` | KB producto |
| `publishArticle(brandId, article)` | KnowledgeArticle |

**Emite:** `CompanyBrainUpdated`, `ProductKnowledgeUpdated`, …

---

## AssetService

| Operación | Descripción |
|-----------|-------------|
| `registerAsset(brandId, metadata, fileRef)` | Alta con metadatos |
| `searchAssets(brandId, query)` | Reutilización IA |
| `approveAsset(assetId, actor)` | → approved |
| `deprecateAsset(assetId, reason)` | → deprecated |

---

## RoadmapService

| Operación | Descripción |
|-----------|-------------|
| `generateDailyRoadmap(companyId, date)` | Roadmap del día |
| `listRecommendations(roadmapId, role?)` | Filtrado por rol |
| `acceptRecommendation(id, actor)` | → in_progress |
| `rejectRecommendation(id, actor, reason)` | → rejected |

**Sin IA en Sprint 1** — contrato preparado para Marketing Brain futuro.

---

## RecommendationService

| Operación | Descripción |
|-----------|-------------|
| `create(spec)` | Validar responsable + prioridad |
| `assign(id, roleOrUser)` | Ownership |
| `updateStatus(id, status, actor)` | Ciclo vida |
| `getDependencies(id)` | Grafo dependencias |

---

## AutomationService

| Operación | Descripción |
|-----------|-------------|
| `registerWorkflow(spec)` | Definición |
| `trigger(workflowId, context)` | Disparo |
| `requestApproval(actionId, actor)` | Gate humano |
| `executeApproved(actionId)` | Post-approval |

---

## CorporateMemoryService

| Operación | Descripción |
|-----------|-------------|
| `record(event)` | Append-only |
| `query(filters)` | Búsqueda por entity, tipo, fecha |
| `summarize(companyId, window)` | Input Marketing Brain |

**Regla:** todo servicio emite eventos → `CorporateMemoryService.record`.

---

## PublicationService

| Operación | Descripción |
|-----------|-------------|
| `createDraft(brandId, spec)` | Cola editorial |
| `submitForApproval(publicationId)` | |
| `approve(publicationId, actor)` | |
| `markPublished(publicationId, externalRef)` | post ID red |

*Convive con cola legacy hasta migración.*

---

## ROIService

| Operación | Descripción |
|-----------|-------------|
| `recordMetrics(source, metrics)` | Ingesta |
| `assessCampaign(campaignId)` | ROI campaña |
| `suggestStopStart(brandId)` | Señales detener/reactivar |

---

## AIProviderService (infra — límite dominio)

| Operación | Descripción |
|-----------|-------------|
| `complete(prompt, contextRefs)` | Generación |
| `estimateCost(requestId)` | Trazabilidad |

**No es servicio de dominio tenant** — capa infraestructura; dominio pasa `contextRefs`, no prompts crudos en agregados.

---

## Referencias

- [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)
- [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md)
- [MARKETING_PLAN_APPLICATION_LAYER.md](MARKETING_PLAN_APPLICATION_LAYER.md)
