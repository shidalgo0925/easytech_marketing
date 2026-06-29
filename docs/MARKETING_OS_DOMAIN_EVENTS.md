# Marketing OS — Catálogo de Eventos de Dominio

**Versión:** 1.0 · Sprint 1 cerrado  
**Regla:** todo evento → `CorporateMemoryService.record` → `memory_events`

Formato: `DomainEventName` · agregado origen · fase ciclo · payload mínimo

---

## Organización

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `TenantCreated` | Tenant | — | tenant_id |
| `TenantSuspended` | Tenant | — | reason |
| `CompanyProfileUpdated` | Company / CompanyBrain | Aprender | fields_changed[] |
| `BrandCreated` | Brand | Observar | brand_id, name |
| `BrandPaused` | Brand | Aprender | reason |
| `UserInvited` | User | — | email, role_id |

---

## Conocimiento

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `CompanyBrainUpdated` | CompanyBrain | Aprender | fields_changed[] |
| `ObjectiveChanged` | CompanyBrain | Aprender | objective_id, text |
| `ProductKnowledgeUpdated` | ProductKnowledge | Aprender | knowledge_id |
| `KnowledgeArticlePublished` | KnowledgeArticle | Aprender | article_id, slug |
| `CaseStudyAdded` | CaseStudy | Aprender | case_id |
| `CompetitorIntelUpdated` | Competitor | Observar | competitor_id |
| `BrandingChanged` | BrandGuide | Aprender | brand_id, fields[] |

---

## Marketing

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `CampaignCreated` | Campaign | Planificar | campaign_id, brand_id |
| `CampaignSubmittedForReview` | Campaign | Planificar | campaign_id |
| `CampaignApproved` | Campaign / Approval | Ejecutar | campaign_id, actor |
| `CampaignRejected` | Campaign / Approval | Aprender | reason |
| `CampaignScheduled` | Campaign | Ejecutar | scheduled_at |
| `CampaignPublished` | Campaign | Ejecutar | campaign_id |
| `CampaignCompleted` | Campaign | Medir | metrics_summary |
| `ContentCreated` | Content | Crear | content_id |
| `FlyerGenerated` | MediaAsset | Crear | asset_id, campaign_id? |
| `PublicationDraftCreated` | Publication | Crear | publication_id |
| `PublicationApproved` | Publication / Approval | Ejecutar | publication_id |
| `PublicationPublished` | Publication | Ejecutar | external_post_id |
| `PublicationFailed` | Publication | Medir | error |
| `ContentRejected` | Publication / Approval | Aprender | reason |
| `CommentReceived` | Channel connector | Observar | channel, external_id |

---

## Comercial

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `LeadCreated` | Lead | Observar | lead_id, source |
| `LeadAssigned` | Lead | Planificar | assignee_id |
| `LeadStaleDetected` | Lead / Insight | Analizar | days_stale |
| `OpportunityIdentified` | Opportunity | Analizar | opportunity_id, stage |
| `CustomerConverted` | Customer | Medir | customer_id, lead_id |
| `CustomerLost` | Customer | Aprender | reason |
| `ConversationLogged` | Contact | Observar | channel, summary |

---

## Roadmap y analítica

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `DailyRoadmapGenerated` | DailyRoadmap | Planificar | roadmap_id, date |
| `RecommendationCreated` | Recommendation | Planificar | recommendation_id, action |
| `RecommendationAccepted` | Recommendation | Ejecutar | actor |
| `RecommendationRejected` | Recommendation | Aprender | reason |
| `RecommendationCompleted` | Recommendation | Medir | outcome |
| `MetricRecorded` | Metric | Medir | source_type, source_id, name, value |
| `ROIAssessed` | ROI | Analizar | scope_type, scope_id |
| `InsightGenerated` | Insight | Analizar | summary |
| `ExperimentStarted` | Experiment | Planificar | experiment_id |
| `ExperimentConcluded` | Experiment | Aprender | result |

---

## Automatización

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `WorkflowTriggered` | Trigger | Ejecutar | workflow_id |
| `ActionExecuted` | Action | Ejecutar | action_id |
| `ActionFailed` | Action | Medir | error |
| `ApprovalRequested` | Approval | Ejecutar | approval_id, target |
| `ApprovalGranted` | Approval | Ejecutar | decided_by |
| `ApprovalDenied` | Approval | Aprender | reason |
| `TaskCreated` | Task | Planificar | task_id, assignee |

---

## Producto

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `ProductUpdated` | Product | Aprender | product_id, fields[] |
| `PromotionStarted` | Promotion | Ejecutar | promotion_id |
| `PromotionEnded` | Promotion | Medir | promotion_id |
| `PriceChanged` | Offer | Aprender | offer_id, price |

---

## Auditoría transversal

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `AuditRecorded` | Cualquier agregado | — | action, entity_ref, result |

---

## Envelope común (Corporate Memory)

Todo evento se persiste con esta forma en `memory_events`:

```json
{
  "event_id": "uuid",
  "event_type": "CampaignPublished",
  "tenant_id": "easytech",
  "brand_id": "default",
  "actor": { "type": "user", "id": "usr_..." },
  "timestamp": "2026-06-26T12:00:00Z",
  "entity_refs": [
    { "type": "Campaign", "id": "cmp_..." },
    { "type": "Publication", "id": "pub_..." }
  ],
  "payload": { "external_post_id": "urn:li:..." },
  "summary": "Campaña Q3 publicada en LinkedIn",
  "correlation_id": "optional-trace-id"
}
```

**Reglas envelope:**

- `tenant_id` obligatorio
- `brand_id` cuando el evento es scoped a marca
- `entity_refs` mínimo 1 referencia al agregado origen
- `summary` legible para Console y búsqueda

---

## Referencias

- [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)
- [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md)
- [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md)
