# Aclaración de arquitectura — Tenant vs Apps en EMAcción

**Estado:** Fase 3 implementada (2026-06-27) · **Pendiente:** leads EN1, UI mapping dashboard
**Fecha:** 2026-06-26  
**Complementa:** `docs/CONTEXTO.md`, `docs/EMACCION_PHASE_M_MULTI_TENANT.md`

---

Después de revisar el modelo, hay una corrección conceptual importante.

La arquitectura de EMAcción **no debe diseñarse alrededor de ETS**, sino como un producto SaaS que cualquier empresa pueda utilizar.

---

## Modelo correcto

```
Tenant (Empresa)
    │
    ├── Apps
    │      ├── Campañas
    │      ├── Publicaciones
    │      ├── Flyers
    │      ├── Landing Pages
    │      ├── IA / Knowledge
    │      ├── Leads
    │      ├── Métricas
    │      └── Productos (opcional)
    │
    ├── Usuarios
    ├── Conectores
    ├── Configuración
    └── CRM
```

---

## Qué es un Tenant

Un **Tenant** representa una empresa que utiliza EMAcción.

Ejemplos:

- Easy Technology Services
- Modecosa
- International Institute
- Relatic
- Cualquier cliente futuro

Cada Tenant está completamente aislado del resto.

El Tenant es el límite de seguridad, usuarios, configuración y datos.

---

## Qué es una App

Una **App** representa una línea de negocio, producto, servicio o marca que ese Tenant desea promocionar.

- No es un Tenant.
- No crea aislamiento.
- No tiene usuarios propios.
- Vive dentro del Tenant.

Por ejemplo:

```
Tenant: Easy Technology Services

Apps:
• Easy NodeOne
• EPayRoll
• EPOSOne
• EClassOne
• EConverso
• Odoo
• Facturación Electrónica
• Servicios de Desarrollo
```

Otro ejemplo:

```
Tenant: Modecosa

Apps:
• Ferretería
• Materiales
• Promociones
• Sucursales
```

Otro ejemplo:

```
Tenant: International Institute

Apps:
• Diplomados
• Cursos
• Talleres
• Certificaciones
```

---

## La confusión detectada

En el análisis anterior se asumió que:

```
Tenant = ETS únicamente
```

Eso funcionaría para nuestro caso actual, pero rompe el objetivo comercial de EMAcción.

EMAcción debe poder venderse como SaaS.

Por lo tanto, ETS es simplemente **un Tenant más**.

Mañana podremos crear:

- Tenant: Modecosa
- Tenant: Relatic
- Tenant: International Institute

sin modificar la arquitectura.

---

## Relatic y Modecosa

Hay dos escenarios distintos.

### Escenario 1 — App dentro de ETS

Relatic es un producto del portafolio de ETS.

```
Tenant: ETS
  └── App: Relatic
```

### Escenario 2 — Tenant independiente

Relatic compra EMAcción para gestionar su propio marketing.

```
Tenant: Relatic

Apps:
• CRM
• Eventos
• Servicios
• Noticias
```

En este caso Relatic deja de ser una App de ETS y pasa a ser un Tenant completamente independiente.

**La arquitectura debe soportar ambos escenarios sin cambios.**

---

## Modelo de datos recomendado

```
Tenant
--------
tenant_id
name
status
branding
timezone
crm
settings

App
--------
app_id
tenant_id
name
slug
description
logo
brand_colors
tone
target_audience
status

Campaign
--------
campaign_id
tenant_id
app_id

Content
--------
content_id
tenant_id
app_id

Lead
--------
lead_id
tenant_id
app_id

Connector
--------
connector_id
tenant_id
(opcionalmente app_id si algún conector pertenece solo a una App)
```

---

## Organización de archivos

```
Marketing/
tenants/
    ets/
        apps/
            en1/
            epayroll/
            eposone/
            eclassone/
            econverso/

    modecosa/
        apps/
            promociones/
            materiales/

    iius/
        apps/
            diplomados/
            cursos/
```

---

## Reglas arquitectónicas

- Un Tenant puede tener muchas Apps.
- Una App siempre pertenece a un solo Tenant.
- Todo registro operativo debe conocer `tenant_id`.
- Todo contenido de marketing debe conocer `app_id`.
- Nunca crear un Tenant para representar una App.
- Nunca asumir que ETS será el único Tenant del sistema.

---

## Objetivo

Construir EMAcción como una plataforma SaaS multi-tenant desde el inicio.

ETS será simplemente el primer Tenant de producción, pero la arquitectura deberá permitir incorporar cualquier empresa nueva sin rediseñar el sistema.

---

## Relación con EN1 (referencia externa)

EN1 (`/admin/organizations`) es otro producto SaaS con su propio CRUD de organizaciones. **No duplicar** ese CRUD en EMAcción.

| EN1 | EMAcción |
|-----|----------|
| `saas_organization` | Equivalente conceptual a **Tenant** (cuando exista sync) |
| — | **App** — capa exclusiva de EMAcción |

Las capturas de EN1 Dev son referencia de producto; la integración API EN1 ↔ EMAcción sigue pendiente.

---

## Estado del código (2026-06-26)

| Concepto acordado | Implementación actual | Gap |
|-------------------|----------------------|-----|
| Tenant SaaS | `tenant_id` + `Marketing/tenants/{id}/` | Parcial — vocabulario UI dice “Empresa” |
| App | `products.json` (catálogo sin cola propia) | **Fase 2** — registry + selector UI + colas filtradas por `app_id` |
| `app_id` en contenido | Cola/campañas a nivel tenant | Posts con `app_id`; filtro por app en API/dashboard/publishers |
| ETS = un tenant | `easytech` ≈ Easy Technology Services | OK como primer tenant |
| Relatic como tenant | `relatic` en registry | OK si escenario 2; conflict si era App de ETS |
| Flyers / IIUS | Globales en `Marketing/flyers/` | Sin `tenant_id` / `app_id` |

**Próximo paso técnico (requiere GO):** leads EN1 → CRM (write) + UI mapping en dashboard.

### Fase 3 implementada (2026-06-27)

- `Motor_Tecnico/accio_engine/en1_organizations.py` — sync **read-only** EN1 ↔ `tenant_id`
- API: `GET /accio/en1/organizations`, `GET /accio/en1/sync`, `POST /accio/{tenant}/settings/en1-mapping`
- Campo `en1_organization_id` en `registry.json` (solo lado EMAcción)
- Referencia EN1 Dev cuando API no configurada; cache local tras fetch live
- Test CRM EN1 valida lectura de organizaciones cuando hay credenciales

### Fase 2 implementada (2026-06-27)

- Selector **App** en dashboard (`static/dashboard.html`) — `localStorage` por tenant
- API dashboard filtrada: `?app_id=` / header `X-Accio-App`
- `executor.py`, `dashboard_data.py`, `app.py` — colas, status, campañas, calendario, métricas por app
- Publishers: `linkedin_publisher.py`, `meta_publisher.py` con `--app-id=`
- App `default` mantiene paths del tenant (retrocompat)

### Fase 1 implementada (2026-06-26)

- `Motor_Tecnico/accio_engine/marketing_app.py`
- `Marketing/tenants/{tenant}/apps/registry.json`
- API: `GET/POST /accio/{tenant}/apps`, `GET /accio/{tenant}/apps/{app_id}`
- App `default` → paths del tenant (sin romper easytech)
- Bootstrap desde `products.json` (easytech: 9 apps)
