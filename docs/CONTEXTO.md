# Contexto técnico — EM+Acción

Documento maestro para operadores, programadores y agentes IA.  
**Actualizado:** 2026-06-22 · **Repo:** `github.com/shidalgo0925/easytech_marketing` · **Commit base:** `6732a05`

---

## 1. Objetivo estratégico

**EMAcción** es el **motor comercial central** de EasyTech — no un publicador de contenido.

Debe: conocer el portafolio · detectar oportunidades · clasificar · generar campañas · publicar · capturar leads · EN1 CRM · medir · optimizar.

Los productos (EN1, EPOSOne, EPayRoll, Odoo, EClassOne…) son **destinos**, no motores de marketing independientes.

---

## 2. Estado técnico actual (jun 2026)

### Repositorio

| Item | Valor |
|------|-------|
| Repo | `github.com/shidalgo0925/easytech_marketing` |
| VPS prod | `/opt/easytech_marketing` |
| Rama | `main` |
| Commit base auditoría | `6732a05` |

### Motor

| Item | Valor |
|------|-------|
| Servicio | `easytech-accio-engine` |
| Puerto | `8092` |
| Auth | `ACCIO_API_KEY` |
| Infra rutas | `/accio/` (sin renombrar) |

### Dashboard EM+Acción

- URL: https://n8n.etsrv.site/accio/dashboard/
- Estilo: verde bosque + cobre (`accio-design.css`)
- Tabs: Resumen · Campañas · Calendario · Métricas · Flyers · Conectores

### Cola editorial

| Métrica | Valor |
|---------|-------|
| Posts en cola | 22 |
| Publicados LinkedIn | 3 |
| Próximo | `linkedin_04_fe_errores` (30 jun 2026) |
| Regla interina | 3 valor + 1 venta (75/25) |

Archivos: `content_queue.json` · `campaigns.json` · `calendar.json` · `orders.json` · `tasks.json`

### CRM

| | Actual | Objetivo |
|---|--------|----------|
| CRM | **Odoo** (`easydb.etsrv.site`) | **EN1 CRM** |
| Scraper | `scraper_panama.py` → CSV → Odoo | Mantener + EN1 |
| Landing | `/guia/` (1 genérica) | Landings por producto |

---

## 3. Conectores

| Canal | Estado |
|-------|--------|
| LinkedIn | ✅ Publicó 3 posts |
| Facebook | ✅ OAuth OK, publisher listo |
| Instagram | ⏳ Falta `META_IG_USER_ID` |
| Google Business | ⏳ Falta OAuth |
| YouTube / TikTok / Ads | ❌ Stub |
| X / Blog / Email | ❌ No existe |

Registro: `Marketing/accio/connectors.json`

---

## 4. API activa

### Dashboard (requiere `ACCIO_API_KEY`)

```
GET /accio/dashboard/api/summary
GET /accio/dashboard/api/campaigns
GET /accio/dashboard/api/calendar
GET /accio/dashboard/api/metrics
GET /accio/dashboard/api/flyers
GET /accio/dashboard/api/connectors
```

### Motor

```
GET  /accio/health
GET  /accio/status
GET  /accio/content/queue
GET  /accio/orders
POST /accio/orders
POST /accio/tick
POST /accio/run/pipeline
POST /accio/run/publish-linkedin
POST /accio/run/publish-meta
POST /accio/run/publish-channel
POST /accio/content/queue
POST /accio/calendar
GET  /accio/files/tree
GET  /accio/tasks
```

### No existe aún

- Oportunidades / clasificación IA
- Generador de campañas IA
- Knowledge API integrada
- EN1 sync
- Analítica de clics

---

## 5. Servicios systemd

| Servicio | Puerto | Rol |
|----------|--------|-----|
| `easytech-accio-engine` | 8092 | Dashboard + API |
| `easytech-meta-oauth` | 8093 | Facebook/IG |
| `easytech-linkedin-oauth` | 8091 | LinkedIn |
| `easytech-google-oauth` | 8094 | Google |
| `easytech-tiktok-oauth` | 8095 | TikTok |
| `easytech-lead-api` | 8080 | Leads → Odoo |

Reiniciar `easytech-accio-engine` tras cambios en `.env`.

---

## 6. Medición actual

| Métrica | Estado |
|---------|--------|
| Leads Odoo por origen | ✅ |
| Posts publicados | ✅ |
| Conversión guía/post | ⚠️ Aproximada |
| Clics UTM / landing | ❌ |
| Ventas / demos | ❌ |
| Aprendizaje automático | ❌ |

---

## 7. Brecha resumida

```
HOY                              OBJETIVO V1
──────────────────────────────────────────────────
Publicador + dashboard        →  Agente comercial IA
Cola manual + cron            →  Opportunity Engine
Flyers estáticos              →  Campaign Engine + imágenes IA
Odoo CRM                      →  EN1 CRM
1 landing                     →  Landings por producto
LI + FB parcial               →  LI+FB+IG+Blog+Email
Sin Knowledge operativo       →  Knowledge Engine (Fase E)
```

Detalle: `docs/EMACCION_GAP_ANALYSIS.md`

---

## 8. Arquitectura objetivo

```
Internet / Redes
      │
      ▼
EMAcción (Agente Comercial IA)
      │
      ├── Knowledge Engine
      ├── Opportunity Engine
      ├── Campaign Engine
      ├── Publisher
      └── Analytics
      │
      ▼
Producto (EN1 · EPOSOne · EPayRoll · Odoo · EClassOne)
      │
      ▼
Landing específica → EN1 CRM → Demo → Cliente
```

Detalle: `docs/EMACCION_ARCHITECTURE.md`

---

## 9. Fase E — Knowledge Engine (prioridad inmediata)

Archivos iniciados (versionados en Git):

```
Marketing/accio/business_context.json
Marketing/accio/editorial_rules.json
Marketing/knowledge/
Motor_Tecnico/accio_engine/knowledge_api.py  ← preparatorio, NO integrado a app.py aún
```

Detalle: `docs/EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md`

---

## 10. URLs

| Recurso | URL |
|---------|-----|
| Dashboard | https://n8n.etsrv.site/accio/dashboard/ |
| API | https://n8n.etsrv.site/accio/ |
| Meta OAuth | https://n8n.etsrv.site/meta/ |
| Guía leads | https://n8n.etsrv.site/guia/ |
| Odoo CRM | https://easydb.etsrv.site |
| Meta Developers | https://developers.facebook.com/apps/944229778615599/ |

---

## 11. Orden de implementación

1. Fase A — Base técnica estable
2. Fase E — Knowledge Engine
3. Fase F — Opportunity Engine
4. Fase D — Landings por producto
5. Fase I — EN1 CRM
6. Fase H — Publisher multicanal completo
7. Fase J — Analítica
8. Fase K — Agentes especializados

Roadmap completo: `docs/ROADMAP.md`

---

## 12. Contacto y CTA

- CTA: **DIAGNÓSTICO**
- WhatsApp: +507 6688-4938
- Email: easytechservices25@gmail.com
- Guía: https://n8n.etsrv.site/guia/

---

## 13. Reglas para programadores

- **No implementar runtime sin GO explícito.**
- No tocar `.env` ni credenciales en commits.
- No reiniciar producción sin GO.
- Documentación primero; código después.
- EN1, EPOSOne, EPayRoll no hacen marketing propio — EMAcción es el cerebro.
