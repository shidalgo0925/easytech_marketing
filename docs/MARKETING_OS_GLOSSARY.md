# Marketing OS — Glosario oficial

**Versión:** 1.0 · Sprint 1 cerrado  
**Constitución:** [MARKETING_OS_CONSTITUTION.md](MARKETING_OS_CONSTITUTION.md)  
**Dominio:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)

---

## Términos de producto

| Término | Definición |
|---------|------------|
| **Marketing OS** | Sistema Operativo de Marketing — plataforma |
| **Director de Marketing Digital** | Metáfora del producto hacia el usuario |
| **Marketing Console** | Centro de operaciones (shell, roadmap, chat) |
| **Empresa Viva** | Conocimiento nunca estático; sync continuo |
| **Ciclo permanente** | Observar → Analizar → Planificar → Crear → Ejecutar → Medir → Aprender |

---

## Entidades ↔ términos (1:1)

| Término EN | Español | Entidad §1 |
|------------|---------|------------|
| Tenant | Cliente SaaS | 1.1 Tenant |
| Company / Empresa | Empresa | 1.1 Empresa |
| Brand / Marca | Marca | 1.1 Marca |
| User | Usuario | 1.1 Usuario |
| Role | Rol | 1.1 Rol |
| Team | Equipo | 1.1 Equipo |
| CompanyBrain | Cerebro empresa | 1.2 CompanyBrain |
| CorporateMemory | Memoria corporativa | 1.2 CorporateMemory |
| MemoryEvent | Evento memoria | unidad en CorporateMemory |
| ProductKnowledge | Conocimiento producto | 1.2 ProductKnowledge |
| KnowledgeArticle | Artículo KB | 1.2 KnowledgeArticle |
| FAQ | Pregunta frecuente | 1.2 FAQ |
| Competitor | Competidor | 1.2 Competitor |
| CaseStudy | Caso de éxito | 1.2 CaseStudy |
| BrandGuide | Manual de marca | 1.3 BrandGuide |
| MediaAsset / Asset | Activo multimedia | 1.4 MediaAsset |
| Flyer | Flyer | 1.4 subtipo MediaAsset |
| Product | Producto | 1.5 Product |
| ProductCategory | Categoría | 1.5 ProductCategory |
| Promotion | Promoción | 1.5 Promotion |
| Offer | Oferta / precio | 1.5 Offer |
| CTA | Llamada a la acción | 1.5 CTA |
| Campaign | Campaña | 1.6 Campaign |
| Publication | Publicación | 1.6 Publication |
| Content | Contenido | 1.6 Content |
| Channel | Canal | 1.6 Channel |
| EditorialCalendar | Calendario editorial | 1.6 EditorialCalendar |
| Lead | Lead | 1.7 Lead |
| Opportunity | Oportunidad | 1.7 Opportunity |
| Customer | Cliente | 1.7 Customer |
| Contact | Contacto | 1.7 Contact |
| SalesPipeline | Embudo ventas | 1.7 SalesPipeline |
| Workflow | Flujo automatización | 1.8 Workflow |
| Trigger | Disparador | 1.8 Trigger |
| Action | Acción | 1.8 Action |
| Approval | Aprobación | 1.8 Approval |
| Task | Tarea | 1.8 Task |
| Scheduler | Programador | 1.8 Scheduler |
| DailyRoadmap | Roadmap del día | 1.9 DailyRoadmap |
| Recommendation | Recomendación | 1.9 Recommendation |
| KPI | Indicador clave | 1.9 KPI |
| Metric | Métrica | 1.9 Metric |
| ROI | Retorno inversión | 1.9 ROI |
| Insight | Insight analítico | 1.9 Insight |
| Experiment | Experimento | 1.9 Experiment |
| MarketingPlan | Plan marketing | 1.10 subdominio v1.1 |

---

## Mapeo legacy → dominio

| Legacy | Dominio | Tabla |
|--------|---------|-------|
| `tenant_id` | Tenant | `tenants` |
| `app_id` | Brand | `brands.legacy_app_id` |
| `content_queue` | Publication | `publications` |
| `business_context.json` | CompanyBrain | `company_profiles` |
| `knowledge/*.md` | KnowledgeArticle | `knowledge_articles` |
| `MarketingPlan` | Planificar v1.1 | JSON (sin tabla) |
| `assistant_audit.jsonl` | CorporateMemory | `memory_events` |
| `products.json` | Product | `products` |
| `flyers/*.png` | MediaAsset (flyer) | `media_assets` |

---

## Fases del ciclo

| Fase | Pregunta |
|------|----------|
| Observar | ¿Qué está pasando? |
| Analizar | ¿Qué significa? |
| Planificar | ¿Qué hacemos? |
| Crear | ¿Qué producimos? |
| Ejecutar | ¿Qué hicimos en el mundo real? |
| Medir | ¿Qué resultado tuvo? |
| Aprender | ¿Qué guardamos para mañana? |

---

## Roles (Marketing Console)

Director General · Gerente Comercial · Gerente de Marketing · Community Manager · Diseñador · Vendedor

Mapean a `assignee_role` en Recommendation y permisos en `roles`.

---

## Reglas mnemotécnicas

- **El dominio gobierna; el código implementa.**
- **La memoria es el activo.**
- **¿Ayuda a vender más?** (Principio 1)
- **Buscar antes de crear** (Principio 3)
- **Memoria no se borra** (Principios 5, 12)
- **Principio 19** — 10 preguntas pre-código

---

## Referencias

- [MARKETING_OS_DOMAIN_PERSISTENCE.md](MARKETING_OS_DOMAIN_PERSISTENCE.md)
- [EMACCION_TENANT_VS_APP.md](EMACCION_TENANT_VS_APP.md)
