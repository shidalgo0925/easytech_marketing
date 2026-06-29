# Marketing OS — Catálogo de Eventos de Dominio

**Versión:** 0.1 · Sprint 1  
**Regla:** todo evento alimenta **CorporateMemory**

Formato: `DomainEventName` · agregado origen · fase ciclo · payload mínimo

---

## Organización

| Evento | Origen | Fase | Payload clave |
|--------|--------|------|---------------|
| `TenantCreated` | Tenant | — | tenant_id |
| `TenantSuspended` | Tenant | — | reason |
| `CompanyProfileUpdated` | Empresa / CompanyBrain | Aprender | fields_changed[] |
| `BrandCreated` | Marca | Observar | brand_id, name |
| `BrandPaused` | Marca | Aprender | reason |
| `UserInvited` | Usuario | — | role |

---

## Conocimiento

| Evento | Origen | Fase |
|--------|--------|------|
| `CompanyBrainUpdated` | CompanyBrain | Aprender |
| `ProductKnowledgeUpdated` | ProductKnowledge | Aprender |
| `KnowledgeArticlePublished` | KnowledgeArticle | Aprender |
| `CaseStudyAdded` | CaseStudy | Aprender |
| `CompetitorIntelUpdated` | Competitor | Observar |
| `BrandingChanged` | BrandGuide | Aprender |

---

## Marketing

| Evento | Origen | Fase |
|--------|--------|------|
| `CampaignCreated` | Campaign | Planificar |
| `CampaignSubmittedForReview` | Campaign | Planificar |
| `CampaignApproved` | Campaign / Approval | Ejecutar |
| `CampaignRejected` | Campaign / Approval | Aprender |
| `CampaignScheduled` | Campaign | Ejecutar |
| `CampaignPublished` | Campaign / Publication | Ejecutar |
| `CampaignCompleted` | Campaign | Medir |
| `ContentCreated` | Content | Crear |
| `FlyerGenerated` | Flyer / Asset | Crear |
| `PublicationDraftCreated` | Publication | Crear |
| `PublicationApproved` | Publication / Approval | Ejecutar |
| `PublicationPublished` | Publication | Ejecutar |
| `PublicationFailed` | Publication | Medir |
| `ContentRejected` | Publication / Approval | Aprender |
| `CommentReceived` | Channel connector | Observar |

---

## Comercial

| Evento | Origen | Fase |
|--------|--------|------|
| `LeadCreated` | Lead | Observar |
| `LeadAssigned` | Lead | Planificar |
| `LeadStaleDetected` | Lead / Insight | Analizar |
| `OpportunityIdentified` | Opportunity | Analizar |
| `CustomerConverted` | Customer | Medir |
| `CustomerLost` | Customer | Aprender |
| `ConversationLogged` | Contact | Observar |

---

## Roadmap y analítica

| Evento | Origen | Fase |
|--------|--------|------|
| `RecommendationCreated` | Recommendation | Planificar |
| `RecommendationAccepted` | Recommendation | Ejecutar |
| `RecommendationRejected` | Recommendation | Aprender |
| `RecommendationCompleted` | Recommendation | Medir |
| `MetricRecorded` | Metric | Medir |
| `ROIAssessed` | ROI | Analizar |
| `InsightGenerated` | Insight | Analizar |
| `ExperimentStarted` | Experiment | Planificar |
| `ExperimentConcluded` | Experiment | Aprender |

---

## Automatización

| Evento | Origen | Fase |
|--------|--------|------|
| `WorkflowTriggered` | Trigger | Ejecutar |
| `ActionExecuted` | Action | Ejecutar |
| `ActionFailed` | Action | Medir |
| `ApprovalRequested` | Approval | Ejecutar |
| `ApprovalGranted` | Approval | Ejecutar |
| `ApprovalDenied` | Approval | Aprender |
| `TaskCreated` | Task | Planificar |

---

## Producto

| Evento | Origen | Fase |
|--------|--------|------|
| `ProductUpdated` | Product | Aprender |
| `PromotionStarted` | Promotion | Ejecutar |
| `PromotionEnded` | Promotion | Medir |
| `PriceChanged` | Offer | Aprender |

---

## Envelope común (Corporate Memory)

```json
{
  "event_id": "uuid",
  "event_type": "CampaignPublished",
  "tenant_id": "easytech",
  "brand_id": "en1",
  "actor": { "type": "user|system", "id": "..." },
  "timestamp": "ISO-8601",
  "entity_refs": [{ "type": "Campaign", "id": "..." }],
  "payload": {},
  "correlation_id": "optional"
}
```

---

## Referencias

- [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)
- [MARKETING_OS_DOMAIN_SERVICES.md](MARKETING_OS_DOMAIN_SERVICES.md)
