# M9 — Leads (Sprint 11)

**Estado:** ✅ Cerrado (2026-06-26)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v9 `leads` | `platform_infrastructure/schema_v9_leads.py` |
| Domain slice | `lead_{domain,application,infrastructure,api}/` |
| Facade | `leads_store.load/save/record/list` → SQL cuando `ACCIO_LEAD_STORE=sql\|dual` |
| API | `GET /api/v1/tenants/{id}/leads[/{lead_id}]` |
| Migración | `scripts/migrate_leads_to_sql.py` |
| Tests | `tests/test_leads.py` |

---

## Config

```env
ACCIO_LEAD_STORE=dual   # json | sql | dual
```

---

## Siguiente: M10 Decision Engine — ver [MARKETING_OS_SPRINT12_DECISION_ENGINE.md](MARKETING_OS_SPRINT12_DECISION_ENGINE.md)
