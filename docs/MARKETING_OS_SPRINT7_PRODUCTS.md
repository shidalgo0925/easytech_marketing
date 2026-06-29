# M5 — Products (Sprint 7)

**Estado:** ✅ Cerrado (2026-06-26)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v5 `products` | `platform_infrastructure/schema_v5_products.py` |
| Domain slice | `product_{domain,application,infrastructure,api}/` |
| Facade | `settings_center.load/save_products` → SQL cuando `ACCIO_PRODUCT_STORE=sql\|dual` |
| API | `GET /api/v1/tenants/{id}/apps/{app_id}/products[/{product_id}]` |
| Migración | `scripts/migrate_products_to_sql.py` |
| Tests | `tests/test_products.py` |

---

## Config

```env
ACCIO_PRODUCT_STORE=dual   # json | sql | dual
```

Mapeo slug→marca (easytech): `marketing_app._PRODUCT_SLUG_TO_APP`. Otros tenants → `default`.

---

## Siguiente: M6 ProductKnowledge (`knowledge/*.md`)
