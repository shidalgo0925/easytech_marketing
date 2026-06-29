# Pieza 3 — Servicio de Dominio: MarketingPlan

**Versión:** 1.1 (diseño aprobado)  
**Estado:** ✅ Aprobado — **GO implementación**  
**Fuentes:** [`MARKETING_PLAN_DOMAIN_v1.1.md`](MARKETING_PLAN_DOMAIN_v1.1.md) · [`MARKETING_PLAN_DOMAIN_SCHEMA_v1.md`](MARKETING_PLAN_DOMAIN_SCHEMA_v1.md)

> **Contrato.** Este documento define qué hace y qué no hace el Servicio de Dominio. Es el único lugar autorizado para ejecutar reglas R1–R9, transiciones de estado, validaciones e invariantes del agregado `MarketingPlan`.
>
> **Regla de equipo:** ningún controlador, endpoint, cron, asistente IA, dashboard o comando podrá modificar un `MarketingPlan` sin pasar por el Servicio de Dominio.

---

## 1. ¿Qué hace?

El **MarketingPlanDomainService** (nombre provisional) es la **única capa autorizada** para:

1. **Crear** un `MarketingPlan` en estado `borrador`.
2. **Actualizar** atributos de un plan en estados editables (`borrador`, `pausado`).
3. **Transicionar** el ciclo de vida: `borrador`→`activo`, `activo`→`pausado`/`finalizado`, `pausado`→`activo`/`finalizado`.
4. **Resolver R2** al activar: detectar plan `activo` existente y exigir resolución (`finalizar` o `pausar` el anterior) antes de activar el nuevo.
5. **Validar** el agregado contra el schema (§5 del schema): campos, enums, `DateRange`, `Budget`, contenido declarativo (R3 heurística).
6. **Garantizar R1**: como máximo un plan `activo` por `(tenant_id, app_id)`.
7. **Emitir eventos de dominio** (`PlanCreated`, `PlanActivated`, `PlanPaused`, `PlanCompleted`) como resultado de operaciones exitosas — contrato §4 del schema.
8. **Consultar** (vía puerto de repositorio): plan por id, plan activo de una app, listado de planes por app/tenant con filtros de estado.

No persiste por sí mismo. **Orquesta** reglas de negocio y delega lectura/escritura a un **puerto de repositorio** (implementación en fase posterior).

---

## 2. ¿Qué no hace?

| Responsabilidad | Capa correcta |
|-----------------|---------------|
| Persistir en JSON, SQL o archivos | Repositorio / infraestructura |
| Exponer HTTP REST | API / aplicación |
| Renderizar UI o formularios | Presentación |
| Llamar OpenAI, Accio u otro LLM | IA / Context Builder |
| Publicar en LinkedIn, Meta, etc. | Conectores / publishers |
| Crear publicaciones, campañas, calendario | Piezas operativas futuras |
| Modificar Knowledge Base | Servicio KB existente |
| Decidir permisos de usuario | RBAC / auth (solo **rechaza** si la capa aplicación no autorizó) |
| Cross-sell o override de sesión IA | Context Builder / capa IA (R4, R5) |
| Enviar emails, webhooks, cron | Automatizaciones / infra |

El servicio **no conoce** consumidores del Plan (Principio 4 del dominio).

---

## 3. ¿Qué recibe?

### 3.1 Dependencias (puertos — no implementados en Pieza 3 diseño)

| Puerto | Responsabilidad |
|--------|-----------------|
| `MarketingPlanRepository` | Leer/guardar agregado `MarketingPlan`; consultar activo por `(tenant_id, app_id)` |
| `TenantAppValidator` (opcional) | Confirmar que `tenant_id` y `app_id` existen (puede ser adaptador a `marketing_app` existente) |
| `Clock` (opcional) | `now()` UTC para auditoría |

### 3.2 Entradas por operación (conceptual)

| Operación | Entrada principal |
|-----------|-------------------|
| `createPlan` | `CreatePlanCommand`: datos del schema sin `id`, `estado=borrador`, `created_by` |
| `updatePlan` | `UpdatePlanCommand`: `plan_id`, campos mutables, `updated_by` |
| `activatePlan` | `ActivatePlanCommand`: `plan_id`, `activated_by`, `ConflictResolution?` (`finalize_previous` \| `pause_previous`) |
| `pausePlan` | `PausePlanCommand`: `plan_id`, `paused_by` |
| `completePlan` | `CompletePlanCommand`: `plan_id`, `completed_by` |
| `getPlan` | `plan_id`, `tenant_id` |
| `getActivePlan` | `tenant_id`, `app_id` |
| `listPlans` | `tenant_id`, `app_id?`, `estado?` |

**Nota:** comandos llevan identidad del actor (`UserId`) para auditoría y eventos; el servicio no autentica — la capa aplicación verifica RBAC (R7) antes de invocar.

---

## 4. ¿Qué devuelve?

| Resultado | Contenido |
|-----------|-----------|
| **Éxito mutación** | `MarketingPlan` actualizado + lista de `DomainEvent` emitidos |
| **Éxito consulta** | `MarketingPlan` o colección |
| **Error de dominio** | `DomainError` tipado (códigos §5.2 schema): ej. `ACTIVE_PLAN_CONFLICT`, `INVALID_STATUS_TRANSITION`, `ACTIVE_PLAN_RESOLUTION_REQUIRED` |
| **Sin side-effects operativos** | Nunca devuelve órdenes de publicación, jobs, ni llamadas a conectores (R8) |

Los eventos se devuelven al **publicador de eventos** (infra futura) o al log de auditoría; el servicio no los persiste obligatoriamente en Pieza 3 inicial.

---

## 5. ¿Qué reglas ejecuta?

| Regla | Dónde en el servicio |
|-------|----------------------|
| **R1** | Antes de `activatePlan`: repositorio confirma ≤1 activo; tras activación, invariante garantizada |
| **R2** | `activatePlan`: si hay activo distinto → error `ACTIVE_PLAN_RESOLUTION_REQUIRED` hasta recibir resolución; luego pausar/finalizar anterior y activar nuevo |
| **R3** | Validación declarativa en create/update (heurística + no rechazo único de imperativos en V1) |
| **R4** | **No ejecuta** — Context Builder / IA |
| **R5** | **No ejecuta** — sesión IA |
| **R6** | Validación `DateRange` en create/update |
| **R7** | **No ejecuta** — capa aplicación verifica permisos antes de invocar |
| **R8** | Transiciones no invocan publishers, cola ni conectores |
| **R9** | Rechaza payloads con campos prohibidos (IA, ejecución, etc.) |

**Transiciones de estado** (schema §1.6): solo las permitidas; `finalizado` es terminal.

**Validaciones de campo** (schema §5.1): todas antes de persistir.

---

## 6. Principios del contrato (endurecimiento v1.1)

### Principio 1 — Determinismo

Para los **mismos datos de entrada**, el Servicio de Dominio siempre debe producir el **mismo resultado**.

No puede depender de:

- hora del servidor (salvo puerto `Clock`)
- IA, red, APIs externas, archivos, variables globales

Todo lo no determinista entra por **puertos** (`Clock`, `IdGenerator`, `Repository`, etc.).

### Principio 2 — Idempotencia

Las operaciones críticas de transición deben ser **seguras ante reintentos**:

| Operación | Si ya está en estado destino |
|-----------|------------------------------|
| `activatePlan` | Devuelve el plan sin error; sin eventos duplicados |
| `pausePlan` | Idem |
| `completePlan` | Idem |

No rompe invariantes ni emite eventos redundantes.

### Principio 3 — Errores tipados

El dominio **nunca** devuelve `"Error"` genérico. Catálogo mínimo:

| Código | Cuándo |
|--------|--------|
| `PlanNotFound` | Plan inexistente o fuera de tenant |
| `PlanAlreadyActive` | Transición inválida hacia activo (mismo plan ya activo se trata como idempotencia, no error) |
| `PlanCompleted` | Mutación sobre plan `finalizado` |
| `StrategyTypeInvalid` | Enum strategy inválido |
| `InvalidDateRange` | R6 — fin < inicio |
| `ConflictActivePlan` | R2 — activación con otro activo sin resolución |
| `InvalidStatusTransition` | Transición no permitida |
| `BudgetInvalid` | amount < 0 o moneda inválida |
| *(+ códigos §5.1 schema)* | Validaciones de campo |

HTTP, CLI, UI y logs **traducen** estos códigos; el dominio no habla HTTP.

**Explícitamente fuera de alcance V1:** CQRS, Event Sourcing, Saga, Mediator, Bus, microservicios.

---

## 7. ¿Qué nunca puede hacer?

1. **Activar dos planes** en la misma app sin resolver R2.
2. **Reactivar** un plan `finalizado`.
3. **Transicionar** por rutas no definidas en el schema.
4. **Publicar, encolar o conectar** redes como efecto de cambiar estado del Plan.
5. **Modificar** `tenant_id` o `app_id` de un plan existente (identidad fija del agregado).
6. **Incluir** campos de proveedor IA, prompts o consumidores en el agregado.
7. **Saltarse** validaciones del schema por conveniencia de API o UI.
8. **Decidir** cross-sell o override de chat (R4/R5).
9. **Sustituir** al repositorio escribiendo directamente en filesystem o SQL desde el servicio.
10. **Alterar** reglas del dominio — si hace falta, **detener** y revisar `MARKETING_PLAN_DOMAIN_v1.1.md`.

---

## 8. Flujo resumido (activate con conflicto R2)

```
activatePlan(command)
  → cargar plan (debe estar borrador o pausado)
  → validar transición permitida → activo
  → buscar activo en (tenant_id, app_id)
  → si existe otro activo:
       si command.resolution es null → ACTIVE_PLAN_RESOLUTION_REQUIRED
       si finalize_previous → completePlan(anterior)
       si pause_previous → pausePlan(anterior)
  → aplicar estado activo, activated_at = now
  → persistir vía repositorio
  → emitir PlanActivated (+ PlanCompleted/PlanPaused del anterior si aplica)
  → retornar plan + eventos
```

---

## 9. Relación con otras capas (futuro)

```
UI / API
   ↓ (comandos, tras RBAC)
MarketingPlanDomainService  ← único ejecutor R1–R9
   ↓
MarketingPlanRepository (puerto)
   ↓
Infraestructura (JSON, SQL, …)   ← Fuera del dominio §10 schema
```

IA y Context Builder **leen** el plan activo vía consulta/repositorio; **no** mutan el agregado excepto invocando el servicio a través de la capa aplicación con permisos.

---

## 10. Criterios de aceptación (diseño Pieza 3)

| Criterio | |
|----------|---|
| Sin código en este entregable | ✓ |
| Solo `MarketingPlan` como Aggregate Root | ✓ |
| R1, R2, transiciones, validaciones, eventos centralizados aquí | ✓ |
| API/UI/persistencia/IA explícitamente excluidas | ✓ |
| Alineado 100 % con dominio y schema | ✓ |

---

## 11. Próximo paso

| Acción | Estado |
|--------|--------|
| Revisión / aprobación de este diseño | ✅ Aprobado |
| **Implementación** del servicio (código) | ✅ Entregado — repositorio en memoria + tests |
| Persistencia (repositorio real) | ⏳ Después |
| API / UI / IA | ⏳ Después |

**Disciplina de implementación:** si aparece necesidad de romper R1–R9 o modificar el dominio congelado → **detener** y volver a revisión arquitectónica. Si el código puede adaptarse al dominio, esa es siempre la opción preferente.

---

*Pieza 3 — Contrato del Servicio de Dominio · EM+Acción · v1.1 (aprobado)*
