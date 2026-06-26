# Fase N — Tenant Settings & API Credentials

**Versión:** 1.0 · **Fecha:** 2026-06-19  
**Estado:** Diseño aprobado — **no implementar runtime sin GO explícito**  
**Depende de:** Fase M (Multi-Tenant Core)

---

## 1. Objetivo

Pantalla de **Configuración por tenant** en EMAcción para registrar, editar y validar credenciales **sin tocar archivos manualmente**.

Reemplaza soluciones temporales (p. ej. `dashboard_client.json` con API key en texto plano).

**Ruta UI:** EMAcción → **Configuración** → APIs / Conectores / CRM

---

## 2. Reglas de seguridad

| Regla | Detalle |
|-------|---------|
| No JSON visible con secretos | No guardar tokens en archivos versionados ni legibles en disco sin cifrar |
| Almacenamiento | Tabla segura cifrada (preferido) o `.env` segmentado por tenant |
| UI | Nunca mostrar secretos completos — solo máscara (`••••••••abcd`) |
| Publicación | **No publicar ni ejecutar campañas** con credenciales nuevas hasta **Probar conexión** OK |
| Auditoría | Log de quién cambió qué (sin valor del secreto) |

---

## 3. Rutas API sugeridas

```
GET  /accio/{tenant_id}/settings
POST /accio/{tenant_id}/settings

GET  /accio/{tenant_id}/settings/connectors
POST /accio/{tenant_id}/settings/connectors

GET  /accio/{tenant_id}/settings/crm
POST /accio/{tenant_id}/settings/crm

POST /accio/{tenant_id}/settings/connectors/{connector_id}/test
POST /accio/{tenant_id}/settings/crm/test
```

Alias cortos (opcional, mismo handler):

```
GET/POST /accio/settings?tenant_id=easytech
```

---

## 4. Campos por sección

### 4.1 APIs / Conectores (por tenant)

| Campo | Conector |
|-------|----------|
| LinkedIn OAuth / access token | LinkedIn |
| Meta App ID | Facebook / Instagram |
| Meta App Secret | Facebook / Instagram |
| Facebook Page ID | Facebook |
| Facebook Page Token | Facebook |
| Instagram User ID | Instagram |
| Google OAuth (refresh token) | Google Business |
| TikTok OAuth | TikTok |

### 4.2 CRM (por tenant)

| Campo | Destino |
|-------|---------|
| EN1 API URL | EN1 CRM |
| EN1 API Key | EN1 CRM |
| Odoo URL | Odoo |
| Odoo DB | Odoo |
| Odoo usuario | Odoo |
| Odoo API key | Odoo |

### 4.3 Plataforma (opcional)

| Campo | Uso |
|-------|-----|
| Dashboard API key por tenant | Auth operador solo para ese cliente |
| Webhook URLs | Notificaciones |

---

## 5. Almacenamiento seguro (implementación objetivo)

**Opción A — Tabla cifrada (recomendada)**

```
tenant_secrets
  tenant_id
  namespace        # connectors | crm | platform
  key              # linkedin_access_token, meta_app_secret, …
  value_encrypted  # Fernet / AES con MASTER_KEY en .env
  updated_at
  updated_by
  validated_at
  validation_status
```

`MASTER_KEY` solo en `.env` del servidor — nunca en Git.

**Opción B — `.env` por tenant (transitorio)**

```
/opt/easytech_marketing/deploy/secrets/tenants/easytech.env
/opt/easytech_marketing/deploy/secrets/tenants/relatic.env
```

Permisos `600`, propietario servicio, gitignored.

---

## 6. UI Dashboard — tab Configuración

### Secciones

1. **General** — nombre, dominio, locale, CRM destino por defecto
2. **Conectores** — formulario por canal con estado (conectado / pendiente / error)
3. **CRM** — Odoo / EN1
4. **Seguridad** — rotación de keys, última validación

### Controles por campo secreto

- Input `type=password` con toggle mostrar
- Placeholder si ya existe valor guardado: `(configurado — dejar vacío para no cambiar)`
- Botón **Probar conexión** por conector
- Badge: `✅ Validado` / `⚠️ Sin validar` / `❌ Error`

### Auto-login dashboard

La opción de **no pedir API key cada vez** pasa a:

- Sesión tras login con `ACCIO_API_KEY` de plataforma, **o**
- Cookie httpOnly emitida por el servidor tras auth válida

**No** inyectar API key en HTML (`window.__ACCIO_PRELOAD_KEY__`) — eliminar al implementar Fase N.

---

## 7. Flujo de validación

```
Usuario guarda credenciales
        │
        ▼
POST /settings/connectors (status: pending_validation)
        │
        ▼
Usuario pulsa "Probar conexión"
        │
        ├── OK → validated_at, status: active → puede publicar
        └── FAIL → status: error, mensaje en UI → NO publicar
```

`executor.py` y publishers deben comprobar `validation_status === active` antes de usar credenciales.

---

## 8. Auditoría

`tenant_settings_audit.log` o tabla:

```
timestamp, tenant_id, actor, section, field_name, action (set|clear|test), success
```

Nunca registrar el valor del secreto.

---

## 9. Tareas Fase N

| ID | Tarea | Estado |
|----|-------|--------|
| N1 | Módulo `tenant_secrets.py` (cifrado + CRUD) | ❌ |
| N2 | Endpoints `/settings`, `/settings/connectors`, `/settings/crm` | ❌ |
| N3 | Tab Configuración en dashboard | ❌ |
| N4 | Máscara de secretos + no reescribir si vacío | ❌ |
| N5 | Botón Probar conexión por conector | ❌ |
| N6 | Bloqueo publicación sin validación | ❌ |
| N7 | Auditoría de cambios | ❌ |
| N8 | Eliminar `dashboard_client.json` y preload en HTML | ❌ |
| N9 | Migrar secretos actuales `.env` → almacén por tenant (`easytech`) | ❌ |

**Criterio de cierre:** Operador configura LinkedIn/Meta/Odoo/EN1 de EasyTech y Relatic desde el dashboard, sin editar archivos; secretos cifrados; conexión validada antes de publicar.

---

## 10. Estado actual (gap)

| Lo pedido | Lo existe hoy | Cumple |
|-----------|---------------|--------|
| Pantalla Configuración por tenant | ❌ No | No |
| Almacenamiento seguro cifrado | ❌ No | No |
| `dashboard_client.json` con API key | ✅ Parche temporal | **No** — viola regla de no JSON visible |
| Inyección key en HTML | ✅ `__ACCIO_PRELOAD_KEY__` | **No** — inseguro para multi-tenant |

**Acción:** Fase N reemplaza el parche; Fase M define el `tenant_id` bajo el cual vive cada configuración.

---

## 11. Referencias

- [EMACCION_PHASE_M_MULTI_TENANT.md](EMACCION_PHASE_M_MULTI_TENANT.md)
- [ROADMAP.md](ROADMAP.md)
- [CONECTAR_REDES.md](CONECTAR_REDES.md)
- [deploy/SECRETS.md](../deploy/SECRETS.md)
