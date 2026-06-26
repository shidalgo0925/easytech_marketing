# EM+Acción — Diagnóstico de arquitectura (Entregable 1)

**Fecha:** 2026-06-26  
**Alcance:** Autenticación, credenciales, multi-tenant, publishers, código muerto/duplicado, seguridad.  
**Estado:** Diagnóstico únicamente — **sin implementación runtime** (pendiente GO explícito).

---

## Resumen ejecutivo

El sistema tiene **bases parciales** de lo que pide la especificación (login por usuario, secretos cifrados por tenant en SQLite, UI de Configuración, RBAC básico), pero **no cumple** los criterios de aceptación de un SaaS multi-tenant comercial:

| Área | Estado | Riesgo |
|------|--------|--------|
| Login usuario | Parcial | Sin `user_tenants`, sin roles de la spec |
| API key en dashboard | Mejorado | Sesión por cookie; API key solo técnica |
| Credenciales en publicación | **Crítico** | Publishers leen `.env` global, no tenant |
| Aislamiento tenant en publish | **Crítico** | Cola legacy global en scripts |
| Configuración centralizada | Parcial | Lógica repartida en 4+ módulos |
| Auditoría | Parcial | Log de settings; sin tabla `audit_log` |
| Arquitectura publishers | **Deuda** | Sin `PublisherBase`, sin `tenant_id` en subprocess |
| Código muerto / legacy | Alto | ~12 rutas legacy + fallback `Marketing/accio/` |

**Conclusión:** No avanzar funcionalidades nuevas hasta cerrar migración de credenciales → tenant + auth real + publishers tenant-aware.

---

## 1. Estado actual de autenticación

### Lo que existe hoy

| Componente | Ubicación | Notas |
|------------|-----------|-------|
| Login usuario (email/usuario + password) | `POST /accio/auth/login`, `static/login.html` | Flask session cookie |
| Login API key (técnico) | Mismo endpoint, body `api_key` | Rol `admin` forzado |
| Sesión | `session[accio_auth, tenant_id, role, user_id]` | Sin tabla `sessions` |
| Usuarios | `Marketing/tenants/{id}/users.json` | `password_hash` werkzeug/scrypt |
| Roles | JSON por tenant: `admin`, `operator`, `viewer` | **No** coinciden con spec §4 |
| RBAC API | `rbac.py` + `require_api_key` | Permisos: `read`, `publish`, `config`, `admin` |
| Protección dashboard HTML | Redirect a `/accio/login/{tenant}/` sin sesión | OK |
| Protección API JSON | `require_api_key` acepta sesión **o** Bearer/`X-Accio-Key` | OK para sesión |

### Lo que NO existe (spec §4)

```text
users (tabla BD)          → solo users.json por tenant
roles (tabla BD)          → solo JSON embebido
user_tenants              → NO EXISTE
sessions (tabla BD)       → solo Flask cookie
super_admin               → NO EXISTE
tenant_admin              → aproximado por role "admin" por tenant
marketing_operator        → aproximado por "operator"
```

### Brechas críticas de auth

1. **Sin `user_tenants`:** cualquier usuario logueado puede abrir `/accio/dashboard/relatic/` si conoce la URL. El selector de tenant lista todos los tenants del registry sin filtrar por permiso.
2. **Usuarios duplicados por tenant:** no hay identidad global; `admin@easytech.services` y `admin@relatic.local` son registros distintos.
3. **API key sigue siendo bypass total:** quien tenga `ACCIO_API_KEY` global o la del tenant obtiene rol `admin` sin auditoría de usuario real.
4. **`marketing_operator` no puede publicar sin ver secretos en UI** — no implementado (operator tiene permiso `config` hoy).

---

## 2. Dónde se pide actualmente API key

### Dashboard (UI)

| Momento | ¿Pide API key? | Estado |
|---------|----------------|--------|
| Pantalla login | No (usuario + contraseña) | OK |
| Publicar siguiente | No en UI | Usa sesión cookie |
| Ejecutar pipeline | No en UI | Usa sesión cookie |
| Guardar configuración | No en UI | Usa sesión cookie |
| Config → Clave integración | Campo opcional `accio_api_key` | Solo admin; no es login |

**Nota:** `authHeaders()` en `dashboard.html` ya **no** envía `Authorization: Bearer`. Solo cookie + `X-Accio-Tenant`.

### Scripts / cron / CLI

| Archivo | Uso API key |
|---------|-------------|
| `scripts/accio_tick.sh` | `Authorization: Bearer ${ACCIO_API_KEY}` → `POST /accio/tick` |
| `scripts/accio_cli.sh` | Todas las llamadas con Bearer global |
| Documentación / skills | Referencias a pegar API key en chat |

### API (fallback cuando no hay sesión)

Cualquier endpoint con `@require_api_key` acepta:
- Sesión Flask válida para el `tenant_id`, **o**
- `Authorization: Bearer <ACCIO_API_KEY>` global, **o**
- `X-Accio-Key` header, **o**
- `accio_api_key` guardada en `tenant_secrets.db` (namespace `platform`)

### Publicación (problema real)

Los publishers **no piden API key al usuario**, pero **fallan o usan `.env`** si no hay variables globales:

```text
linkedin_publisher.py  → require_env("LINKEDIN_ACCESS_TOKEN") desde .env
meta_publisher.py      → require_env("META_PAGE_ACCESS_TOKEN") desde .env
odoo_sync.py           → ODOO_* desde .env
```

Esto produce el síntoma percibido: *"al publicar algo falla / pide configuración"* aunque el dashboard no muestre un campo de API key.

---

## 3. Endpoints que usan `ACCIO_API_KEY` / `@require_api_key`

**Total aproximado:** 76 rutas decoradas con `@require_api_key` en `app.py`.

### Categorías

| Categoría | Ejemplos | Auth aceptada |
|-----------|----------|---------------|
| Dashboard API | `/accio/{tenant}/dashboard/api/*` | Sesión o API key |
| Settings | `/accio/{tenant}/settings/*` | Sesión o API key + RBAC |
| Publish | `/accio/{tenant}/run/publish-linkedin`, `publish-meta`, `pipeline`, `tick` | Sesión o API key |
| Content | `/accio/{tenant}/content/queue`, `generate-topic` | Sesión o API key |
| Legacy (sin tenant en URL) | `/accio/status`, `/accio/run/pipeline`, … | API key → tenant `easytech` |

### Rutas legacy a deprecar (§16)

```text
GET  /accio/dashboard/api/summary
GET  /accio/dashboard/api/knowledge
GET  /accio/status
GET  /accio/content/queue
POST /accio/run/pipeline
POST /accio/run/publish-linkedin
POST /accio/run/publish-meta
GET/POST /accio/config/business-context
POST /accio/content/generate-topic
```

Implementadas con decorador `_legacy_tenant` → siempre `easytech`.

### Rutas públicas (sin auth)

```text
GET /accio/health
GET /accio/static/*
GET /accio/login/*
POST /accio/auth/login
GET /accio/auth/status
POST /accio/auth/logout
GET /accio/privacidad
```

---

## 4. Rutas del dashboard sin login real

| Ruta | Protección actual | ¿Cumple spec? |
|------|-------------------|---------------|
| `/accio/dashboard/{tenant}/` | Redirect login si no hay sesión | Parcial |
| `/accio/login/{tenant}/` | Pública | OK |
| API bajo `/accio/{tenant}/...` | Sesión o API key | Parcial |
| Assets estáticos | Públicos | OK |

**Brecha:** usuario autenticado en `easytech` puede acceder API de `relatic` si cambia `tenant_id` en URL (no hay check `user_tenants`).

---

## 5. Credenciales en `.env` (global)

Según `.env.example` (nombres, no valores):

```text
# CRM
ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD

# LinkedIn
LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN

# Meta
META_APP_ID, META_APP_SECRET, META_PAGE_ID, META_PAGE_ACCESS_TOKEN, META_IG_USER_ID, …

# Google / TikTok
GOOGLE_*, TIKTOK_*, YOUTUBE_*

# Plataforma
ACCIO_API_KEY, ACCIO_ADMIN_PASSWORD, ACCIO_SECRETS_KEY, ACCIO_ENGINE_PORT
PUBLIC_SITE_URL
```

**Uso activo en runtime (incorrecto para multi-tenant):**

| Variable | Consumidor |
|----------|------------|
| `LINKEDIN_*` | `linkedin_publisher.py` (directo `os.getenv`) |
| `META_*` | `meta_publisher.py`, `meta_oauth.py` |
| `ODOO_*` | `odoo_sync.py`, `dashboard_data.py` (fallback) |
| `GOOGLE_*` | `google_oauth.py`, `google_business.py`, `google_auth.py` |
| `TIKTOK_*` | `tiktok_oauth.py` |
| `ACCIO_API_KEY` | `app.py`, `accio_tick.sh`, cifrado Fernet fallback |

---

## 6. Credenciales en JSON / SQLite

### SQLite cifrado (correcto en diseño)

**Archivo:** `Marketing/tenants/.secrets/tenant_secrets.db` (gitignored)

**Tabla actual:** `tenant_secrets (tenant_id, namespace, key, value_encrypted, validation_status, …)`

Equivalente parcial a `tenant_connector_credentials` de la spec.

**Namespaces:** `connectors`, `crm`, `platform`, `variables`

### JSON por tenant (no secretos, OK en git si no hay tokens)

```text
Marketing/tenants/{id}/
  tenant.json, business_context.json, editorial_rules.json
  products.json, publication.json, landings.json, ai.json
  users.json          ← contiene password_hash (NO debe ir a git)
  content_queue.json, campaigns.json, calendar.json, …
```

### JSON legacy (easytech fallback)

```text
Marketing/accio/          ← orders, campaigns, calendar, connectors, …
Marketing/content_queue.json
Marketing/knowledge/
```

`tenant.py` → `effective_paths()` redirige easytech a legacy si faltan archivos en `tenants/easytech/`.

---

## 7. Credenciales que podrían estar en Git

| Archivo | En git hoy | Riesgo |
|---------|------------|--------|
| `.env` | Ignorado | OK en repo |
| `deploy/secrets/` | Ignorado | OK |
| `Marketing/tenants/.secrets/` | Ignorado | OK |
| `Marketing/tenants/*/users.json` | **No trackeado** (carpeta tenants fuera de git) | OK por ahora |
| `Marketing/accio/orders.json` | Ignorado | OK |
| `dashboard_client.json` | Ignorado | OK |
| `.env.example` | Trackeado | OK (solo plantilla) |

### `.gitignore` — faltan entradas de la spec §23

No están explícitamente:

```text
*.env
tokens.json
secrets.json
credentials.json
Marketing/tenants/*/secrets.json
Marketing/tenants/*/tokens.json
```

---

## 8. Código muerto detectado

| Ítem | Ubicación | Evidencia | Recomendación |
|------|-----------|-----------|---------------|
| Rutas legacy `/accio/...` sin tenant | `app.py` L971+ | 12 endpoints duplicados | Deprecar → 410/redirect |
| `dashboard_assets_legacy` | `app.py` | Assets bajo `/accio/dashboard/` | Mantener solo `/accio/static/` |
| Fallback `Marketing/accio/` | `tenant.py` `effective_paths` | Solo easytech | Migrar datos y eliminar |
| `dashboard_client.json` | docs referencian; archivo ausente | Parche ya removido | Cerrar docs |
| Publishers stub | `stub_runner.py`, `tiktok.py`, `youtube.py`, … | `implementation: stub` | Mantener hasta Fase H |
| Login overlay en dashboard | Eliminado de HTML | — | OK |
| `toggleTechLogin` / API key UI | Eliminado | — | OK |

### Comandos sugeridos para profundizar (no ejecutados en este entregable)

```bash
vulture Motor_Tecnico/ --min-confidence 80
grep -R "def " Motor_Tecnico/accio_engine | wc -l
```

---

## 9. Código duplicado detectado

### Publishers (§17)

| Archivo | Qué hace | Fuente oficial propuesta | Acción |
|---------|----------|--------------------------|--------|
| `linkedin_publisher.py` | LI publish desde cola global + `.env` | `publishers/linkedin.py` (nuevo) | **Migrar** |
| `meta_publisher.py` | FB/IG publish + `.env` | `publishers/meta.py` (nuevo) | **Migrar** |
| `channel_publisher.py` | Router subprocess | Mantener como CLI entry | Refactor |
| `connectors/publishers/*.py` | Wrappers a stub o scripts | Unificar bajo `PublisherBase` | Refactor |
| `executor.publish_*` | Llama scripts sin `tenant_id` | `publish_service.py` | **Corregir** |

**Duplicación de lógica cola/log:**

```text
linkedin_publisher.py  → QUEUE_PATH hardcoded Marketing/content_queue.json
meta_publisher.py      → idem
executor.py            → usa effective_paths(tenant_id)  ← INCONSISTENTE
```

### OAuth handlers (escriben `.env`, no tenant)

| Archivo | Puerto | Problema |
|---------|--------|----------|
| `linkedin_oauth.py` | 8091 | Tokens globales |
| `meta_oauth.py` | 8093 | Tokens globales |
| `google_oauth.py` | 8094 | Tokens globales |
| `tiktok_oauth.py` | 8095 | Tokens globales |

**Deben** escribir en `tenant_secrets.db` con `tenant_id` del flujo OAuth.

### Configuración (§18)

| Módulo | Responsabilidad | Solapamiento |
|--------|-----------------|--------------|
| `tenant_secrets.py` | Cifrado, test conexión, mask | Core secrets |
| `settings_center.py` | JSON tenant, users, products | Config no-secreta |
| `tenant_profile.py` | Branding | Tenant metadata |
| `app.py` | 30+ rutas settings mezcladas | Debería ser `routes/settings_routes.py` |
| `rbac.py` | Permisos | Debería estar en `auth_service.py` |

**No existe:** `settings_service.py`, `auth_service.py`, `audit_service.py`.

### Dashboard / CRM

| Archivo | Duplicación |
|---------|-------------|
| `dashboard_data.py` | Credenciales Odoo: `tenant_secrets` + fallback `os.environ` |
| `tenant_secrets.test_crm` | Misma lógica Odoo |
| `odoo_sync.py` | Solo `.env` |

---

## 10. Riesgos de seguridad

| # | Riesgo | Severidad |
|---|--------|-----------|
| 1 | Publishers usan tokens globales `.env` → Relatic podría publicar con credenciales EasyTech | **Crítica** |
| 2 | Sin `user_tenants` → escalación horizontal entre tenants | **Alta** |
| 3 | `ACCIO_API_KEY` global bypass de RBAC con rol admin | **Alta** |
| 4 | OAuth guarda tokens en `.env` compartido | **Alta** |
| 5 | `users.json` con `password_hash` en disco sin BD central | Media |
| 6 | Auditoría solo en `settings_audit.log`, no estructurada | Media |
| 7 | Scripts cron (`accio_tick.sh`) sin `tenant_id` | Media |
| 8 | Fernet key derivada de `ACCIO_API_KEY` si falta `ACCIO_SECRETS_KEY` | Media |
| 9 | Roles spec (`super_admin`, etc.) no implementados | Media |

---

## 11. Plan de migración a tenant settings (propuesto)

### Fase M1 — Auth (sin BD, mínimo viable)

```text
1. Crear auth_service.py
   - login/logout/session/current_user
   - user_tenants.json global o tabla SQLite users + user_tenants
2. Roles: super_admin | tenant_admin | marketing_operator | viewer
3. Filtrar tenant selector y API por user_tenants
4. Deprecar login por api_key en UI (mantener solo header para scripts internos)
```

### Fase M2 — Settings unificado

```text
1. Crear settings_service.py
   - delega secretos → tenant_secrets
   - delega config → settings_center / JSON
   - mask, validate, audit
2. Renombrar namespace platform.accio_api_key → solo integraciones externas
3. Pantalla Conectores según spec §7 (estado, conectar, probar, renovar, desconectar)
```

### Fase M3 — Publishers tenant-aware (crítico)

```text
1. PublisherBase(tenant_id, credentials, content, media)
2. Refactor linkedin_publisher + meta_publisher
3. executor.publish_* pasa --tenant-id a subprocess
4. Cola siempre desde Marketing/tenants/{id}/content_queue.json
5. Eliminar require_env() global; usar tenant_secrets.connector_env_value()
6. Marcar .env client tokens como DEPRECATED en docs
```

### Fase M4 — OAuth → tenant

```text
1. Flujo OAuth incluye tenant_id en state
2. Callback escribe tenant_secrets.db
3. Apagar escritura a .env para tokens de cliente
```

### Fase M5 — Auditoría y logs

```text
1. audit_log SQLite (o ampliar settings_audit.log)
2. publish_logs con tenant_id + user_id
3. Logs UI por tenant
```

### Fase M6 — Limpieza

```text
1. Eliminar rutas legacy
2. Eliminar fallback Marketing/accio/
3. Reporte final código muerto
4. Actualizar .gitignore §23
```

---

## 12. Matriz spec vs estado actual

| Criterio spec §27 | Cumple |
|-------------------|--------|
| No pedir API keys al publicar (UI) | ✅ |
| Publicación usa credenciales tenant guardadas | ❌ |
| Usuario solo ve tenants asignados | ❌ |
| No mezclar campañas entre tenants | ⚠️ (datos sí; publish no) |
| Tokens enmascarados en UI | ✅ |
| Secretos no en Git | ✅ (con gaps en gitignore) |
| Publishers no leen tokens globales | ❌ |
| Auditoría de cambios | ⚠️ parcial |
| Reporte código muerto | ✅ (este doc) |
| Reporte código duplicado | ✅ (este doc) |

---

## 13. Prioridad inmediata (orden del doc §28)

```text
1. ✅ Diagnóstico autenticación y credenciales     ← ESTE DOCUMENTO
2. ✅ Diagnóstico código muerto y duplicado         ← ESTE DOCUMENTO
3. ⏳ Diseño final settings_service + auth_service  ← requiere GO
4. ⏳ Login real + user_tenants                     ← requiere GO
5. ⏳ Configuración segura unificada                ← requiere GO
6. ⏳ Migrar publishers a tenant credentials       ← requiere GO (máxima prioridad técnica)
```

---

## 14. Instrucción para el equipo

**No implementar Entregable 2** hasta GO explícito del responsable de producto.

La primera línea de código post-GO recomendada:

> Hacer que `linkedin_publisher.py` y `meta_publisher.py` reciban `--tenant-id` y lean credenciales desde `tenant_secrets` + cola desde `Marketing/tenants/{id}/`.

Sin eso, el dashboard puede tener el mejor login del mundo y **seguirá fallando al publicar** o publicará con la cuenta equivocada.

---

*Documento generado para Easy Technology Services — uso interno.*
