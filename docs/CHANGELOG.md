# Changelog — EasyMarketingOne / ARROZCONPOLLO

Formato basado en fechas. Solo cambios operativos relevantes en el VPS o repo.

---

## 2026-06-26 — Estabilización inicial ARROZCONPOLLO

### Añadido
- `docs/PROJECT_STATE.md` — fuente única de verdad del servidor y reglas de operación
- `scripts/doctor.sh` — diagnóstico automatizado (host, servicios, git, docker)
- `docs/CHANGELOG.md` — este archivo
- `docs/NEXT_STEPS.md` — plan operativo pendiente

### Corregido
- `scripts/accio_tick.sh` — ruta `POST /accio/easytech/tick` (antes `/accio/tick` → 404)
- `scripts/accio_cli.sh` — rutas tenant-scoped para `orders` y `tick`
- `Motor_Tecnico/accio_engine/app.py` — API key Bearer recupera permisos de automatización (cron/Accio Work); antes RBAC devolvía 403 en `tick`

### Actualizado
- `docs/INVENTARIO_DESPLIEGUE.md` — refleja motor Accio activo, servicios OAuth, endpoints multi-tenant

### Verificado
- `easytech-accio-engine` running en :8092
- Endpoints: `/accio/health`, `/accio/status`, `/accio/easytech/tasks`, `/accio/files/tree` → 200
- OAuth services LinkedIn/Meta/Google → 200
- `accio_tick.sh` → `{"ok": true, "message": "Sin ordenes pendientes"}`

---

## 2026-06-26 — GO #2 (push + n8n + legacy tick)

### Añadido
- Ruta legacy `POST /accio/tick` → delega a `/accio/easytech/tick`

### Corregido
- `docs/n8n-workflow-*.json` — IDs de workflow y nodos para import CLI n8n

### Desplegado
- Push commit `5661107` → `origin/main`
- Workflows n8n importados (inactivos): LinkedIn automático, pipeline semanal

---

## 2026-06-27 — Tenant vs App (Fase 1)

### Añadido
- `docs/EMACCION_TENANT_VS_APP.md` — arquitectura SaaS tenant + app
- `Motor_Tecnico/accio_engine/marketing_app.py` — modelo App
- `Marketing/tenants/easytech/apps/registry.json` (9 apps)
- `Marketing/tenants/relatic/apps/registry.json` (default)
- API `GET/POST /accio/{tenant}/apps`
- Tests `tests/test_marketing_app.py`

### Corregido
- Vocabulario: `tenant_provisioning` documentado como CRUD de **tenants**, no apps
- Posts en cola easytech: campo `app_id: default` (22 posts)

### Pendiente (post Fase 3)
- UI mapping EN1 en dashboard
- Leads EN1 (write)

---

## 2026-06-27 — Tenant vs App (Fase 3)

### Añadido
- `en1_organizations.py` — sync read-only EN1 `saas_organization` ↔ `tenant_id`
- API `GET /accio/en1/organizations`, `GET /accio/en1/sync`, `POST /accio/{tenant}/settings/en1-mapping`
- Referencia EN1 Dev (4 orgs) + cache local tras fetch live
- Tests `tests/test_en1_organizations.py`
- Campo `en1_organization_id` en registry tenant

### Actualizado
- `test_crm` EN1 — valida lectura de organizaciones si hay credenciales
- `.gitignore` — cache EN1 local

---

## 2026-06-27 — Tenant vs App (Fase 2)

### Añadido
- Selector **App** en dashboard (`Tenant` + `App` en header)
- Filtrado por `app_id` en API dashboard, cola de contenido, executor y publishers
- `meta_publisher.py` — soporte `--app-id=`
- Header `X-Accio-App` y query `?app_id=` en rutas dashboard

### Corregido
- `load_flyers_library()` — parámetro `app_id` (500 en `/summary`)

### Verificado
- Tests `test_marketing_app` + `test_tenant_provisioning` → OK
- `GET /accio/easytech/dashboard/api/summary?app_id=default` → 200 con `app_name`

---

### Bitácora de sesiones (2026-06-26)

- Carpeta `docs/sessions/` — ver `docs/sessions/2026-06-26.md`

---

## Histórico (commits recientes en Git)

| Fecha | Commit | Resumen |
|-------|--------|---------|
| 2026-06-26 | `b7e34a9` | Multi-empresa, auth, CRUD configuración |
| 2026-06-26 | `a5bb44d` | Phase E Knowledge Engine integrado |
| 2026-06-26 | `ad9bb91` | Documentación EMAcción como motor comercial IA |
| 2026-06-26 | `6732a05` | Roadmap Phase E |
| 2026-06-26 | `3fba19a` | Contexto proyecto + README |
