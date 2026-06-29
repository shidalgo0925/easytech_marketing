# M4 — Publications (Sprint 6)

**Estado:** ✅ Cerrado (2026-06-26)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v4 `publications` | `platform_infrastructure/schema_v4_publications.py` |
| Domain slice | `publication_{domain,application,infrastructure,api}/` |
| Facade | `executor.load/save_content_queue` → SQL cuando `ACCIO_PUBLICATION_STORE=sql\|dual` |
| API | `GET /api/v1/tenants/{id}/apps/{app_id}/publications[/{id}]` |
| Migración | `scripts/migrate_content_queue_to_publications.py` |
| Tests | `tests/test_publications.py` |

---

## Config

```env
ACCIO_PUBLICATION_STORE=dual   # json | sql | dual
```

Dual-write: nuevas escrituras van a SQLite y JSON. Dual-read: SQL primero si hay filas.

---

## Siguiente: M5 Products (`products.json`)
