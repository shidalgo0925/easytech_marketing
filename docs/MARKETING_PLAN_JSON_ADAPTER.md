# Pieza 4.1 — JSON Repository Adapter

**Estado:** Implementado  
**Puerto:** `MarketingPlanRepository` (`marketing_plan_domain/ports.py`)

> **Regla permanente:** toda clase fuera de `marketing_plan_domain/` **prohibido** implementar reglas de negocio. Solo transformar, serializar, persistir, mapear o transportar.

---

## Responsabilidad

Traducir `MarketingPlan` ↔ JSON en filesystem. Implementa exactamente el puerto:

- `save`
- `get_by_id`
- `find_active`
- `list_plans`

No hay `delete` en el puerto — no implementado.

---

## Ubicación en disco

Raíz configurable (en producción: árbol de tenants EM+Acción).

```
{root}/{tenant_id}/apps/{app_id}/marketing_plans/{plan_id}.json
```

Ejemplo operativo futuro:

```
Marketing/tenants/easytech/apps/en1/marketing_plans/mpl_001.json
```

En tests se usa un directorio temporal.

### Regla — layout físico exclusivo del adaptador

El layout `{tenant}/apps/{app}/marketing_plans/` es una **decisión de este adaptador JSON**, no del dominio.

- El dominio y el Servicio de Dominio **nunca** asumen carpetas, JSON, `apps/`, ni rutas de disco.
- Un adaptador PostgreSQL, SQLite u otro backend puede usar tablas, blobs o paths distintos **sin cambiar** dominio, schema ni servicio.
- Solo el adaptador conoce dónde y cómo persiste; el puerto habla únicamente en términos de `MarketingPlan`.

---

## Formato JSON

Un archivo por plan. Metadato de persistencia + campos del agregado:

```json
{
  "persistence_schema_version": 1,
  "id": "mpl_001",
  "tenant_id": "easytech",
  "app_id": "en1",
  "nombre": "...",
  "objetivo_general": "...",
  "strategy_type": "lead_generation",
  "north_star_metric": "...",
  "success_criteria": ["100 leads"],
  "publico_objetivo": ["Gerentes PYME"],
  "marketing_brief": "...",
  "periodo": { "inicio": "2026-07-01", "fin": "2026-09-30" },
  "budget": { "amount": "5000", "currency": "USD" },
  "estado": "borrador",
  "prioridad": "alta",
  "observaciones": "",
  "created_at": "2026-06-26T12:00:00+00:00",
  "updated_at": "2026-06-26T12:00:00+00:00",
  "created_by": "admin@easytech",
  "activated_at": null
}
```

- `amount` como string decimal (precisión).
- Fechas ISO 8601; datetimes con offset cuando aplica.
- `success_criteria` / `publico_objetivo`: string o lista (schema V1).

---

## Módulos

| Archivo | Rol |
|---------|-----|
| `mapper.py` | `MarketingPlan` ↔ `dict` |
| `serializer.py` | `dict` ↔ archivo JSON (write atómico `.tmp` → rename) |
| `json_repository.py` | Orquesta mapper + serializer; cumple puerto |

**Separación:** persistencia (`serializer`) ≠ mapeo (`mapper`) ≠ acceso (`json_repository`).

---

## Limitaciones (V1)

- Sin cache, índices, locking, async ni pools.
- `get_by_id` localiza por búsqueda bajo `{root}/**/marketing_plans/{id}.json` (sin índice global).
- Sin migraciones automáticas entre versiones de schema de persistencia.
- No valida R1–R9; no impide dos activos en datos corruptos — eso es responsabilidad del **Servicio de Dominio**.
- Sin delete.

---

## Dependencias

```
JsonMarketingPlanRepository
    → mapper, serializer
    → marketing_plan_domain (model, enums)
```

El dominio **no importa** este adaptador.

---

## Tests

- `tests/test_marketing_plan_repository_contract.py` — mismos escenarios contra Memory y JSON.
- `MarketingPlanDomainServiceJsonTests` — mismos 22 tests del servicio con JSON repository.

---

*Pieza 4.1 · EM+Acción · Infrastructure Adapters*
