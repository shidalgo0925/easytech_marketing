# Marketing OS — Servicios de Dominio (contratos)

**Versión:** 1.0 · Sprint 1 cerrado  
**Regla:** contratos only — implementar en Sprint 3+ post-Arquitectura

Patrón: Application → **Domain Service** → agregados. Sin IA, HTTP ni UI en dominio.

**Regla transversal:** todo servicio emite eventos → `CorporateMemoryService.record`.

---

## CorporateMemoryService

| Operación | Descripción |
|-----------|-------------|
| `record(event: DomainEvent)` | Append-only a `memory_events` |
| `query(filters)` | Por tenant, entity, tipo, rango fecha |
| `summarize(companyId, window)` | Input Marketing Brain / ROI |

---

## KnowledgeService

| Operación | Descripción |
|-----------|-------------|
| `getCompanyBrain(companyId)` | Lectura |
| `updateCompanyBrain(companyId, patch, actor)` | Empresa Viva |
| `getProductKnowledge(brandId, productId?)` | KB marca/producto |
| `publishArticle(brandId, article)` | KnowledgeArticle |
| `searchBeforeCreate(brandId, query)` | Principio 3 — orden jerárquico |

**Emite:** `CompanyBrainUpdated`, `ProductKnowledgeUpdated`, `KnowledgeArticlePublished`

---

## BrandService

| Operación | Descripción |
|-----------|-------------|
| `getBrandGuide(brandId)` | Brand Center |
| `updateBrandGuide(brandId, patch, actor)` | Colores, logo, manual |
| `listTemplates(brandId)` | Plantillas reutilizables |

**Emite:** `BrandingChanged`

---

## AssetService

| Operación | Descripción |
|-----------|-------------|
| `registerAsset(brandId, metadata, fileRef)` | Alta con metadatos obligatorios |
| `searchAssets(brandId, query)` | Reutilización |
| `approveAsset(assetId, actor)` | → approved |
| `deprecateAsset(assetId, reason)` | → deprecated |

**Emite:** `FlyerGenerated` (si tipo flyer)

---

## ProductService

| Operación | Descripción |
|-----------|-------------|
| `createProduct(brandId, spec)` | Alta producto |
| `updateProduct(productId, patch, actor)` | |
| `listByBrand(brandId)` | Catálogo |

**Emite:** `ProductUpdated`, `PromotionStarted`, `PriceChanged`

---

## CampaignService

| Operación | Descripción |
|-----------|-------------|
| `createCampaign(brandId, spec)` | Borrador |
| `submitForReview(campaignId)` | → in_review |
| `approve(campaignId, actor)` | Requiere Approval |
| `schedule(campaignId, at)` | Programar |
| `recordPublication(campaignId, publicationId)` | Vincula publicación |
| `complete(campaignId, metrics)` | Cierra campaña |

**Emite:** `CampaignCreated` … `CampaignCompleted`

---

## PublicationService

| Operación | Descripción |
|-----------|-------------|
| `createDraft(brandId, spec)` | Cola editorial |
| `submitForApproval(publicationId)` | |
| `approve(publicationId, actor)` | |
| `markPublished(publicationId, externalRef)` | post ID red |
| `markFailed(publicationId, error)` | |

*Convive con `content_queue.json` hasta migración.*

**Emite:** `PublicationDraftCreated` … `PublicationFailed`

---

## RoadmapService

| Operación | Descripción |
|-----------|-------------|
| `generateDailyRoadmap(companyId, date)` | DailyRoadmap + recomendaciones |
| `listRecommendations(roadmapId, role?)` | Filtrado por rol Console |
| `getActivePlanContext(companyId)` | Lee MarketingPlan v1.1 JSON — no muta |

**Emite:** `DailyRoadmapGenerated`, `RecommendationCreated`

---

## RecommendationService

| Operación | Descripción |
|-----------|-------------|
| `create(spec)` | Valida assignee + priority |
| `assign(id, roleOrUser)` | Ownership |
| `accept(id, actor)` | → in_progress |
| `reject(id, actor, reason)` | → rejected |
| `complete(id, actor, outcome)` | → done |
| `getDependencies(id)` | Grafo |

**Emite:** `RecommendationAccepted`, `RecommendationRejected`, `RecommendationCompleted`

---

## LeadService · CommercialService

| Operación | Servicio |
|-----------|----------|
| `ingestLead(tenantId, source, contact)` | LeadService |
| `assignLead(leadId, userId)` | LeadService |
| `convertToCustomer(leadId)` | CommercialService |
| `logConversation(contactId, channel, summary)` | CommercialService |

**Emite:** `LeadCreated`, `LeadAssigned`, `CustomerConverted`, `ConversationLogged`

---

## AutomationService

| Operación | Descripción |
|-----------|-------------|
| `registerWorkflow(spec)` | Definición |
| `trigger(workflowId, context)` | Disparo |
| `requestApproval(targetType, targetId, actor)` | Gate humano |
| `executeApproved(approvalId)` | Post-approval |

**Emite:** `WorkflowTriggered`, `ApprovalRequested`, `ActionExecuted`, …

---

## ROIService · AnalyticsService

| Operación | Servicio |
|-----------|----------|
| `recordMetrics(source, metrics)` | ROIService |
| `assessCampaign(campaignId)` | ROIService |
| `assessBrand(brandId, window)` | ROIService |
| `generateInsight(brandId, contextRefs)` | AnalyticsService |

**Emite:** `MetricRecorded`, `ROIAssessed`, `InsightGenerated`

---

## TenantService

| Operación | Descripción |
|-----------|-------------|
| `provisionTenant(spec)` | Alta SaaS |
| `suspendTenant(tenantId, reason)` | |
| `resolveBrand(tenantId, legacyAppId)` | Mapping `app_id` → `brand_id` |

---

## AIProviderService (infra — fuera dominio tenant)

| Operación | Descripción |
|-----------|-------------|
| `complete(prompt, contextRefs)` | Generación |
| `estimateCost(requestId)` | Trazabilidad |

Capa infraestructura; dominio pasa `contextRefs` (IDs KB, Brain), no prompts en agregados.

---

## Mapa servicio → agregado

| Servicio | Agregados principales |
|----------|----------------------|
| CorporateMemoryService | MemoryEvent |
| KnowledgeService | CompanyBrain, ProductKnowledge |
| BrandService | BrandGuide |
| AssetService | MediaAsset |
| ProductService | Product, Promotion, Offer |
| CampaignService | Campaign |
| PublicationService | Publication |
| RoadmapService | DailyRoadmap, Recommendation |
| RecommendationService | Recommendation |
| LeadService | Lead |
| CommercialService | Customer, Opportunity |
| AutomationService | Workflow, Approval, Task |
| ROIService | Metric, ROI |
| TenantService | Tenant, Brand |

---

## Referencias

- [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)
- [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md)
- [MARKETING_PLAN_APPLICATION_LAYER.md](MARKETING_PLAN_APPLICATION_LAYER.md)
