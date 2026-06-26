# EM+Acción — Contexto operativo (snapshot)

**Fecha:** 2026-06-26  
**Repo:** `/opt/easytech_marketing` · **Servicio:** `easytech-accio-engine` (:8092)  
**Dashboard PROD:** https://emaccion.etsrv.site/accio/dashboard/easytech/

Documento de continuidad para operadores y agentes. Complementa `docs/CONTEXTO.md` y `docs/EMACCION_V2_ESTADO.md`.

---

## 1. Modelo de producto (acordado)

**EMAcción = SaaS multi-tenant.** Documento canónico: `docs/EMACCION_TENANT_VS_APP.md`.

| Nivel | Qué es | Ejemplos | Interno |
|-------|--------|----------|---------|
| **Tenant** | Empresa que usa EMAcción | ETS, Modecosa, IIUS, Relatic (cliente) | `tenant_id` |
| **App** | Línea/marca/producto a promocionar | EN1, EPayRoll, Diplomados | `app_id` |

| Concepto UI | Concepto interno |
|-------------|------------------|
| Empresa (selector login) | **Tenant** — `tenant_id` + `Marketing/tenants/{id}/` |
| App / línea (fase 1 API) | **App** — `Marketing/tenants/{id}/apps/` |
| Administrador de empresa | `tenant_admin` |
| Super administrador | `super_admin` |

Cada **tenant** tiene aislado: usuarios, conectores, CRM, configuración.  
Cada **app** tiene (objetivo): cola, campañas, flyers, knowledge — hoy la app `default` usa la cola del tenant (compat).

**Reglas:** Nunca crear un tenant para representar una App. Todo contenido lleva `tenant_id` + `app_id`.

**EN1** (`/admin/organizations`): producto SaaS aparte; no duplicar su CRUD. Sync futuro `organization_id` ↔ `tenant_id`.

---

## 2. Flujo de acceso

```
GET /accio/login/          → Login plataforma (email + contraseña)
        │
        ├─ 1 empresa  → /accio/dashboard/{id}/
        └─ N empresas → /accio/empresas/  → elegir → POST /accio/auth/empresas/{id}/entrar
```

| Ruta | Uso |
|------|-----|
| `/accio/login/` | Login sin empresa en URL |
| `/accio/empresas/` | Selector de empresa |
| `/accio/dashboard/` | Redirige a empresa en sesión o easytech si tiene acceso |
| `/accio/dashboard/{tenant_id}/` | Dashboard operativo |
| `/accio/login/{tenant_id}/` | Login legacy por empresa (compat) |

**Auth:** SQLite `Marketing/tenants/.secrets/auth.db`  
Tablas: `users`, `user_tenants` (rol por empresa).

**Usuario de prueba:** `shidalgo@easytech.services` · rol `tenant_admin` · solo empresa `easytech`.

---

## 3. Dashboard — pestañas

| Pestaña | Contenido |
|---------|-----------|
| Resumen | KPIs, cola posts, leads Odoo, órdenes |
| Campañas | `campaigns.json` |
| Calendario | `calendar.json` |
| Métricas | Odoo + LinkedIn |
| Flyers | Biblioteca assets |
| Conocimiento | Contexto IA + KB + generador temas |
| Conectores | Estado multicanal |
| Configuración | Centro de configuración (13 sub-secciones) |

Header: **Empresa:** selector + nombre comercial. Banner en Resumen: “Empresa activa”.

---

## 4. Configuration Center — CRUD (2026-06-26)

Sub-nav en **Configuración**:

| Sección | CRUD | Backend |
|---------|------|---------|
| Información general | Empresa + branding + contexto IA | `tenant_provisioning`, `knowledge_api` |
| Usuarios | + fila, editar, eliminar, Guardar → **auth.db** | `settings_center.save_users` → `auth_service.sync_tenant_users` |
| Roles | + rol, permisos csv | `users.json` (definición roles) |
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

**Empresas (solo `super_admin`):** listar, crear, editar, suspender, **reactivar** (`POST .../empresas/{id}/enable`).

**Knowledge (pestaña Conocimiento):** CRUD artículos Markdown (`POST/DELETE /accio/{tenant}/knowledge`).

### Roles canónicos

| ID | Permisos |
|----|----------|
| `tenant_admin` | read, publish, config, admin |
| `marketing_operator` | read, publish |
| `viewer` | read |

Alias legacy: `admin` → `tenant_admin`, `operator` → `marketing_operator`.

---

## 5. Datos por empresa (easytech)

| Recurso | Ubicación | Estado jun 2026 |
|---------|-----------|-----------------|
| Cola posts | `Marketing/tenants/easytech/content_queue.json` | ~22 posts, 8 LI pendientes |
| Registry | `Marketing/tenants/registry.json` | easytech + relatic |
| Contexto IA | `tenants/easytech/business_context.json` | Easy Technology Services |
| Auth | `Marketing/tenants/.secrets/auth.db` | shidalgo, admin → easytech |
| Relatic | `tenants/relatic/` | Vacío (aislado, sin cola) |

---

## 6. Archivos clave en código

| Archivo | Rol |
|---------|-----|
| `Motor_Tecnico/accio_engine/app.py` | Rutas HTTP, sesión, dashboard |
| `Motor_Tecnico/accio_engine/auth_service.py` | Login, RBAC, sync usuarios |
| `Motor_Tecnico/accio_engine/tenant_provisioning.py` | CRUD empresas |
| `Motor_Tecnico/accio_engine/settings_center.py` | Vista configuración |
| `Motor_Tecnico/accio_engine/static/dashboard.html` | UI principal |
| `Motor_Tecnico/accio_engine/static/empresas.html` | Selector empresa |
| `Motor_Tecnico/accio_engine/static/login.html` | Login plataforma |
| `Motor_Tecnico/accio_engine/knowledge_api.py` | KB + artículos |

**Tests:** `venv/bin/python3 -m unittest tests/test_*.py -v` (25 tests, jun 2026)

**Reiniciar:** `sudo systemctl restart easytech-accio-engine`

---

## 7. Incidentes resueltos (sesión 2026-06-26)

| Problema | Causa | Fix |
|---------|-------|-----|
| Dashboard vacío (sin KPIs/cola) | `switchTenant` declarado dos veces en `dashboard.html` → SyntaxError, JS no ejecutaba | Eliminar declaración duplicada |
| Sesión sin empresa activa | Login plataforma sin `_enter_empresa_session` | Fijar empresa al abrir dashboard + redirects |
| Usuarios UI no afectaban login | Guardado solo en `users.json`, login usa `auth.db` | `sync_tenant_users` en guardar |
| Confusión pestaña Empresa vs datos | Pestaña operativa renombrada a **Configuración** | Header mantiene selector Empresa |

---

## 8. Pendiente (no implementado)

| Ítem | Prioridad |
|------|-----------|
| Wizard onboarding 7 pasos (crear empresa) | Alta |
| Cron/publicadores recorriendo **todas** las empresas activas | Alta |
| `en1_sync` — lead → EN1 CRM | Media |
| Menú Oportunidades / Leads (spec §14) | Media |
| Opportunity Engine (Fase E plan V2) | Roadmap |
| Deprecar `dashboard_client.json` / API key en HTML | Seguridad |
| Instagram `META_IG_USER_ID` | Conectores |

---

## 9. Reglas para agentes

1. **No commitear** sin pedido explícito del usuario.
2. **No mezclar datos** entre empresas.
3. Tras cambios en `app.py` / estáticos → reiniciar `easytech-accio-engine`.
4. UI: decir **Empresa**, no tenant.
5. Probar con sesión real: datos easytech en Resumen, no solo HTML 200.
6. Documentación maestra: `docs/CONTEXTO.md` · estado fases: `docs/EMACCION_V2_ESTADO.md`.

---

## 10. URLs

| Recurso | URL |
|---------|-----|
| Dashboard easytech | https://emaccion.etsrv.site/accio/dashboard/easytech/ |
| Login | https://emaccion.etsrv.site/accio/login/ |
| Health | https://emaccion.etsrv.site/accio/health |
| Proxy alternativo | https://n8n.etsrv.site/accio/ (mismo motor) |
| Odoo CRM | https://easydb.etsrv.site |
| Guía leads | https://n8n.etsrv.site/guia/ |
