# Pieza 5 — Application Layer: Marketing Plan

**Versión:** 1.1 (diseño aprobado)  
**Estado:** ✅ Aprobado — **GO implementación**  
**Fuentes:** [`MARKETING_PLAN_DOMAIN_v1.1.md`](MARKETING_PLAN_DOMAIN_v1.1.md) · [`MARKETING_PLAN_DOMAIN_SERVICE.md`](MARKETING_PLAN_DOMAIN_SERVICE.md) · [`MARKETING_PLAN_JSON_ADAPTER.md`](MARKETING_PLAN_JSON_ADAPTER.md)

> **Fase B.** Casos de uso que orquestan el dominio hacia interfaces futuras (API, dashboard, IA, cron).
>
> **Regla permanente:** ningún endpoint, cron, dashboard ni asistente IA podrá llamar directamente al Domain Service. Siempre: **Interfaz → Application → Domain**.

---

## 1. ¿Qué es la Application Layer?

La **Application Layer** traduce **intenciones del usuario o del sistema** en llamadas al **Servicio de Dominio**, después de autorización (R7) y resolución de contexto operativo (tenant, app, actor).

```
HTTP / Dashboard / Cron / IA (futuro)
              ↓
    Application Services   ← Pieza 5
              ↓
    MarketingPlanDomainService
              ↓
    MarketingPlanRepository (puerto)
              ↓
    Infrastructure Adapters
```

**Regla:** la aplicación **coordina**; el dominio **decide** reglas R1–R9.

---

## 1.1 Principios del contrato (v1.1)

### Principio 1 — Un caso de uso = una intención de negocio

No servicios genéricos (`execute`, `process`, `handle`). Cada clase representa una intención:

- `CreateMarketingPlan`, `ActivateMarketingPlan`, `GetMarketingPlan`, …

### Principio 2 — Commands y Queries separados

Aunque no haya CQRS completo:

- **Comandos** (`use_cases/commands/`) mutan estado → devuelven `CommandResult`.
- **Consultas** (`use_cases/queries/`) solo leen → devuelven `MarketingPlan` o listas; **nunca** publican eventos.

### Principio 3 — Application Layer no contiene negocio

La aplicación **coordina, autoriza, publica eventos e invoca dominio**. **Nunca** decide R1–R9, estados ni validaciones de agregado.

### Principio 4 — Múltiples consumidores, un solo camino

REST, Dashboard, CLI, Cron, IA y Scheduler invocan **la misma** Application Layer. Sin caminos especiales para IA.

---

## 2. ¿Qué hace y qué no hace?

### Hace

- Exponer **casos de uso** estables (comandos y consultas) para el agregado `MarketingPlan` V1.
- Verificar **R7** (RBAC) antes de invocar el dominio.
- Resolver **contexto de sesión**: `tenant_id`, `app_id`, `actor_id` (usuario autenticado).
- Invocar `MarketingPlanDomainService` con comandos de dominio ya construidos.
- Propagar **eventos de dominio** a infraestructura de auditoría (puerto futuro; no implementar en diseño).
- Traducir `DomainError` → errores de aplicación (sin HTTP; la API lo hará en Pieza 6).

### No hace

- Reglas R1–R9, transiciones, validaciones de agregado.
- Persistencia directa (JSON, SQL, archivos).
- HTTP, REST, serialización JSON de respuestas API.
- UI, templates, prompts IA.
- Orquestar Campaign, Calendar, ContentQueue, Metrics (futuro — placeholders §8).
- Modificar Knowledge Base, cola de publicaciones o conectores.

---

## 3. Casos de uso — Comandos (mutaciones)

Cada caso de uso = una operación de aplicación con entrada de aplicación → comando de dominio.

| Caso de uso | Permiso RBAC | Orquesta | Comando dominio |
|-------------|--------------|----------|-----------------|
| **CreateMarketingPlan** | `config` o `admin` | Validar tenant/app en contexto; mapear DTO → `CreatePlanCommand`; llamar `create_plan`; publicar eventos | `CreatePlanCommand` |
| **UpdateMarketingPlan** | `config` o `admin` | Cargar contexto; mapear campos editables; `update_plan` | `UpdatePlanCommand` |
| **ActivateMarketingPlan** | `admin` | Si UI envió resolución R2, incluir `ConflictResolution`; `activate_plan` | `ActivatePlanCommand` |
| **PauseMarketingPlan** | `admin` | `pause_plan` | `PausePlanCommand` |
| **CompleteMarketingPlan** | `admin` | `complete_plan` | `CompletePlanCommand` |

**Actor:** `actor_id` del usuario autenticado → `created_by`, `updated_by`, `activated_by`, etc.

**R2 en aplicación:** si `activate_plan` devuelve `ActivePlanResolutionRequired`, la capa aplicación **no** resuelve sola — devuelve ese error a la UI/API para que el administrador elija `finalize_previous` o `pause_previous` y reintente con resolución explícita.

---

## 4. Casos de uso — Consultas (solo lectura)

| Caso de uso | Permiso RBAC | Orquesta | Dominio |
|-------------|--------------|----------|---------|
| **GetMarketingPlan** | `read` (mínimo) | Verificar plan pertenece al tenant del contexto; `get_plan` | `get_plan(plan_id, tenant_id)` |
| **GetActiveMarketingPlan** | `read` | `get_active_plan(tenant_id, app_id)` | consulta |
| **ListMarketingPlans** | `read` | Filtros `app_id`, `estado` desde query de aplicación; `list_plans` | consulta |

**Nota:** operadores de marketing pueden **leer** plan activo; mutaciones requieren `admin`/`config` según dominio R7.

---

## 5. Puertos que utiliza la Application Layer

| Puerto | Origen | Uso en aplicación |
|--------|--------|-------------------|
| `MarketingPlanDomainService` | Dominio (inyectado) | Única vía de mutación/consulta de negocio |
| `AuthorizationPort` | Infra / `rbac` existente | `assert_permission(actor, tenant_id, permission)` |
| `TenantAppContextPort` | Infra / `tenant`, `marketing_app` | Confirmar tenant/app del request; alimentar `TenantAppValidator` del dominio |
| `DomainEventPublisher` | Infra futura | Recibir `DomainEvent[]` post-mutación (audit, webhooks) |
| `Clock` / `IdGenerator` | Infra | Inyectados al construir el domain service (composition root) |

La aplicación **no** implementa `MarketingPlanRepository`; recibe un domain service ya compuesto.

---

## 6. Entradas y salidas (nivel aplicación — sin HTTP)

### Entrada típica (comando)

Conceptual — no JSON ni REST:

```
ApplicationContext:
  tenant_id
  app_id
  actor_id
  actor_role

CreateMarketingPlanInput:
  nombre, objetivo_general, strategy_type, …
  (campos alineados al schema; sin id, sin estado)
```

### Salida típica (mutación)

```
ApplicationResult:
  plan: MarketingPlan          # agregado dominio
  events: DomainEvent[]        # para publisher
```

### Salida error

```
ApplicationError:
  code: str                    # mismo código dominio o wrapper
  source: "domain" | "auth" | "context"
  domain_error?: DomainError
```

La API (Pieza 6) mapeará `ApplicationError` → status HTTP; la aplicación **no** conoce HTTP.

---

## 7. RBAC (R7) — responsabilidad de aplicación

| Operación | Permiso mínimo |
|-----------|----------------|
| Create, Update | `config` o `admin` |
| Activate, Pause, Complete | `admin` |
| Get, List, GetActive | `read` |

Integración prevista: adaptador sobre `accio_engine.rbac.has_permission(role_id, permission, tenant_id)`.

Si falla autorización → `ApplicationError` código `Forbidden` (capa aplicación), **sin** invocar dominio.

---

## 8. Evolución — multi-agregado (futuro, no Pieza 5 V1)

Cuando existan Campaign, Calendar, ContentQueue, Metrics, la Application Layer tendrá casos de uso **compuestos**, por ejemplo:

| Caso de uso futuro | Coordina |
|--------------------|----------|
| `LaunchCampaignUnderPlan` | Plan activo + Campaign (futuro) |
| `ScheduleContentForActivePlan` | Plan + Calendar + Queue (futuro) |

**Pieza 5 V1:** solo casos de uso del agregado `MarketingPlan`. Los compuestos se diseñan cuando existan los agregados; la aplicación seguirá sin reglas de negocio propias.

---

## 9. Composition root (dónde se ensambla)

Sin implementar aún. Conceptualmente:

```
MarketingPlanApplicationService(
  domain_service: MarketingPlanDomainService,
  authorization: AuthorizationPort,
  context: TenantAppContextPort,
  events: DomainEventPublisher,
)
```

El **composition root** (futuro módulo `app.py` o factory de infra) elige:

- `JsonMarketingPlanRepository` vs `InMemoryMarketingPlanRepository`
- adaptador RBAC real
- `FixedClock` / producción

El domain service **no cambia** al cambiar adaptador.

---

## 10. Dependencias permitidas

```
marketing_plan_application/   (futuro paquete)
    → marketing_plan_domain
    → puertos propios (AuthorizationPort, …)
    ✗ marketing_plan_infrastructure (solo vía composition root, no import directo en casos de uso)
    ✗ Flask / FastAPI
    ✗ OpenAI
```

Infraestructura conoce aplicación y dominio; aplicación conoce dominio; dominio conoce solo dominio.

---

## 11. Criterios de aceptación (diseño Pieza 5)

| Criterio | |
|----------|---|
| Casos de uso listados (comandos + consultas) | ✓ |
| RBAC en aplicación, no en dominio | ✓ |
| Sin HTTP / REST / FastAPI | ✓ |
| Sin reglas R1–R9 en aplicación | ✓ |
| Dominio intacto | ✓ |
| Preparado para API (Pieza 6) como cliente de aplicación | ✓ |

---

## 12. Próximo paso

| Pieza | Estado |
|-------|--------|
| Revisión / aprobación diseño Application Layer | ✅ Aprobado |
| **Implementación Application Services** | ✅ Entregado — `marketing_plan_application/` |
| **API Contract** (Pieza 6 — diseño, sin FastAPI) | ⏳ Siguiente |
| REST API / Dashboard / Context Builder / IA | ⏳ Después |

**Implementación:** `Motor_Tecnico/accio_engine/marketing_plan_application/` — 5 comandos + 3 consultas; tests en `tests/test_marketing_plan_application.py`.

---

## Roadmap acordado (Fase B en adelante)

| Pieza | Nombre |
|-------|--------|
| 5 | Application Services ✅ |
| **6** | **API Contract** (diseño) ← **siguiente** |
| 6b | REST API (código) |
| 7 | Dashboard / UI |
| 8 | Context Builder |
| 9 | AI Planner |
| 10 | Campaign Engine |

---

*Pieza 5 — Application Layer · EM+Acción · v1.1 (aprobado + implementado)*
