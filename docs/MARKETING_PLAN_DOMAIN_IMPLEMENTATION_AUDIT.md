# Pieza 3.5 — Auditoría de Conformidad del Servicio de Dominio

**Acción:** 3.5  
**Tipo:** Auditoría técnica (sin modificación de código)  
**Fecha:** 2026-06-27  
**Alcance:** `Motor_Tecnico/accio_engine/marketing_plan_domain/` + `tests/test_marketing_plan_domain_service.py`

**Referencias:**

- [`MARKETING_PLAN_DOMAIN_v1.1.md`](MARKETING_PLAN_DOMAIN_v1.1.md)
- [`MARKETING_PLAN_DOMAIN_SCHEMA_v1.md`](MARKETING_PLAN_DOMAIN_SCHEMA_v1.md)
- [`MARKETING_PLAN_DOMAIN_SERVICE.md`](MARKETING_PLAN_DOMAIN_SERVICE.md)

**Veredicto global:** ⚠️ **Conformidad sustancial con gaps menores.** No bloqueantes de dominio; **1 hallazgo de dependencias** y **brechas de tests/nomenclatura** conviene pulir antes o en paralelo con Pieza 4 (Infrastructure Adapters).

---

## 1. Cobertura R1–R9

| Regla | Estado | Evidencia |
|-------|--------|-----------|
| **R1** — ≤1 plan `activo` por `(tenant_id, app_id)` | **Implementada** (vía servicio) | `activate_plan` consulta `repository.find_active` antes de activar; sin resolución lanza `ConflictActivePlan` (`service.py` L160–172). Test: `test_r1_single_active_plan`. Tras R2 resuelto, solo queda un activo (`test_r2_*`). **Nota:** la invariante no se enforce en el puerto repositorio; un adaptador corrupto podría persistir dos activos — responsabilidad futura del adaptador. |
| **R2** — Activación con conflicto exige resolución | **Implementada** | Sin `resolution` → `DomainErrorCode.CONFLICT_ACTIVE_PLAN` (L164–172). Con `finalize_previous` / `pause_previous` → `_complete_plan_internal` / `_pause_plan_internal` + `PlanActivated` con `resolution` (`L173–205`). Tests: `test_r2_activate_with_finalize_previous`, `test_r2_activate_with_pause_previous`. |
| **R3** — Plan declarativo (heurística) | **Parcial** | `validators.validate_declarative_content`: ≥2 keywords operativos → `PlanNotDeclarative` (`validators.py` L145–153). Cumple contrato V1 («no rechazo único de imperativos»). **Revisión humana** (schema §5.3) fuera del servicio — correcto. **Sin test** que ejercite `PlanNotDeclarative`. |
| **R4** — Cross-sell / enfoque principal | **No implementada** (correcto) | Ausente en servicio. Contrato §5: Context Builder / IA. |
| **R5** — Override sesión IA | **No implementada** (correcto) | Ausente en servicio. Contrato §5: sesión IA. |
| **R6** — `periodo.fin` ≥ `periodo.inicio` | **Implementada** | `validate_date_range` (`validators.py` L57–63); invocada en `validate_plan_fields`. Test: `test_invalid_date_range_raises`. |
| **R7** — Permisos RBAC | **No implementada** (correcto) | Sin auth en servicio. Comandos llevan actor; capa aplicación debe verificar antes de invocar. |
| **R8** — Sin side-effects operativos | **Implementada** | Transiciones solo mutan agregado + eventos; sin imports ni llamadas a publishers, cola, conectores, IA. |
| **R9** — Campos prohibidos | **Parcial** | `reject_forbidden_fields` + `FORBIDDEN_PLAN_FIELDS` (`model.py` L72–91). En `update_plan` vía `command.extra_fields` (`service.py` L102). En `create_plan` inspecciona `command.__dict__`, pero `CreatePlanCommand` no expone vía `extra_fields` — campos prohibidos arbitrarios en create **no tienen camino de entrada** salvo extender el dataclass. **Sin test** R9. |

---

## 2. Métodos públicos

Convención: contrato usa camelCase; implementación Python usa snake_case. Semántica equivalente.

| Método | Contrato | Implementado | Diferencias |
|--------|----------|--------------|-------------|
| `createPlan` | Crear plan en `borrador`; validar schema; emitir `PlanCreated`; delegar persistencia | ✅ `create_plan` | Nombre snake_case. Puerto `IdGenerator` usado pero no listado en contrato §3.1 (sí en Principio 1). |
| `updatePlan` | Editar solo `borrador`/`pausado`; validar; sin eventos | ✅ `update_plan` | `updated_by` en comando **no se persiste** en agregado — alineado con dominio v1.1 (no existe `updated_by` en entidad; actor solo para trazabilidad futura). |
| `activatePlan` | Transición a `activo`; R1/R2; idempotente si ya activo; `PlanActivated` | ✅ `activate_plan` | Código error R2: contrato/schema dicen `ACTIVE_PLAN_RESOLUTION_REQUIRED`; código usa `ConflictActivePlan`. |
| `pausePlan` | `activo`→`pausado`; idempotente; `PlanPaused` | ✅ `pause_plan` | — |
| `completePlan` | →`finalizado`; idempotente; `PlanCompleted` | ✅ `complete_plan` | — |
| `getPlan` | Plan por id + tenant | ✅ `get_plan` | Lanza `PlanNotFound` si id inexistente o tenant distinto. |
| `getActivePlan` | Plan activo por `(tenant_id, app_id)` | ✅ `get_active_plan` | Retorna `None` si no hay activo (contrato: consulta). |
| `listPlans` | Listado con filtros opcionales | ✅ `list_plans` | Filtros `app_id`, `estado`. Test: `test_list_plans_filter_by_estado`. |

**Tipos de retorno:** mutaciones devuelven `MutationResult(plan, events)` — alineado con contrato §4.

---

## 3. Eventos

Schema §4 define exactamente **4 eventos**. Implementación en `events.py`; emisión en `service.py`.

| Evento | Payload schema | Emitido | Evidencia |
|--------|----------------|---------|-----------|
| `PlanCreated` | §4.1 | ✅ | `create_plan` L90–98. Test: `test_create_plan_emits_plan_created`. |
| `PlanActivated` | §4.2 | ✅ | `activate_plan` L194–205. Tests R2 + idempotencia. |
| `PlanPaused` | §4.3 | ✅ | `_pause_plan_internal` L249–256. Tests pause + R2 pause_previous. |
| `PlanCompleted` | §4.4 | ✅ | `_complete_plan_internal` L266–273. Tests complete + R2 finalize. |

**Nunca emitidos:** ninguno de los cuatro se emite fuera de su disparador. `update_plan` devuelve `events=[]` — correcto.

**Faltantes:** ninguno respecto al schema v1.

**Detalle menor:** en activación sin conflicto, `PlanActivated.previous_active_plan_id` es `null` y `resolution` es `null` — conforme §4.2.

---

## 4. Errores — Contrato vs Implementación vs Tests

### 4.1 Catálogo mínimo del contrato (§6 Principio 3)

| Código contrato | En `DomainErrorCode` | Usado en código | Cubierto por test |
|-----------------|----------------------|-----------------|-------------------|
| `PlanNotFound` | ✅ | ✅ `service._require_plan` | ✅ `test_plan_not_found_wrong_tenant` |
| `PlanAlreadyActive` | ✅ | ❌ nunca lanzado | ❌ (idempotencia en su lugar — conforme contrato) |
| `PlanCompleted` | ✅ | ✅ update/activate/pause sobre finalizado | ⚠️ parcial (activate/pause sí; update finalizado no testeado) |
| `StrategyTypeInvalid` | ✅ | ✅ | ✅ `test_invalid_strategy_raises` |
| `InvalidDateRange` | ✅ | ✅ | ✅ `test_invalid_date_range_raises` |
| `ConflictActivePlan` | ✅ | ✅ R2 sin resolución | ✅ `test_r1_single_active_plan` |
| `InvalidStatusTransition` | ✅ | ✅ | ✅ `test_invalid_transition_from_borrador_to_pausado` |
| `BudgetInvalid` | ✅ | ✅ `validate_budget` | ❌ sin test |

### 4.2 Schema §5.1 / §5.2 — códigos adicionales

| Código schema | Implementación | Test |
|---------------|----------------|------|
| `ACTIVE_PLAN_RESOLUTION_REQUIRED` | **Alias ausente** — se usa `ConflictActivePlan` | ✅ (mismo flujo) |
| `ACTIVE_PLAN_CONFLICT` | Enum definido; **nunca lanzado** | ❌ |
| `PLAN_ALREADY_FINALIZED` | Se usa `PlanCompleted` | ⚠️ |
| `PLAN_NOT_DECLARATIVE` | ✅ implementado | ❌ |
| `FORBIDDEN_FIELD` | ✅ implementado | ❌ |
| `TENANT_REQUIRED` / `APP_REQUIRED` | ✅ | ❌ |
| `TENANT_NOT_FOUND` / `APP_NOT_FOUND` | ✅ (`AcceptAllTenantAppValidator` default no los dispara) | ❌ |
| `NAME_INVALID`, `OBJECTIVE_INVALID`, … | ✅ en `validate_plan_fields` | ❌ |
| `CURRENCY_INVALID` (enum) | **Definido pero no usado** — moneda inválida → `BudgetInvalid` | ❌ |
| `START_DATE_REQUIRED` / `END_DATE_INVALID` | No códigos separados — fechas inválidas vía `InvalidDateRange` o excepción parse | ❌ |

### 4.3 Conclusión errores

- **Implementación:** catálogo **más amplio** que tests; **2 códigos muertos** (`PlanAlreadyActive`, `ActivePlanConflict`); **1 sin usar** (`CurrencyInvalid`).
- **Contrato ↔ código:** divergencia de **nomenclatura** R2 (`ACTIVE_PLAN_RESOLUTION_REQUIRED` vs `ConflictActivePlan`) — semántica correcta.
- **Contrato ↔ tests:** **14 tests OK**; cubren camino feliz + R1/R2 + idempotencia + 4 códigos de error. **~15 códigos sin test directo.**

**No se devuelven strings genéricos `"Error"`** — conforme Principio 3.

---

## 5. Determinismo

| Fuente no determinista | ¿Entra por puerto? | Evidencia |
|------------------------|-------------------|-----------|
| Hora | ✅ `Clock` | `service.py` usa `self._clock.now()`; sin `datetime.now()`. |
| IDs plan/evento | ✅ `IdGenerator` | `ports.py` L14–17; `FixedIdGenerator` en tests. |
| Persistencia | ✅ `MarketingPlanRepository` | Inyectado; sin FS/SQL/HTTP en dominio. |
| IA / red / APIs | ✅ Ausentes | Sin imports externos operativos. |
| Variables globales / env | ✅ Ausentes | — |

Test explícito: `test_determinism_same_inputs_same_output`.

**Observación:** `FixedIdGenerator` agota listas predefinidas y luego genera `mpl_NNNN` / `evt_NNNN` de forma determinista — aceptable.

---

## 6. Idempotencia

| Operación | Comportamiento si ya en estado destino | Verificado en código | Test |
|-----------|--------------------------------------|----------------------|------|
| `activate_plan` | Retorna plan; `events=[]` | L154–155 | ✅ `test_idempotent_activate` |
| `pause_plan` | Retorna plan; `events=[]` | L210–211 | ✅ `test_idempotent_pause_and_complete` |
| `complete_plan` | Retorna plan; `events=[]` | L222–223 | ✅ `test_idempotent_pause_and_complete` |
| `create_plan` | No idempotente (nuevo plan cada vez) | — | N/A (contrato no lo exige) |
| `update_plan` | No idempotente (muta `updated_at`) | — | N/A |

**Casos adicionales verificados en código (sin test):**

- `activate_plan` sobre `finalizado` → **error** `PlanCompleted` (no idempotente — correcto).
- `pause_plan` sobre `finalizado` → **error** `PlanCompleted`.
- `complete_plan` desde `borrador` → **error** `InvalidStatusTransition` vía `_ensure_transition`.

---

## 7. Dependencias

Regla auditada: el dominio solo debe depender de **model, VOs, enums, ports, errors, events**.

### 7.1 Grafo interno `marketing_plan_domain/`

| Módulo | Importa |
|--------|---------|
| `enums.py` | stdlib |
| `errors.py` | stdlib |
| `model.py` | `enums` |
| `events.py` | `enums` |
| `ports.py` | `enums`, `model` |
| `validators.py` | `enums`, `errors`, `model`, stdlib `re` |
| `commands.py` | `enums`, `model` |
| `service.py` | `commands`, `enums`, `errors`, `events`, **`memory`**, `model`, `ports`, `validators` |
| `memory.py` | `enums`, `model`, `events` — **adaptador infra dentro del paquete dominio** |

### 7.2 Hallazgos

| # | Severidad | Hallazgo |
|---|-----------|----------|
| 1 | **⚠️ Bloqueante arquitectónico menor** | `service.py` L22: `from .memory import AcceptAllTenantAppValidator` — el **servicio de dominio importa un módulo de infraestructura** (stub en memoria). Debería vivir en `validators.py`, `ports.py` o módulo `defaults.py` del dominio, no en `memory.py`. |
| 2 | Informativo | `memory.py` (`InMemoryMarketingPlanRepository`, `FixedClock`, `FixedIdGenerator`) convive en el mismo paquete que el dominio — aceptable **temporalmente** para Pieza 3; Pieza 4 debería mover stubs a `marketing_plan_infrastructure/` o similar. |
| 3 | Informativo | `commands.py` y `validators.py` no están en la lista cerrada del auditor — son **parte legítima del servicio de dominio** (DTOs + reglas). No violan espíritu del dominio. |
| 4 | Menor | `memory.py` importa `DomainEvent` sin uso; define `MutationResult` duplicado (también en `service.py`) — código muerto. |
| 5 | Menor | `commands.py` importa `Budget`, `DateRange` sin uso. |

**Sin dependencias** a Flask, FastAPI, SQLite, OpenAI, accio_engine operativo, filesystem, HTTP.

---

## 8. Complejidad (solo señalamiento)

| Método / función | Líneas aprox. | Observación |
|------------------|---------------|-------------|
| `activate_plan` | ~60 | Mayor complejidad del servicio (R2 + eventos múltiples). Aún legible; no requiere refactor urgente. |
| `validate_plan_fields` | ~55 | Concentración de validaciones §5.1 — coherente con schema. |
| `update_plan` | ~43 | Secuencia repetitiva de `if command.campo is not None` — verboso pero claro. |
| `create_plan` | ~45 | Similar a update en estructura. |

Ningún método supera umbral que sugiera decomposición obligatoria antes de Pieza 4.

---

## 9. Deuda técnica (no rompe contrato; conviene pulir)

| # | Item | Impacto |
|---|------|---------|
| 1 | Mover `AcceptAllTenantAppValidator` fuera de `memory.py` | Limpia dependencia dominio→infra |
| 2 | Reubicar `memory.py` en capa **Infrastructure Adapters** (Pieza 4) | Separación física paquetes |
| 3 | Alinear nomenclatura errores R2: alias `ACTIVE_PLAN_RESOLUTION_REQUIRED` o documentar mapping | Contrato/schema/código |
| 4 | Eliminar códigos muertos (`ActivePlanConflict`, `CurrencyInvalid`) o usarlos | Claridad catálogo |
| 5 | Ampliar tests: R3, R9, `BudgetInvalid`, `complete` desde `borrador`, `update` sobre `finalizado`, `TenantNotFound` | Confianza pre-adaptadores |
| 6 | `CreatePlanCommand.extra_fields` simétrico a `UpdatePlanCommand` para R9 en create | Cobertura R9 completa |
| 7 | Adaptador repositorio futuro: constraint único `(tenant_id, app_id, activo)` | Defensa en profundidad R1 |
| 8 | Eliminar `MutationResult` duplicado en `memory.py` | Limpieza |

---

## 10. Checklist final

| Item | Estado | Notas |
|------|--------|-------|
| Dominio respetado | ⚠️ **Parcial** | Reglas core OK; R9 create incompleto; sin alterar dominio congelado. |
| Schema respetado | ⚠️ **Parcial** | Modelo, enums, transiciones, eventos OK; nomenclatura errores §5.2 difiere. |
| Contrato respetado | ⚠️ **Parcial** | 8/8 métodos; principios determinismo/idempotencia OK; import `memory` rompe regla §7. |
| Eventos correctos | ✅ **OK** | 4/4 definidos y emitidos correctamente. |
| Errores correctos | ⚠️ **Parcial** | Tipados sí; catálogo > tests; alias schema pendiente. |
| R1–R9 completos | ⚠️ **Parcial** | R1,R2,R3,R6,R8,R9 parcial; R4,R5,R7 N/A correcto. |
| Determinismo | ✅ **OK** | Puertos Clock, IdGenerator, Repository. |
| Idempotencia | ✅ **OK** | activate / pause / complete verificados. |
| Dependencias limpias | ❌ **No** | `service` → `memory` (1 violación). |
| Listo para persistencia | ⚠️ **Condicional** | GO Pieza 4 **Infrastructure Adapters** tras pulir item §9.1 (y recomendable §9.3–9.5). |

---

## Decisión recomendada

| Acción | Recomendación |
|--------|---------------|
| **Pieza 4 — Infrastructure Adapters** | ⚠️ **GO condicional** — no requiere reescribir lógica de negocio; sí conviene **1 fix de dependencia** (`AcceptAllTenantAppValidator`) y **tests adicionales** antes o como primer commit de Pieza 4. |
| **Bloqueo duro** | Solo la dependencia `service.py` → `memory.py` si se aplica la regla §7 estrictamente. |
| **No bloquea** | Nomenclatura errores, tests faltantes, códigos muertos, ubicación física de `memory.py`. |

---

## Qué falta pulir (resumen ejecutivo)

1. **Dependencia:** sacar `AcceptAllTenantAppValidator` de `memory.py` para que el servicio no importe infraestructura.
2. **Tests:** R3, R9, presupuesto inválido, transiciones negativas adicionales, tenant/app inexistente.
3. **Errores:** unificar alias `ConflictActivePlan` ↔ `ACTIVE_PLAN_RESOLUTION_REQUIRED`; podar enums no usados.
4. **R9 create:** patrón `extra_fields` en `CreatePlanCommand` (simetría con update).
5. **Pieza 4:** mover stubs (`InMemoryMarketingPlanRepository`, `FixedClock`, `FixedIdGenerator`) a paquete **Infrastructure Adapters**; implementar primer adaptador de persistencia contra el mismo puerto `MarketingPlanRepository`.

La lógica de negocio **respeta el dominio** en los caminos críticos (R1, R2, ciclo de vida, eventos, determinismo, idempotencia). Los gaps son de **higiene arquitectónica y cobertura de tests**, no de reinterpretación del modelo.

---

*Pieza 3.5 — Auditoría de Conformidad · EM+Acción · Sin modificación de código*
