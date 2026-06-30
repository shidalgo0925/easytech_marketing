# EM+Acción — Contexto operativo (snapshot)

**Fecha:** 2026-06-30  
**Repo:** `/opt/easytech_marketing` · **Servicio:** `easytech-accio-engine` (:8092)  
**Bitácora:** `docs/sessions/2026-06-29-vs1-ux.md`

Documento de continuidad para operadores y agentes. Complementa `docs/CONTEXTO.md` y `docs/EMACCION_V2_ESTADO.md`.

---

## 1. Modelo de producto (acordado)

**EM+Acción = SaaS multi-tenant.** Documento canónico: `docs/EMACCION_TENANT_VS_APP.md`.

| Nivel | Qué es | Ejemplos | Interno |
|-------|--------|----------|---------|
| **Tenant** | Empresa que usa EM+Acción | ETS, Modecosa, IIUS, Relatic | `tenant_id` |
| **App** | Línea/marca/producto a promocionar | EN1, EPayRoll, Diplomados | `app_id` |

| Concepto UI | Concepto interno |
|-------------|------------------|
| Empresa (selector login) | **Tenant** — `tenant_id` + `Marketing/tenants/{id}/` |
| App / línea | **App** — `Marketing/tenants/{id}/apps/` |
| Administrador del tenant | `tenant_admin` |
| Super administrador plataforma | `super_admin` |

Cada **tenant** tiene aislado: usuarios, conectores, CRM, configuración.  
Cada **app** tiene (objetivo): cola, campañas, flyers, knowledge — hoy la app `default` usa la cola del tenant (compat).

**Reglas:** Nunca crear un tenant para representar una App. Todo contenido lleva `tenant_id` + `app_id`.

**EN1** (`/admin/organizations`): producto SaaS aparte; referencia en `Marketing/tenants/.en1/reference_organizations.json`. Sync futuro `organization_id` ↔ `tenant_id`.

---

## 2. Flujo de acceso

```
GET /accio/login/          → Login plataforma (email + contraseña)
        │
        ├─ 1 empresa  → /accio/plan/{id}/   (Inicio)
        └─ N empresas → /accio/empresas/  → elegir → POST /accio/auth/empresas/{id}/entrar → /accio/plan/{id}/
```

| Ruta | Uso |
|------|-----|
| `/accio/producto/` | **Landing producto EM+Acción** (pública) |
| `/accio/login/` | Login sin empresa en URL |
| `/accio/empresas/` | Selector de empresa |
| `/accio/dashboard/` | Vista **Operaciones** (legacy): redirige a dashboard del tenant en sesión |
| `/accio/dashboard/{tenant_id}/` | Operaciones avanzadas (cola, CRM, conectores, config) |
| `/accio/plan/` | **Home** — redirige a plan del tenant en sesión |
| `/accio/plan/{tenant_id}/` | **Inicio** — módulo Plan VS1 (5 pantallas) |
| `/accio/{tenant_id}/legal/` | Documentos legales por tenant |
| `/accio/login/{tenant_id}/` | Login legacy por empresa (compat) |

**Auth:** SQLite `Marketing/tenants/.secrets/auth.db`  
Tablas: `users`, `user_tenants` (rol por empresa).

**Usuario operador:** `shidalgo@easytech.services` · rol global `super_admin` · acceso a todos los tenants.

---

## 3. Landing de producto (SaaS enterprise v2 — 2026-06-27)

Página comercial oficial — **no** landing por tenant. Spec: `docs/LANDING_EMACCION_SPEC_v1.md` (v2 SaaS).

| Campo | Valor |
|-------|-------|
| **URL** | https://emaccion.etsrv.site/accio/producto/ |
| **Estilo** | SaaS empresarial premium (referencia Twilio/HubSpot, marca EasyTech) |
| **Nav** | Plataforma · Soluciones · Integraciones · Casos · Precios · Recursos · Contacto |
| **Hero** | Foto real + iframe dashboard + conectores |
| **Video** | Demo interactivo 5 pasos (`#video`) — MP4 pendiente |
| **Precios** | Starter $49 · Business $149 · Enterprise $499+ · Founders $99 |
| **Fotos** | `assets/photos/` |
| **Previews** | `previews/*.html` (UI real) |
| **Leads** | `POST /accio/producto/lead` → Odoo |

**Logout** → `/accio/producto/`

**Pendiente:** video MP4, PNG capturas autenticadas, nginx raíz → producto.

---

## 4. Dashboard — pestañas

| Pestaña | Contenido |
|---------|-----------|
| Operaciones | KPIs, cola posts, leads Odoo, órdenes (vista avanzada; home = `/accio/plan/`) |
| Campañas | `campaigns.json` |
| Calendario | `calendar.json` |
| Métricas | Odoo + LinkedIn |
| Flyers | Biblioteca assets |
| Conocimiento | Contexto IA + KB + generador temas |
| Conectores | Estado multicanal |
| Configuración | Centro de configuración (13 sub-secciones) |

Header: selector **Empresa** + nombre comercial. Barra de progreso al arrancar (~5 s).

Pestaña **Plan** del dashboard redirige a `/accio/plan/{tenant}/` (módulo VS1).

---

## 4b. Vertical Slice 1 — Plan de Marketing (jun 2026)

**Estado:** Implementado en repo · **sin deploy producción** hasta cierre UX.

| Pantalla | Ruta / nav | UX producto |
|----------|------------|-------------|
| 1 Inicio | Sidebar · Inicio | ✅ Revisada |
| 2 Crear Plan | Sidebar · Plan | ✅ Revisada |
| 3 Activar Plan | Tras guardar plan | ⏳ Pendiente |
| 4 Contexto | Sidebar · Contexto | ✅ Revisada |
| 5 Propuesta | Sidebar · Propuestas | ⏳ Pendiente |

**API v1:** `/api/v1/tenants/{tenant}/apps/{app}/marketing-plans` (+ `marketing-context`, `planner/proposals`)

**Docs:** `docs/VERTICAL_SLICE_1.md` · `docs/MARKETING_PLAN_DOMAIN_v1.1.md`

**Evidencia UX:** `Marketing/deliverables/vertical_slice_1/`

**Regla:** iteración producto pantalla por pantalla; no reiniciar servicio en prod sin GO final.

---

## 5. Configuration Center — CRUD

| Sección | CRUD | Backend |
|---------|------|---------|
| Información general | Empresa + branding + contexto IA | `tenant_provisioning`, `knowledge_api` |
| Usuarios | + fila, editar, eliminar → **auth.db** | `auth_service.sync_tenant_users` |
| Roles | + rol, permisos csv | `users.json` |
| Productos | + producto, eliminar fila | `products.json` |
| CRM | Campos cifrados | `tenant_secrets.db` |
| Conectores | Campos + Probar | `tenant_secrets.db` |
| Landings | + ruta | `landings.json` |
| Publicación | Reglas editoriales | `publication.json` |
| Variables | + variable pública + secretos | `variables.json` + secrets |
| IA | Modelo temas/imagen | `ai_config.json` |
| Logs | Lectura | `logs/accio_tick.log` |
| Backups | Ejecutar script | `scripts/backup_secrets.sh` |
| Seguridad | API key + auditoría | `tenant_secrets` + `audit.log` |

**Empresas (solo `super_admin`):** crear, editar, suspender, reactivar.

### Matriz de roles

| Rol | Alcance | Configuración |
|-----|---------|---------------|
| `super_admin` | Toda la plataforma | Todos los tenants + crear/suspender orgs |
| `tenant_admin` | Tenants asignados | Productos, landings, usuarios, conectores |
| `marketing_operator` | Tenant asignado | Publicar; sin Configuración |
| `viewer` | Tenant asignado | Solo lectura |

`super_admin` no puede editarse/borrarse desde UI de tenant.

---

## 6. Tenants activos (jun 2026)

| tenant_id | display_name | Dominio | Estado datos |
|-----------|--------------|---------|--------------|
| `easytech` | Easy Technology Services | easytech.services | Cola ~22 posts, KB, conectores LI+FB |
| `relatic` | Relatic Panamá | relaticpanama.org | Contexto, 25 productos, landings, legal |

### Relatic — archivos clave

| Recurso | Ubicación |
|---------|-----------|
| Contexto comercial | `Marketing/tenants/relatic/business_context.json` |
| Catálogo marketing | `Marketing/tenants/relatic/products.json` |
| Rutas sitio | `Marketing/tenants/relatic/landings.json` |
| Legal (HTML) | `Marketing/tenants/relatic/legal/` |
| Hub legal | https://emaccion.etsrv.site/accio/relatic/legal/ |

Sitio referencia: https://relaticpanama.org/

---

## 7. Archivos clave en código

| Archivo | Rol |
|---------|-----|
| `Motor_Tecnico/accio_engine/static/plan_slice.*` | UI Vertical Slice 1 (5 pantallas) |
| `Motor_Tecnico/accio_engine/marketing_plan_*` | Dominio + API v1 Plan de Marketing |
| `Motor_Tecnico/accio_engine/marketing_context_builder.py` | Context Builder V1 |
| `Motor_Tecnico/accio_engine/marketing_planner.py` | Planner 3 propuestas |
| `Motor_Tecnico/accio_engine/marketing_app.py` | Modelo Tenant → Apps, paths, provision |
| `Motor_Tecnico/accio_engine/editorial.py` | Estados editoriales y transiciones |
| `Motor_Tecnico/accio_engine/leads_store.py` | Leads locales con tenant/app/UTM |
| `Motor_Tecnico/accio_engine/metrics_store.py` | Eventos métricos por tenant/app |
| `Motor_Tecnico/accio_engine/app.py` | Rutas HTTP, landing, legal, leads, cola editorial |
| `Motor_Tecnico/accio_engine/auth_service.py` | Login, RBAC, protección super_admin |
| `Motor_Tecnico/accio_engine/static/emaccion/` | Landing producto |
| `Motor_Tecnico/accio_engine/static/dashboard.html` | UI principal |
| `Motor_Tecnico/accio_engine/static/accio-design.css` | Design system |
| `Marketing/tenants/registry.json` | Registry tenants |

**Reiniciar tras cambios:** `sudo systemctl restart easytech-accio-engine`

---

## 8. Procesos internos (GO 2026-06-27)

| Capacidad | Estado |
|-----------|--------|
| Modelo Apps (`profile`, `branding`, `knowledge`, cola, calendario, métricas) | ✅ `provision_all_apps()` |
| Cola por app `tenants/{id}/apps/{app_id}/content_queue.json` | ✅ EasyTech default sigue en raíz |
| Selector Tenant + App en dashboard | ✅ |
| Estados editoriales (`draft` … `archived`, legacy `pending`) | ✅ |
| PATCH `/accio/{tenant}/content/queue/{post_id}` | ✅ |
| Conectores con `tenant_id` + `app_id` | ✅ LinkedIn, Meta, channel, stub |
| Leads locales + Odoo landing | ✅ `leads.json` |
| Métricas por app | ✅ `metrics/events.jsonl` |

**Pendiente operativo**

| Ítem | Prioridad |
|------|-----------|
| Flyer #10 IIUS (PNG dueño) | Alta |
| Home nginx → `/accio/producto/` | Media (requiere GO) |
| Capturas reales dashboard en landing | Media |
| Legal Relatic — revisión abogado | Media |
| Instagram / Google Business conectores | Media |
| Cron/publicadores multi-tenant | Alta |
| Wizard onboarding 7 pasos | Alta |
| Migrar posts de producto a colas por App | ✅ `migrate_queue_by_app.py` |
| Vista **Publicaciones** + historial filtrable | ✅ |
| **Asistente EM+Acción** (chat + órdenes aprobables) | ✅ |

---

## 9. Reglas para agentes

1. **Diagnóstico → plan → GO → ejecutar.** No implementar sin GO explícito.
2. **No commitear** sin pedido del usuario.
3. **No mezclar datos** entre tenants.
4. Tras cambios en `app.py` / estáticos → reiniciar servicio.
5. UI: decir **Empresa**, no tenant (salvo docs técnicos).
6. URL pública plataforma: **`emaccion.etsrv.site`** (no `n8n.etsrv.site` para la app).
7. Marca: **EM+Acción** (no “EMAccion Command Center”).

---

## 10. URLs

| Recurso | URL |
|---------|-----|
| **Landing producto** | https://emaccion.etsrv.site/accio/producto/ |
| Dashboard easytech | https://emaccion.etsrv.site/accio/dashboard/easytech/ |
| **Plan VS1** | https://emaccion.etsrv.site/accio/plan/easytech/ |
| Dashboard relatic | https://emaccion.etsrv.site/accio/dashboard/relatic/ |
| Login | https://emaccion.etsrv.site/accio/login/ |
| Legal Relatic | https://emaccion.etsrv.site/accio/relatic/legal/ |
| Health | https://emaccion.etsrv.site/accio/health |
| Odoo CRM | https://easydb.etsrv.site |
| Guía leads (legacy) | https://n8n.etsrv.site/guia/ |
| OAuth / n8n proxy | https://n8n.etsrv.site/accio/ |

**Contacto:** info@easytech.services · WhatsApp +507 6688-4938

---

## 11. Marketing OS — Decision Engine (M10)

**Último commit plataforma:** `91a482d` (M10.1–M10.4) · **Estrategia:** [EMACCION_PLAN_MAESTRO_v3.md](EMACCION_PLAN_MAESTRO_v3.md)

| Sub-fase | Estado | Módulo / API |
|----------|--------|----------------|
| M10.1 Roadmap Builder | ✅ | `decision_engine_*` · regla `brand_publication_gap` |
| M10.2 Priority Engine | ✅ | `PriorityScorer` |
| M10.3 Recommendations | ✅ | schema v10 · `GET /api/v1/tenants/{id}/recommendations` |
| M10.4 Daily Planner | ✅ | schema v11 · `POST/GET .../roadmaps/{date}` |
| M10.5 Approval Queue | ✅ | approve / reject / snooze |
| AI Provider Manager | ✅ código · ⏳ CODITO prod | `ai_provider/` · `scripts/validate_codito_ai.py` |
| Marketing Context Engine | ✅ | `marketing_context_engine/` · `GET .../marketing-context` |
| Marketing Intelligence Layer | ✅ | `docs/MARKETING_INTELLIGENCE_LAYER.md` · scorer + composer + explain |
| Campaign Engine | ✅ | `docs/CAMPAIGN_ENGINE.md` · planner + builder + explain |
| Content Engine | ✅ | `docs/CONTENT_ENGINE.md` · planner + builder + explain · schema v15 |
| VS2 Primera campaña publicada | ✅ | `docs/VS2_PRIMERA_CAMPANA_PUBLICADA.md` · approve → queue → LinkedIn |
| M11 Marketing Brain | ✅ | IA enriquece con contexto + estructura composed |
| Opportunity Engine F1–F4 | ✅ | detect → promote → roadmap → enrich |
| M12 Business Intelligence | 📋 | ROI, CTA, horario, producto |
| M13 Automation Brain | 📋 | ejecutar post-aprobación |

**Prioridad inmediata (v3):** Bloque 2 IA — **proveer `CODITO_HOST`** y ejecutar `enable_ai_prod.sh` → Bloques 3–6.

---

## 12. AI Provider + Marketing Context Engine (2026-06-30)

### AI Provider Manager

Capa única de salida LLM: `Motor_Tecnico/accio_engine/ai_provider/`. Ningún módulo debe llamar OpenAI/Ollama/LiteLLM directamente.

| Variable | Uso |
|----------|-----|
| `ACCIO_AI_PROVIDER` | `litellm` \| `openai` \| `disabled` |
| `ACCIO_AI_ENABLED` | `true`/`false` (alias `AI_ASSISTANT_ENABLED`) |
| `ACCIO_AI_BASE_URL` | URL LiteLLM en CODITO (ej. `http://HOST:4000`) |
| `ACCIO_AI_MODEL` | Modelo (ej. `qwen2.5-coder:14b`) |
| `ACCIO_AI_API_KEY` | Opcional para LiteLLM |
| `ACCIO_AI_TIMEOUT` | Segundos (default 90) |
| `ACCIO_AI_OPENAI_FALLBACK` | Si LiteLLM falla y hay `OPENAI_API_KEY` |
| `OPENAI_API_KEY` | Fallback opcional (no UI tenant) |

**Estado endpoint:** `GET /accio/{tenant}/assistant/status` — devuelve `llm_available`, `provider`, `unavailable_reason`, `active_provider`.

### Validación CODITO (2026-06-30)

Comando ejecutado en ARROZCONPOLLO:

```bash
./venv/bin/python scripts/validate_codito_ai.py
```

| Campo | Valor observado |
|-------|-----------------|
| `ACCIO_AI_PROVIDER` | `litellm` |
| `ACCIO_AI_BASE_URL` | **(vacío)** |
| `ACCIO_AI_MODEL` | `gpt-4o-mini` |
| API key | no configurada |
| Resultado | **FAIL** — exit code 1 |

**Diagnóstico:** el código del Provider Manager está desplegado, pero el VPS no tiene URL de CODITO en `.env`. Sin `ACCIO_AI_BASE_URL`, el pipeline responde `llm_skipped=true` con causa `ACCIO_AI_BASE_URL not configured` — no rompe el flujo.

**Siguiente acción requerida (ops):**

1. Definir en `/opt/easytech_marketing/.env`:
   ```bash
   ACCIO_AI_BASE_URL=http://<CODITO_HOST>:4000
   ACCIO_AI_MODEL=qwen2.5-coder:14b
   ACCIO_AI_ENABLED=true
   ```
2. Re-ejecutar `scripts/validate_codito_ai.py` (debe exit 0).
3. `sudo systemctl restart easytech-accio-engine`
4. En `/accio/plan/easytech/` → **Pipeline completo** → verificar `llm_enriched > 0`.

**Alternativa fallback:** `OPENAI_API_KEY=sk-…` + `ACCIO_AI_OPENAI_FALLBACK=true` (solo si CODITO no disponible).

### Marketing Context Engine

Fuente única de contexto estructurado por tenant:

- Módulo: `marketing_context_engine/builder.py` → `MarketingContextBuilder`
- API: `GET /api/v1/tenants/{tenant}/marketing-context?purpose=llm|full`
- Consumidores: M11 Marketing Brain (enrich), futuros Campaign/Content/Automation

Incluye: company brain, brands, productos, knowledge matrix, oportunidades, recomendaciones pendientes, roadmap del día, editorial **3 valor + 1 venta**, CTA **DIAGNÓSTICO**, guía `https://n8n.etsrv.site/guia/`.

### Pipeline operativo

`POST /api/v1/tenants/{tenant}/opportunities/run-pipeline`

Respuesta incluye: `detected`, `promoted`, `roadmap_generated`, `llm_enriched`, `llm_skipped`, `llm_skip_reason`, `errors`.

### Campaign Engine (2026-06-30)

Documento: `docs/CAMPAIGN_ENGINE.md`

- **CampaignPlanner** + **CampaignBuilder** — recomendación aprobada → campaña estructurada
- **Campaign Explain** — trazabilidad completa
- API: `/api/v1/tenants/{id}/campaigns/*`
- Consola: sección **Campañas** en `/accio/plan/`
- Schema v14: `campaign_channels`, `campaign_kpis`, `campaign_history`

### Marketing Intelligence Layer (2026-06-30)

Documento: `docs/MARKETING_INTELLIGENCE_LAYER.md`

- **OpportunityScorer** — score 0–100 en cada oportunidad
- **RecommendationComposer** — estructura ejecutiva antes de IA
- **Explainability** — `explain` técnico en cada recomendación promovida
- API v2: `/explain`, `/recompose`, `/similar`, `/rescore`
- Consola: panel **¿Por qué recomendamos esto?**
