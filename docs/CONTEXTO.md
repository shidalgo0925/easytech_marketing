# Contexto técnico — EM+Acción

Documento maestro para operadores, programadores y agentes IA.  
**Actualizado:** 2026-06-26 · **Repo:** `github.com/shidalgo0925/easytech_marketing`

**Snapshot operativo (sesión jun 2026):** [EMACCION_CONTEXTO_OPERATIVO.md](EMACCION_CONTEXTO_OPERATIVO.md)  
**Estado fases V2:** [EMACCION_V2_ESTADO.md](EMACCION_V2_ESTADO.md)

---

## 1. Objetivo estratégico

**EMAcción V2** es el **Agente Comercial IA multi-empresa** del ecosistema EasyTech.

**Plan maestro:** `docs/EMACCION_V2_PLAN_MAESTRO.md` · **Estado:** `docs/EMACCION_V2_ESTADO.md`

Debe servir a **EasyTech**, **Relatic** y futuros clientes con **un solo motor** y datos **100% separados** por empresa (`tenant_id` interno).

**Modelo de producto:** plataforma SaaS multi-tenant. **Tenant** = empresa cliente; **App** = línea/marca/producto a promocionar dentro del tenant. Ver `docs/EMACCION_TENANT_VS_APP.md`. La UI legacy dice *Empresa* (= tenant); `tenant_id` es infraestructura.

**Regla V2:** No implementar una fase hasta cerrar la anterior (A → B → C → D → … → P).

---

## 2. Estado técnico actual (jun 2026)

### Repositorio

| Item | Valor |
|------|-------|
| Repo | `github.com/shidalgo0925/easytech_marketing` |
| VPS prod | `/opt/easytech_marketing` |
| Rama | `main` |

### Motor

| Item | Valor |
|------|-------|
| Servicio | `easytech-accio-engine` |
| Puerto | `8092` |
| Auth sesión | Flask + `auth.db` (usuarios) + `ACCIO_API_KEY` (integraciones) |
| Infra rutas | `/accio/` (sin renombrar) |

### Acceso y sesión

| Paso | Ruta |
|------|------|
| Login plataforma | `GET/POST /accio/login/` |
| Selector empresa | `GET /accio/empresas/` |
| Entrar empresa | `POST /accio/auth/empresas/{tenant_id}/entrar` |
| Dashboard | `GET /accio/dashboard/{tenant_id}/` |

Auth DB: `Marketing/tenants/.secrets/auth.db` (`users`, `user_tenants`).

### Dashboard EM+Acción

- URL principal: https://emaccion.etsrv.site/accio/dashboard/easytech/
- URL alternativa: https://n8n.etsrv.site/accio/dashboard/easytech/
- Estilo: verde bosque + cobre (`accio-design.css`)
- Tabs: Resumen · Campañas · Calendario · Métricas · Flyers · Conocimiento · Conectores · **Configuración**
- Header: selector **Empresa:** (cambio entre empresas asignadas)

### Cola editorial (easytech)

| Métrica | Valor |
|---------|-------|
| Posts en cola | ~22 |
| LinkedIn pendientes | ~8 |
| Publicados LinkedIn | 3 |
| Archivo | `Marketing/tenants/easytech/content_queue.json` |

También: `campaigns.json` · `calendar.json` · `orders.json` por tenant.

### Empresas registradas

| ID | Nombre | CRM | Datos |
|----|--------|-----|-------|
| `easytech` | Easy Technology Services | Odoo | Cola, campañas, KB completa |
| `relatic` | Relatic | EN1 | Tenant vacío (aislado) |

Registry: `Marketing/tenants/registry.json`

### CRM

| | Actual | Objetivo |
|---|--------|----------|
| EasyTech | **Odoo** (`easydb.etsrv.site`) | Mantener + opcional EN1 |
| Relatic | `crm_target: en1` | EN1 sync (pendiente) |
| Scraper | `scraper_panama.py` → CSV → Odoo | Mantener |
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

### Dashboard por empresa (sesión usuario o `ACCIO_API_KEY`)

```
GET /accio/{tenant_id}/dashboard/api/summary
GET /accio/{tenant_id}/dashboard/api/campaigns
GET /accio/{tenant_id}/dashboard/api/calendar
GET /accio/{tenant_id}/dashboard/api/metrics
GET /accio/{tenant_id}/dashboard/api/flyers
GET /accio/{tenant_id}/dashboard/api/connectors
GET /accio/{tenant_id}/dashboard/api/knowledge
GET /accio/{tenant_id}/settings/center
```

### Auth y empresas

```
POST /accio/login/                    # form login plataforma
GET  /accio/auth/status
GET  /accio/auth/empresas
POST /accio/auth/empresas/{id}/entrar
POST /accio/auth/logout
```

### Configuración (CRUD)

```
POST /accio/{tenant_id}/settings/usuarios      # sync auth.db
POST /accio/{tenant_id}/settings/productos
POST /accio/{tenant_id}/settings/landings
POST /accio/{tenant_id}/settings/variables
POST /accio/{tenant_id}/settings/empresas      # crear (super_admin)
POST /accio/{tenant_id}/settings/empresas/{id} # editar
POST /accio/{tenant_id}/settings/empresas/{id}/disable|enable
```

### Knowledge

```
GET    /accio/{tenant_id}/knowledge
GET    /accio/{tenant_id}/knowledge/{slug}
POST   /accio/{tenant_id}/knowledge              # crear
POST   /accio/{tenant_id}/knowledge/{slug}       # editar
DELETE /accio/{tenant_id}/knowledge/{slug}
POST   /accio/{tenant_id}/content/generate-topic
```

### Motor (legacy + tenant)

```
GET  /accio/health
POST /accio/{tenant_id}/run/pipeline
POST /accio/{tenant_id}/run/publish-linkedin
POST /accio/{tenant_id}/run/publish-meta
```

### Pendiente

- Oportunidades / clasificación IA
- EN1 sync
- Cron multi-empresa
- Analítica UTM / clics

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

## 9. Knowledge Engine

Integrado en motor y dashboard (tab Conocimiento):

```
Marketing/tenants/{id}/business_context.json
Marketing/tenants/{id}/editorial_rules.json
Marketing/tenants/{id}/knowledge/
Marketing/tenants/{id}/knowledge_manifest.json
Motor_Tecnico/accio_engine/knowledge_api.py
```

CRUD artículos KB desde UI. Generador de temas: `POST .../content/generate-topic`.

Detalle histórico: `docs/EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md`

---

## 10. URLs

| Recurso | URL |
|---------|-----|
| Dashboard easytech | https://emaccion.etsrv.site/accio/dashboard/easytech/ |
| Login | https://emaccion.etsrv.site/accio/login/ |
| API / health | https://emaccion.etsrv.site/accio/ |
| Proxy n8n | https://n8n.etsrv.site/accio/ |
| Meta OAuth | https://n8n.etsrv.site/meta/ |
| Guía leads | https://n8n.etsrv.site/guia/ |
| Odoo CRM | https://easydb.etsrv.site |
| Meta Developers | https://developers.facebook.com/apps/944229778615599/ |

---

## 11. Orden de implementación (V2)

Ver [ROADMAP.md](ROADMAP.md) y [EMACCION_V2_PLAN_MAESTRO.md](EMACCION_V2_PLAN_MAESTRO.md).

```
A Base → B Multi-tenant → C Config Center → D Knowledge → E Opportunity
→ F Campaign → G Image → H Publisher → I Landings → J CRM → K Analytics
→ L Learning → M Community → N Scheduler → O Automation → P API
```

**Fase activa:** **B** y **C** cerradas en código; siguiente: **D** Knowledge completo + **E** Opportunity.

---

## 12. Contacto y CTA

- CTA: **DIAGNÓSTICO**
- WhatsApp: +507 6688-4938
- Email: easytechservices25@gmail.com
- Guía: https://n8n.etsrv.site/guia/

---

## 13. Reglas para programadores

- **No implementar runtime sin GO explícito** (salvo fixes urgentes acordados).
- **No crear otro EMAcción por cliente** — un motor, muchas empresas (`tenant_id`).
- **Nada de datos mezclados** entre EasyTech y Relatic.
- UI: decir **Empresa**, no tenant.
- Usuarios de login: **auth.db** — al guardar usuarios en Configuración usar `sync_tenant_users`.
- Credenciales: **tenant_secrets.db** cifrado — no JSON visible en repo.
- Tras cambios en motor: `sudo systemctl restart easytech-accio-engine`.
- Tests: `venv/bin/python3 -m unittest tests/test_*.py -v`.
- Contexto sesión: `docs/EMACCION_CONTEXTO_OPERATIVO.md`.
- No tocar `.env` ni credenciales en commits.
- EN1, EPOSOne, EPayRoll no hacen marketing propio — EMAcción es el cerebro.
