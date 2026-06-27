# EM+Acción — Contexto operativo (snapshot)

**Fecha:** 2026-06-27  
**Repo:** `/opt/easytech_marketing` · **Servicio:** `easytech-accio-engine` (:8092)  
**Commit ref:** `7495180` · **Bitácora:** `docs/sessions/2026-06-27.md`

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
        ├─ 1 empresa  → /accio/dashboard/{id}/
        └─ N empresas → /accio/empresas/  → elegir → POST /accio/auth/empresas/{id}/entrar
```

| Ruta | Uso |
|------|-----|
| `/accio/producto/` | **Landing producto EM+Acción** (pública) |
| `/accio/login/` | Login sin empresa en URL |
| `/accio/empresas/` | Selector de empresa |
| `/accio/dashboard/` | Redirige a empresa en sesión o easytech si tiene acceso |
| `/accio/dashboard/{tenant_id}/` | Dashboard operativo |
| `/accio/{tenant_id}/legal/` | Documentos legales por tenant |
| `/accio/login/{tenant_id}/` | Login legacy por empresa (compat) |

**Auth:** SQLite `Marketing/tenants/.secrets/auth.db`  
Tablas: `users`, `user_tenants` (rol por empresa).

**Usuario operador:** `shidalgo@easytech.services` · rol global `super_admin` · acceso a todos los tenants.

---

## 3. Landing de producto (2026-06-27)

Página SaaS de conversión — **no** es landing por tenant.

| Campo | Valor |
|-------|-------|
| **URL** | https://emaccion.etsrv.site/accio/producto/ |
| **Archivos** | `Motor_Tecnico/accio_engine/static/emaccion/` |
| **Leads** | `POST /accio/producto/lead` → Odoo (`emaccion_producto`) |
| **CTA prueba** | `/accio/login/` |
| **WhatsApp** | +507 6688-4938 |

Secciones: hero, funcionalidades, integraciones (activas vs Próximamente), casos de uso, galería, planes, FAQ, contacto.

**Nota:** `emaccion.etsrv.site/` (raíz) aún redirige al dashboard — cambio nginx pendiente si se aprueba.

---

## 4. Dashboard — pestañas

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

Header: selector **Empresa** + nombre comercial. Barra de progreso al arrancar (~5 s).

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
| `Motor_Tecnico/accio_engine/app.py` | Rutas HTTP, landing, legal, leads |
| `Motor_Tecnico/accio_engine/auth_service.py` | Login, RBAC, protección super_admin |
| `Motor_Tecnico/accio_engine/static/emaccion/` | Landing producto |
| `Motor_Tecnico/accio_engine/static/dashboard.html` | UI principal |
| `Motor_Tecnico/accio_engine/static/accio-design.css` | Design system |
| `Marketing/tenants/registry.json` | Registry tenants |

**Reiniciar tras cambios:** `sudo systemctl restart easytech-accio-engine`

---

## 8. Pendiente

| Ítem | Prioridad |
|------|-----------|
| Flyer #10 IIUS (PNG dueño) | Alta |
| Home nginx → `/accio/producto/` | Media (requiere GO) |
| Capturas reales dashboard en landing | Media |
| Legal Relatic — revisión abogado | Media |
| Instagram / Google Business conectores | Media |
| Cron/publicadores multi-tenant | Alta |
| Wizard onboarding 7 pasos | Alta |

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
| Dashboard relatic | https://emaccion.etsrv.site/accio/dashboard/relatic/ |
| Login | https://emaccion.etsrv.site/accio/login/ |
| Legal Relatic | https://emaccion.etsrv.site/accio/relatic/legal/ |
| Health | https://emaccion.etsrv.site/accio/health |
| Odoo CRM | https://easydb.etsrv.site |
| Guía leads (legacy) | https://n8n.etsrv.site/guia/ |
| OAuth / n8n proxy | https://n8n.etsrv.site/accio/ |

**Contacto:** info@easytech.services · WhatsApp +507 6688-4938
