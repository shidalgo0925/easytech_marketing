# SPRINT 3 — M0 + M1 Corporate Memory

## EM+Acción Marketing OS — implementación

**Estado:** ✅ **Cerrado** (2026-06-26)  
**Arquitectura:** [MARKETING_OS_ARCHITECTURE.md](MARKETING_OS_ARCHITECTURE.md) v1.0

---

## Entregables

| Fase | Entregable | Ubicación | Estado |
|------|------------|-----------|--------|
| M0 | SQLite platform DB + schema | `platform_infrastructure/db.py` | ✅ |
| M0 | `memory_events` + índices | schema en db.py | ✅ |
| M1 | Domain + service | `memory_domain/` | ✅ |
| M1 | SQLite repository | `memory_infrastructure/sqlite_repository.py` | ✅ |
| M1 | MarketingPlan → Memory bridge | `memory_infrastructure/marketing_plan_bridge.py` | ✅ |
| M1 | API query | `GET /api/v1/tenants/{id}/memory/events` | ✅ |
| M1 | Import audit script | `scripts/migrate_audit_to_memory.py` | ✅ |
| M1 | Tests | `tests/test_platform_memory.py` | ✅ |

---

## Configuración

```env
ACCIO_PLATFORM_DB=/opt/easytech_marketing/Marketing/platform/marketing_os.db
ACCIO_MEMORY_STORE=sql    # off | sql | dual
```

- **sql** (default): eventos de MarketingPlan → `memory_events`
- **off**: sin escritura Memory (comportamiento previo)
- **dual**: reservado — audit jsonl + sql (assistant pendiente)

---

## API

```
GET /api/v1/tenants/{tenant_id}/memory/events
GET /api/v1/tenants/{tenant_id}/memory/events/{event_id}
```

Query params: `brand_id`, `event_type`, `entity_type`, `entity_id`, `since`, `until`, `limit`, `offset`

---

## Siguiente: M2 Company Brain

Ver [MARKETING_OS_MIGRATION_PLAN.md](MARKETING_OS_MIGRATION_PLAN.md)
