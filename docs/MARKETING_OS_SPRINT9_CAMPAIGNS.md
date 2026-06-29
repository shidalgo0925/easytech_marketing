# M7 — Campaigns (Sprint 9)

**Estado:** ✅ Cerrado (2026-06-26)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v7 `campaigns` | `platform_infrastructure/schema_v7_campaigns.py` |
| Domain slice | `campaign_{domain,application,infrastructure,api}/` |
| Facade | `dashboard_data.load_campaigns` + `publications_api` → SQL cuando `ACCIO_CAMPAIGN_STORE=sql\|dual` |
| API | `GET /api/v1/tenants/{id}/apps/{app_id}/campaigns[/{id}]` |
| Migración | `scripts/migrate_campaigns_to_sql.py` |
| Tests | `tests/test_campaigns.py` |

---

## Config

```env
ACCIO_CAMPAIGN_STORE=dual   # json | sql | dual
```

`load_campaigns` sigue fusionando definiciones con `content_queue` para la vista dashboard.

---

## Siguiente: M8 MediaAssets (`flyers/`)
