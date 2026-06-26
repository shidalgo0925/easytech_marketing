# EM+Acción — Análisis de brecha (Gap Analysis)

**Auditoría:** 2026-06-22 · **Commit base:** `6732a05` · **VPS:** `/opt/easytech_marketing`

---

## 1. Resumen ejecutivo

| | Hoy | Objetivo V1 |
|---|-----|-------------|
| **Rol** | Publicador + dashboard | Motor comercial IA |
| **Completitud** | ~35% base técnica | 100% flujo comercial |
| **CRM** | Odoo | EN1 |
| **Prioridad** | Consolidar + Fase E | Generar demanda real |

**Conclusión:** La base existe. Falta el núcleo: oportunidades → producto → campaña → landing → EN1 → medición.

---

## 2. Inventario por área

### 2.1 Base técnica (Fase A) — 70%

| Item | Hoy | Gap |
|------|-----|-----|
| Git + deploy | ✅ | — |
| systemd :8092 | ✅ | — |
| Dashboard protegido | ✅ | — |
| Backup .env | ❌ | Crear procedimiento cifrado |
| DEV/PROD separado | ❌ | Definir entornos |
| Archivos huérfanos | 🔄 | Versionar o limpiar knowledge local |

### 2.2 Conectores (Fase B) — 45%

| Canal | Hoy | Gap |
|-------|-----|-----|
| LinkedIn | ✅ 3 posts | Mantener |
| Facebook | ✅ listo | Validar 1ª publicación real |
| Instagram | ⏳ | `META_IG_USER_ID` |
| Google Business | ⏳ | OAuth completo |
| Blog / Email / X | ❌ | Crear desde cero |

### 2.3 Cola editorial (Fase C) — 60%

| Item | Hoy | Gap |
|------|-----|-----|
| content_queue.json | ✅ 22 posts | — |
| campaigns.json | ✅ | — |
| Estados draft/approved | ❌ | Modelo de estados |
| Generación IA | ❌ | Campaign Engine |
| Motor oportunidades | ❌ | Opportunity Engine |

### 2.4 Landings (Fase D) — 15%

| Landing | Hoy | Gap |
|---------|-----|-----|
| /guia/ | ✅ | — |
| Por producto (6) | ❌ | Crear todas |

### 2.5 Knowledge Engine (Fase E) — 25%

| Item | Hoy | Gap |
|------|-----|-----|
| knowledge/*.md | 🔄 8 fichas | Completar Converso, sectores, JSON |
| business_context.json | 🔄 | Integrar dashboard + API |
| knowledge_api.py | 🔄 | Integrar app.py |
| Matriz producto-sector | ❌ | Crear sectors.json |

### 2.6 Opportunity Engine (Fase F) — 0%

Todo pendiente: detección, clasificación, `opportunities.json`.

### 2.7 Campaign Engine (Fase G) — 0%

Todo pendiente: generación automática copy/imagen/CTA.

### 2.8 Publisher (Fase H) — 50%

| Item | Hoy | Gap |
|------|-----|-----|
| LinkedIn publisher | ✅ | — |
| Meta publisher | ✅ | IG sin token |
| publish_channel unificado | 🔄 | Estandarizar respuestas |
| Blog/Email | ❌ | — |

### 2.9 EN1 CRM (Fase I) — 0%

| Item | Hoy | Gap |
|------|-----|-----|
| en1_sync.py | ❌ | Crear módulo |
| Endpoint EN1 | ❌ | Credenciales + API |
| Routing lead | Odoo solo | EN1 + reglas |

### 2.10 Analytics (Fase J) — 20%

| Métrica | Hoy | Gap |
|---------|-----|-----|
| Leads Odoo por origen | ✅ | — |
| Clics UTM | ❌ | Tracking web |
| CTR / conversión real | ❌ | Analytics Engine |
| Aprendizaje | ❌ | Feedback loop |

### 2.11 Agentes (Fase K) — 0%

9 agentes documentados, ninguno implementado.

---

## 3. API — qué existe vs qué falta

### Existe ✅

```
/accio/dashboard/api/{summary,campaigns,calendar,metrics,flyers,connectors}
/accio/{status,content/queue,orders,tick}
/accio/run/{pipeline,publish-linkedin,publish-meta,publish-channel}
/accio/{files/tree,tasks,calendar}
```

### Falta ❌

```
/accio/config/business-context
/accio/knowledge
/accio/content/generate-topic
/accio/opportunities
/accio/campaigns/generate
/accio/analytics/clicks
/accio/en1/sync
```

---

## 4. Cambio de visión

### Antes

```
EMAcción → Publica
```

### Ahora

```
EMAcción → Detecta → Analiza → Aprende → Genera campañas
         → Publica → Captura leads → Mide → Mejora
```

---

## 5. Orden vs realidad

| Paso estratégico | Estado | % |
|------------------|--------|---|
| 1. EMAcción estable | 🔄 | 70% |
| 2. Landings por producto | ❌ | 15% |
| 3. EN1 CRM | ❌ | 0% |
| 4. Publicación automática | 🔄 | 50% |
| 5. Medición | 🔄 | 20% |
| 6. Optimización | ❌ | 0% |

**Ajuste recomendado:** insertar Fase E (Knowledge) y Fase F (Opportunity) **antes** de escalar landings y EN1.

---

## 6. Riesgos actuales

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Publicar sin KB | Contenido genérico / ruido | Fase E primero |
| Odoo como CRM final | No escala comercial EN1 | Fase I planificada |
| Archivos locales sin Git | Pérdida de trabajo Fase E | Versionar en este commit |
| Sin medición clics | No saber qué convierte | Fase J |
| Instagram sin token | Canal muerto | Completar Meta IG |

---

## 7. Próximos pasos (requieren GO)

| # | Acción | Fase |
|---|--------|------|
| 1 | Integrar Knowledge Engine al motor + dashboard | E |
| 2 | Completar fichas KB (Converso, sectores) | E |
| 3 | Opportunity Engine MVP (keywords → producto) | F |
| 4 | Primera landing `/eposone` o `/en1-eventos` | D |
| 5 | `en1_sync.py` cuando API EN1 disponible | I |
| 6 | Publicación real Facebook (validar) | B |
| 7 | Instagram OAuth + token | B |

---

## 8. Lo que NO se debe hacer sin GO

- Opportunity Engine runtime
- Campaign Engine runtime
- EN1 Sync runtime
- Analytics Engine runtime
- Nuevos conectores
- Cambios en producción / credenciales
- Publicaciones forzadas

---

## 9. Referencias

- `CONTEXTO.md` — estado operativo
- `ROADMAP.md` — fases A–K
- `EMACCION_ARCHITECTURE.md` — diseño objetivo
- `EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md` — Fase E detalle
