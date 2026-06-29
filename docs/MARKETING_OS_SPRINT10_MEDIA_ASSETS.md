# M8 — MediaAssets (Sprint 10)

**Estado:** ✅ Cerrado (2026-06-26)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v8 `media_assets` | `platform_infrastructure/schema_v8_media_assets.py` |
| Domain slice | `media_asset_{domain,application,infrastructure,api}/` |
| Facade | `dashboard_data._load_manifest` → SQL cuando `ACCIO_ASSET_STORE=sql\|dual` |
| API | `GET /api/v1/tenants/{id}/assets[/{asset_id}]` |
| Migración | `scripts/migrate_flyers_to_media_assets.py` |
| Tests | `tests/test_media_assets.py` |

PNG en disco: `Marketing/flyers/` (sin cambio). SQL guarda metadata + URI relativa.

---

## Config

```env
ACCIO_ASSET_STORE=dual   # json | sql | dual
```

---

## Siguiente: M9 Leads (`leads.json`)
