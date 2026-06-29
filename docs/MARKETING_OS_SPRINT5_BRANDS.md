# M3 — Brands (Sprint 5)

**Estado:** ✅ Cerrado (2026-06-29)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v3 `brands` | `platform_infrastructure/schema_v3_brands.py` |
| Domain slice | `brand_{domain,application,infrastructure,api}/` |
| Facade | `marketing_app.get_app` / `list_apps` → SQL cuando `ACCIO_BRAND_STORE=sql` |
| API | `GET /api/v1/tenants/{id}/brands[/{brand_id}]` |
| Migración | `scripts/migrate_registry_to_brands.py` |
| Tests | `tests/test_brands.py` |

---

## Config

```env
ACCIO_BRAND_STORE=dual   # json | sql | dual
```

---

## Siguiente: M4 Publications (`content_queue.json`)
