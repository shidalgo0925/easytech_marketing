# Fase M — Multi-Tenant Core

**Versión:** 1.0 · **Fecha:** 2026-06-19  
**Estado:** Diseño aprobado — **no implementar runtime sin GO explícito**  
**Prioridad:** **Crítica** — bloquea escalar conectores, campañas y clientes adicionales

---

## 1. Decisión estratégica

EMAcción **ya no es solo para EasyTech**. Evoluciona a **plataforma multi-tenant** para:

| Tenant | ID | Notas |
|--------|-----|-------|
| EasyTech | `easytech` | Tenant inicial (datos actuales migran aquí) |
| Relatic | `relatic` | Segundo tenant |
| Futuros clientes | `future_client` | Mismo motor, datos aislados |

**Regla:** No crear otro EMAcción para Relatic. **Un solo motor multi-tenant.**

```
emaccion.etsrv.site
        │
        ├── /accio/dashboard/easytech
        ├── /accio/dashboard/relatic
        └── /accio/dashboard/{tenant_id}
```

Internamente: `tenant_id` en toda petición API, archivo y job.

---

## 2. Principio de aislamiento

**Nada de datos mezclados** entre EasyTech y Relatic (ni entre ningún par de tenants).

Cada tenant tiene separado:

| Dominio | Ubicación objetivo |
|---------|-------------------|
| Contexto de negocio | `tenants/{id}/business_context.json` |
| Knowledge base | `tenants/{id}/knowledge/` |
| Reglas editoriales | `tenants/{id}/editorial_rules.json` |
| Campañas | `tenants/{id}/campaigns.json` |
| Calendario | `tenants/{id}/calendar.json` |
| Cola de publicaciones | `tenants/{id}/content_queue.json` |
| Conectores (metadatos) | `tenants/{id}/connectors.json` |
| OAuth / tokens | almacén seguro por tenant (Fase N) |
| Órdenes / estado runtime | `tenants/{id}/orders.json`, `state.json` |
| Métricas | `tenants/{id}/metrics/` o DB |
| Leads | routing por tenant |
| CRM destino | config por tenant (Odoo / EN1) |

---

## 3. Modelo de datos `tenant`

```json
{
  "tenant_id": "easytech",
  "display_name": "Easy Technology Services",
  "slug": "easytech",
  "status": "active",
  "created_at": "2026-06-19T00:00:00Z",
  "domains": ["easytech.services"],
  "default_locale": "es-PA",
  "crm_target": "odoo",
  "features": ["knowledge", "publisher", "flyers"]
}
```

Registro maestro: `Marketing/tenants/registry.json` (sin secretos).

---

## 4. Estructura de carpetas objetivo

```
Marketing/
├── tenants/
│   ├── registry.json
│   ├── easytech/
│   │   ├── business_context.json
│   │   ├── editorial_rules.json
│   │   ├── content_queue.json
│   │   ├── campaigns.json
│   │   ├── calendar.json
│   │   ├── connectors.json
│   │   ├── knowledge/
│   │   └── metrics/
│   └── relatic/
│       └── … (misma estructura)
```

Migración: mover contenido actual de `Marketing/accio/` y `Marketing/knowledge/` → `tenants/easytech/`.

---

## 5. API con `tenant_id`

Todas las rutas existentes ganan contexto de tenant:

| Patrón actual | Patrón multi-tenant |
|---------------|---------------------|
| `GET /accio/dashboard/api/summary` | `GET /accio/{tenant_id}/dashboard/api/summary` |
| `POST /accio/run/pipeline` | `POST /accio/{tenant_id}/run/pipeline` |
| `GET /accio/content/queue` | `GET /accio/{tenant_id}/content/queue` |

**Compatibilidad transitoria:** `/accio/...` sin tenant → default `easytech` (deprecar en release siguiente).

Middleware `resolve_tenant(tenant_id)`:

1. Valida que el tenant existe y está `active`
2. Carga paths del tenant
3. Rechaza cross-tenant (401/404)

Auth: `ACCIO_API_KEY` global de plataforma **o** API key por tenant (Fase N).

---

## 6. Dashboard filtrado por tenant

- URL: `https://emaccion.etsrv.site/accio/dashboard/{tenant_id}`
- Selector de tenant en header (solo si el operador tiene acceso a >1)
- Tabs cargan datos solo del tenant activo
- Branding opcional por tenant (logo, colores)

---

## 7. Conectores, knowledge y campañas por tenant

| Módulo | Cambio |
|--------|--------|
| `knowledge_api.py` | Recibe `tenant_id`, lee `tenants/{id}/knowledge/` |
| `executor.py` | Órdenes scoped a tenant |
| `dashboard_data.py` | Summary/metrics por tenant |
| Publishers | Tokens desde almacén seguro del tenant |
| Cron / pipeline | Itera tenants activos o recibe `tenant_id` |

**Regla:** No publicar con credenciales de otro tenant. Validar `tenant_id` en cada job.

---

## 8. CRM destino por tenant

| Tenant | CRM objetivo (ejemplo) |
|--------|------------------------|
| `easytech` | Odoo → migrar a EN1 |
| `relatic` | EN1 u Odoo propio |

Config en Fase N: `GET/POST /accio/{tenant_id}/settings/crm`

---

## 9. Tareas Fase M

| ID | Tarea | Estado |
|----|-------|--------|
| M1 | Modelo `tenant` + `registry.json` | ❌ |
| M2 | Estructura `Marketing/tenants/{id}/` | ❌ |
| M3 | Migración datos EasyTech → `tenants/easytech/` | ❌ |
| M4 | Middleware `resolve_tenant` en `app.py` | ❌ |
| M5 | API con prefijo `/{tenant_id}/` | ❌ |
| M6 | Dashboard por tenant (`/dashboard/{tenant_id}`) | ❌ |
| M7 | `knowledge_api`, `queue_store`, `executor` multi-tenant | ❌ |
| M8 | Pipeline/cron por tenant | ❌ |
| M9 | Tests de aislamiento (no leakage) | ❌ |
| M10 | Documentar migración Relatic onboarding | ❌ |

**Criterio de cierre:** EasyTech y Relatic operan en el mismo motor con datos 100% separados; dashboard y API filtran por `tenant_id`.

---

## 10. Orden respecto a otras fases

**Fase M debe completarse antes de:**

- Escalar conectores a más canales (Fase H)
- Onboarding de Relatic en producción
- Fase N (settings depende del modelo tenant)
- Opportunity / Campaign Engine multi-cliente

Secuencia acordada:

```
Fase A (base) → Fase M (multi-tenant) → Fase N (settings) → Fase E/F/G…
```

---

## 11. Referencias

- [ROADMAP.md](ROADMAP.md)
- [EMACCION_PHASE_N_TENANT_SETTINGS.md](EMACCION_PHASE_N_TENANT_SETTINGS.md)
- [EMACCION_ARCHITECTURE.md](EMACCION_ARCHITECTURE.md)
- [CONTEXTO.md](CONTEXTO.md)
