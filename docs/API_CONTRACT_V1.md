# EM+Acción — API Pública · Contrato v1

**Acción:** 6  
**Versión:** 1.0 (diseño)  
**Estado:** Entregado para revisión — **sin código, sin OpenAPI YAML**  
**Alcance:** contrato global de la plataforma + primer recurso (`MarketingPlan`)

> **Regla permanente.** Ningún endpoint llama al Domain Service. Siempre: **HTTP → Application Layer → Domain Service**.
>
> **Coexistencia.** La API operativa legacy (`/accio/…`, cola, órdenes, tick) sigue existiendo. Esta especificación define la **API pública versionada** para recursos de dominio. No reemplaza legacy en v1; convive hasta migración explícita.

**Referencias:** [`MARKETING_PLAN_APPLICATION_LAYER.md`](MARKETING_PLAN_APPLICATION_LAYER.md) · [`MARKETING_PLAN_DOMAIN_SCHEMA_v1.md`](MARKETING_PLAN_DOMAIN_SCHEMA_v1.md)

---

## 1. Convenciones globales

Aplican a **toda** EM+Acción API v1 y a recursos futuros (Campaign, Calendar, Leads, …).

### 1.1 Base URL y versión

| Elemento | Valor |
|----------|-------|
| Prefijo público | `/api/v1` |
| Ejemplo producción | `https://emaccion.etsrv.site/api/v1` |
| Ejemplo engine | `https://n8n.etsrv.site/api/v1` |

Toda ruta pública comienza con `/api/v1`. Sin versión en path → **404** (no redirect silencioso).

### 1.2 Formato

- **Content-Type:** `application/json; charset=utf-8`
- **Accept:** `application/json`
- Cuerpo vacío en GET/HEAD; DELETE puede devolver `204` sin cuerpo
- Claves JSON: **snake_case**
- Sin campos `null` omitibles en requests (cliente puede omitir; servidor normaliza)

### 1.3 Fechas y hora

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| **date** | ISO 8601 fecha | `"2026-07-01"` |
| **datetime** | ISO 8601 UTC con `Z` | `"2026-06-26T17:00:00Z"` |
| **timezone** | Almacenamiento y API en **UTC** | El tenant tiene timezone para UI; la API v1 siempre UTC |

### 1.4 Identificadores

| Tipo | Regla |
|------|-------|
| **tenant_id** | Slug existente en registry (`easytech`, …) |
| **app_id** | Slug de app del tenant (`en1`, `default`, …) |
| **Resource id** | String opaco (`mpl_…`, UUID v4, …). El cliente no construye ids; los recibe del servidor |
| **UUID** | Permitido donde el dominio lo use; no exigido en v1 para `MarketingPlan` |

### 1.5 Ámbito multi-tenant

Patrón base para recursos de workspace:

```
/api/v1/tenants/{tenant_id}/apps/{app_id}/…
```

- `{tenant_id}` y `{app_id}` siempre en path (no solo en body).
- El servidor valida que el actor autenticado puede operar en ese tenant.
- Cross-tenant → **403 Forbidden** (no 404, para no filtrar existencia).

### 1.6 Paginación

Query params estándar (listados):

| Param | Tipo | Default | Máx |
|-------|------|---------|-----|
| `page` | integer ≥ 1 | `1` | — |
| `page_size` | integer | `20` | `100` |

Respuesta en `meta.pagination`:

```json
{
  "page": 1,
  "page_size": 20,
  "total_items": 45,
  "total_pages": 3
}
```

Recursos sin paginación en v1 documentan excepción explícita.

### 1.7 Ordenamiento

| Param | Valores |
|-------|---------|
| `sort` | Campo permitido por recurso (ej. `created_at`, `nombre`) |
| `order` | `asc` \| `desc` (default `desc` para `created_at`) |

Campos no ordenables → **400** `InvalidSortField`.

### 1.8 Filtros

- Filtros por query param snake_case: `?estado=activo`
- Múltiples valores: `?estado=borrador&estado=pausado` o `?estado=borrador,pausado` (implementación elige uno; contrato preferir repetición de param)
- Filtros no soportados ignorados → **prohibido**; filtro desconocido → **400** `InvalidFilter`

### 1.9 Envelope de respuesta

**Éxito — recurso único:**

```json
{
  "data": { },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_version": "v1"
  }
}
```

**Éxito — colección:**

```json
{
  "data": [ ],
  "meta": {
    "correlation_id": "...",
    "api_version": "v1",
    "pagination": { }
  }
}
```

**Comandos con eventos** (opcional v1): incluir `meta.events` con resumen serializable (tipo + ids), no objetos de dominio crudos.

### 1.10 Correlation ID

| Dirección | Header |
|-----------|--------|
| Cliente → servidor | `X-Correlation-Id` (opcional; UUID recomendado) |
| Servidor → cliente | Mismo valor en header y en `meta.correlation_id` |

Si el cliente no envía, el servidor genera uno. Debe aparecer en logs de auditoría.

### 1.11 Idempotency Key

| Header | Uso |
|--------|-----|
| `Idempotency-Key` | Documentado para POST que crean o transicionan estado |

**v1:** especificado; **implementación diferida**. Cuando exista: misma key + mismo body dentro de ventana (ej. 24 h) → misma respuesta sin duplicar efecto.

Aplica a: `POST …/marketing-plans`, `POST …/activate`, `POST …/pause`, `POST …/complete`.

### 1.12 Autenticación (contrato, sin implementación)

Documentado para consumidores; JWT/auth real en fase REST API:

| Mecanismo | Uso |
|-----------|-----|
| Sesión dashboard | Cookie de sesión existente EM+Acción |
| Integraciones / n8n | `Authorization: Bearer <token>` |
| CLI | Token o sesión según entorno |

Sin credenciales → **401 Unauthorized**. Sin permiso RBAC → **403 Forbidden**.

---

## 2. Convención REST

| Método | Uso en EM+Acción v1 | Idempotente | Body |
|--------|---------------------|-------------|------|
| **GET** | Consulta; sin efectos colaterales | Sí | No |
| **POST** | Crear recurso; **acciones** (`/activate`, …) | No* | Sí |
| **PUT** | Reemplazo completo (reservado; poco uso v1) | Sí | Sí |
| **PATCH** | Actualización parcial | No | Sí |
| **DELETE** | Eliminar (solo donde el dominio lo permita; Plan v1 **sin delete**) | Sí | No |

\* POST idempotente solo con `Idempotency-Key` cuando se implemente.

**Reglas:**

- **No** usar POST para consultas.
- **No** usar GET para mutaciones.
- Transiciones de estado del Plan → **POST** en sub-recurso (`/activate`), no PATCH de `estado` (el dominio controla la máquina de estados).
- **PATCH** no puede cambiar `estado` directamente en v1.

---

## 3. DTOs — separación de capas

```
Request DTO (JSON)
       ↓  mapper API
Application Input / Query
       ↓  caso de uso
Application Result / entidad dominio
       ↓  mapper API
Response DTO (JSON)
```

| Capa | Tipo | Expuesto en HTTP |
|------|------|------------------|
| Domain | `MarketingPlan`, enums internos | **Nunca** |
| Application | `CreateMarketingPlanInput`, … | **Nunca** |
| API | `MarketingPlanResponse`, `CreateMarketingPlanRequest`, … | **Sí** |

Los Response DTO reflejan el schema del dominio pero son **tipos API estables** (pueden diferir en nombres anidados, no en semántica).

---

## 4. Error Contract

Estructura **única** para toda la plataforma:

```json
{
  "error": {
    "code": "ActivePlanResolutionRequired",
    "message": "Existe otro plan activo; se requiere resolución",
    "details": {
      "active_plan_id": "mpl_001"
    },
    "source": "domain"
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_version": "v1"
  }
}
```

| Campo | Descripción |
|-------|-------------|
| `code` | Código estable (mismo string que dominio/aplicación cuando aplique) |
| `message` | Humano, no i18n en v1 |
| `details` | Objeto opcional; contexto machine-readable |
| `source` | `domain` \| `application` \| `api` |

**Prohibido:** `{ "error": "string suelta" }` sin estructura.

### 4.1 Mapeo HTTP (referencia v1)

| HTTP | Cuándo |
|------|--------|
| **400** | Validación API, JSON inválido, filtro/sort inválido |
| **401** | No autenticado |
| **403** | Forbidden (RBAC) |
| **404** | Recurso no encontrado en ámbito tenant |
| **409** | Conflicto dominio (ej. `ActivePlanResolutionRequired`, transición inválida) |
| **422** | Error dominio de validación (ej. `InvalidDateRange`, `PlanNotDeclarative`) |
| **500** | Error interno no esperado |

Códigos dominio → HTTP se fijan en implementación REST; este contrato no cambia códigos de dominio.

---

## 5. Versionado

### 5.1 v1 (actual)

- Prefijo `/api/v1`
- Primer recurso: `marketing-plans`
- Recursos futuros bajo el mismo prefijo

### 5.2 Cuándo nace v2

- Cambio **breaking** en shape de DTOs públicos
- Eliminación de campos obligatorios
- Cambio semántico de códigos de error estables
- Cambio de URL de recurso

### 5.3 Compatibilidad

- **v1** se mantiene mientras haya consumidores
- Campos nuevos en responses → compatibles (clientes ignoran)
- Campos nuevos obligatorios en requests → **breaking** → v2

### 5.4 Deprecación

Headers en respuestas deprecadas:

```
Deprecation: true
Sunset: Sat, 01 Jan 2028 00:00:00 GMT
Link: </api/v2/...>; rel="successor-version"
```

Mínimo **6 meses** entre anuncio Sunset y apagado en producción.

---

## 6. Recurso: MarketingPlan

Primer recurso de la API pública. Alineado con Application Layer Pieza 5.

### 6.1 Nombre REST

| Concepto | Valor |
|----------|-------|
| Recurso | `marketing-plans` |
| Singular DTO | `marketing_plan` |

### 6.2 Endpoints

Base:

```
/api/v1/tenants/{tenant_id}/apps/{app_id}/marketing-plans
```

| Método | Ruta | Caso de uso Application | Descripción |
|--------|------|-------------------------|-------------|
| **GET** | `…/marketing-plans` | `ListMarketingPlans` | Lista planes; filtros `estado`, paginación, sort |
| **POST** | `…/marketing-plans` | `CreateMarketingPlan` | Crea plan en `borrador` |
| **GET** | `…/marketing-plans/active` | `GetActiveMarketingPlan` | Plan activo de la app (0 o 1) |
| **GET** | `…/marketing-plans/{plan_id}` | `GetMarketingPlan` | Plan por id |
| **PATCH** | `…/marketing-plans/{plan_id}` | `UpdateMarketingPlan` | Actualiza campos editables |
| **POST** | `…/marketing-plans/{plan_id}/activate` | `ActivateMarketingPlan` | Transición → `activo` |
| **POST** | `…/marketing-plans/{plan_id}/pause` | `PauseMarketingPlan` | Transición → `pausado` |
| **POST** | `…/marketing-plans/{plan_id}/complete` | `CompleteMarketingPlan` | Transición → `finalizado` |

**Notas:**

- `GET …/active` definido **antes** de `{plan_id}` en enrutamiento (implementación futura).
- **Sin DELETE** en v1 (dominio: `finalizado` es terminal).
- **Sin PATCH** de `estado`; usar acciones POST.

### 6.3 Permisos (RBAC)

| Endpoint | Permiso |
|----------|---------|
| GET (list, get, active) | `read` |
| POST create, PATCH | `config` o `admin` |
| POST activate, pause, complete | `admin` |

### 6.4 Request DTOs

#### `CreateMarketingPlanRequest` — POST create

```json
{
  "nombre": "Plan Q3 EN1",
  "objetivo_general": "Incrementar leads cualificados…",
  "strategy_type": "lead_generation",
  "north_star_metric": "Leads cualificados mensuales",
  "success_criteria": ["100 leads", "20 reuniones"],
  "publico_objetivo": ["Gerentes PYME"],
  "marketing_brief": "Texto largo…",
  "periodo": {
    "inicio": "2026-07-01",
    "fin": "2026-09-30"
  },
  "budget": {
    "amount": "5000.00",
    "currency": "USD"
  },
  "prioridad": "alta",
  "observaciones": ""
}
```

Campos prohibidos (R9) en body → **422** `ForbiddenField`.

#### `UpdateMarketingPlanRequest` — PATCH

Todos los campos opcionales (parcial). Mismos tipos que create. No incluye `estado`, `id`, `tenant_id`, `app_id`.

#### `ActivateMarketingPlanRequest` — POST activate

```json
{
  "resolution": "finalize_previous"
}
```

| `resolution` | Valores |
|--------------|---------|
| Opcional | `finalize_previous` \| `pause_previous` |

Omitido cuando no hay conflicto R2. Obligatorio en **retry** tras **409** `ActivePlanResolutionRequired`.

#### `PauseMarketingPlanRequest` / `CompleteMarketingPlanRequest`

Body vacío `{}` o ausente en v1.

#### Query — GET list

| Param | Tipo |
|-------|------|
| `estado` | `borrador` \| `activo` \| `pausado` \| `finalizado` |
| `page`, `page_size`, `sort`, `order` | Convención §1 |

### 6.5 Response DTO — `MarketingPlanResponse`

```json
{
  "id": "mpl_001",
  "tenant_id": "easytech",
  "app_id": "en1",
  "nombre": "Plan Q3 EN1",
  "objetivo_general": "…",
  "strategy_type": "lead_generation",
  "north_star_metric": "…",
  "success_criteria": ["100 leads"],
  "publico_objetivo": ["Gerentes PYME"],
  "marketing_brief": "…",
  "periodo": {
    "inicio": "2026-07-01",
    "fin": "2026-09-30"
  },
  "budget": {
    "amount": "5000.00",
    "currency": "USD"
  },
  "estado": "borrador",
  "prioridad": "alta",
  "observaciones": "",
  "created_at": "2026-06-26T17:00:00Z",
  "updated_at": "2026-06-26T17:00:00Z",
  "created_by": "admin@easytech",
  "activated_at": null
}
```

#### `MarketingPlanListResponse`

`data`: array de `MarketingPlanResponse` + `meta.pagination`.

#### `MarketingPlanActiveResponse`

`data`: `MarketingPlanResponse` o `null` si no hay activo (**200**, no 404).

### 6.6 Enums (API)

**strategy_type:** `lead_generation`, `brand_awareness`, `remarketing`, `launch`, `upselling`, `cross_selling`, `retention`

**estado:** `borrador`, `activo`, `pausado`, `finalizado`

**prioridad:** `alta`, `media`, `baja`

**resolution:** `finalize_previous`, `pause_previous`

### 6.7 Errores específicos MarketingPlan

| code | HTTP típico |
|------|-------------|
| `PlanNotFound` | 404 |
| `Forbidden` | 403 |
| `ActivePlanResolutionRequired` | 409 |
| `InvalidDateRange` | 422 |
| `PlanNotDeclarative` | 422 |
| `InvalidStatusTransition` | 409 |
| `PlanCompleted` | 409 |
| `PlanNotEditable` | 409 |
| `ForbiddenField` | 422 |

---

## 7. Recursos futuros (placeholder)

Misma convención global; **sin endpoints finales** hasta su pieza de dominio.

| Recurso | Ruta prevista (v1+) |
|---------|-------------------|
| Campaigns | `…/apps/{app_id}/campaigns` |
| Calendar | `…/apps/{app_id}/calendar-events` |
| Content queue | `…/apps/{app_id}/content-queue` |
| Leads | `…/tenants/{tenant_id}/leads` |
| Metrics | `…/apps/{app_id}/metrics` |
| Assets | `…/apps/{app_id}/assets` |

Cada recurso nuevo añade sección en revisión menor de este contrato o en **v2** si breaking.

---

## 8. Consumers

Quién consume la API pública y cómo debe usarla:

| Consumer | Uso | Auth esperada |
|----------|-----|---------------|
| **Dashboard** EM+Acción | CRUD Plan, activar, visualizar activo | Sesión usuario |
| **Web** (landings, portales) | Solo lectura plan activo (futuro) | Token scoped |
| **CLI** | Operaciones admin/scripting | Bearer / API key |
| **Cron / Scheduler** | Consultar plan activo; no mutar sin actor | Service token |
| **IA / Context Builder** | **Solo lectura** plan activo vía API o Application directa | Service token |
| **n8n / automatizaciones** | Webhooks, activación bajo aprobación humana | Bearer |
| **Apps móviles** (futuro) | Lectura + propuestas | OAuth (futuro) |
| **Integraciones** (Odoo, CRM) | Atribución, métricas (futuro) | API key |

**Reglas:**

- IA **no** tiene endpoints exclusivos; usa los mismos que Dashboard (lectura) o Application Layer (interno).
- Cron **no** bypass de RBAC; actor de servicio documentado.
- Todos los mutadores pasan por Application Layer (y RBAC).

---

## 9. OpenAPI (preparación, sin YAML)

Este contrato debe mapear 1:1 a OpenAPI 3.1:

| Elemento contrato | OpenAPI |
|-------------------|---------|
| `/api/v1` | `servers` + `paths` prefix |
| Envelope `data` / `meta` | `components.schemas` wrapper |
| `error` object | `components.schemas.ApiError` |
| Enums | `enum` en schemas |
| Paginación | `parameters` + `PaginationMeta` |
| Acciones POST | `operationId` por caso de uso |

**Pieza siguiente (OpenAPI):** generar `openapi/v1.yaml` desde este documento, no al revés.

---

## 10. Hitos estratégicos (post-contrato)

Tras aprobar este contrato, el siguiente gran hito recomendado es un **flujo vertical** (no big-bang API):

```
Crear Plan → Activar → Visualizar → Context Builder consume → IA propone
```

Ese slice valida: Application → Domain → JSON → API (subset) → UI mínima → IA lectura.

El resto de recursos repiten el mismo patrón.

---

## 11. Criterios de aceptación (Pieza 6 diseño)

| Criterio | |
|----------|---|
| Convenciones globales definidas | ✓ |
| REST documentado | ✓ |
| DTOs separados de dominio | ✓ |
| Error contract único | ✓ |
| Versionado y deprecación | ✓ |
| MarketingPlan completo | ✓ |
| Consumers documentados | ✓ |
| OpenAPI-ready | ✓ |
| Sin FastAPI / código | ✓ |

---

## 12. Próximo paso

| Pieza | Estado |
|-------|--------|
| Revisión / aprobación API Contract v1 | Pendiente |
| OpenAPI YAML | NO GO hasta aprobación |
| REST API (implementación) | NO GO |
| Flujo vertical (slice) | Tras subset API |

---

*EM+Acción — API Pública · Contrato v1.0 · Pieza 6*
