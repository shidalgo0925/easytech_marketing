# Marketing OS — Glosario oficial

**Versión:** 0.1 · Sprint 1  
**North star:** [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md)

---

## Términos de producto

| Término | Definición |
|---------|------------|
| **Marketing OS** | Sistema Operativo de Marketing — plataforma, no aplicación puntual |
| **Director de Marketing Digital** | Rol metáfora del producto hacia el usuario |
| **Marketing Console** | Centro de operaciones (dashboard, roadmap, chat, …) |
| **Empresa Viva** | Conocimiento nunca estático; sync continuo |
| **Ciclo permanente** | Observar → Analizar → Planificar → Crear → Ejecutar → Medir → Aprender |

---

## Agregados principales

| Término (EN) | Español | Descripción breve |
|--------------|---------|-------------------|
| **Tenant** | Tenant / cliente SaaS | Aislamiento multiempresa |
| **Empresa** | Empresa | Organización dentro del tenant |
| **Brand / Marca** | Marca | Línea de negocio promovible (≈ `app_id`) |
| **CompanyBrain** | Cerebro empresa | Perfil institucional curado |
| **CorporateMemory** | Memoria corporativa | Historial append-only de todo |
| **ProductKnowledge** | Conocimiento producto | KB curada por producto |
| **Campaign** | Campaña | Iniciativa marketing con objetivo |
| **Publication** | Publicación | Unidad en cola/redes |
| **Recommendation** | Recomendación | Propuesta Roadmap con responsable |
| **Approval** | Aprobación | Gate humano antes de ejecutar |
| **Insight** | Insight | Conclusión analítica |
| **ROI** | Retorno | ¿Qué vendió más? |

---

## Mapeo legacy → dominio

| Legacy | Dominio |
|--------|---------|
| `tenant_id` | Tenant |
| `app_id` | Marca (Brand) |
| `content_queue` | Publication (cola) |
| `business_context.json` | CompanyBrain (semilla) |
| `knowledge/*.md` | KnowledgeArticle |
| `MarketingPlan` | Subdominio Planificar (v1.1 congelado) |
| `assistant_audit.jsonl` | CorporateMemory (sin modelo) |

---

## Fases del ciclo

| Fase | Pregunta que responde |
|------|------------------------|
| **Observar** | ¿Qué está pasando? |
| **Analizar** | ¿Qué significa? |
| **Planificar** | ¿Qué hacemos? |
| **Crear** | ¿Qué producimos? |
| **Ejecutar** | ¿Qué hicimos en el mundo real? |
| **Medir** | ¿Qué resultado tuvo? |
| **Aprender** | ¿Qué guardamos para mañana? |

---

## Roles (Marketing Console)

Director General · Gerente Comercial · Gerente de Marketing · Community Manager · Diseñador · Vendedor

---

## Reglas mnemotécnicas

- **El dominio gobierna; el código implementa.**
- **La memoria es el activo.**
- **¿Ayuda a vender más?**
- **5 preguntas por desarrollo:** ver [MARKETING_OS_DEV_FRAMEWORK.md](MARKETING_OS_DEV_FRAMEWORK.md)

---

## Referencias

- [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)
- [EMACCION_TENANT_VS_APP.md](EMACCION_TENANT_VS_APP.md)
