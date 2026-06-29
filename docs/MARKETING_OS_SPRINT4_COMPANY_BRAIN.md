# M2 — Company Brain (Sprint 4)

**Estado:** ✅ Cerrado (2026-06-29)  
**Migración:** M2 · `business_context.json` → `company_profiles`

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v2 | `platform_infrastructure/schema_v2_company_brain.py` |
| Domain slice | `company_brain_{domain,application,infrastructure,api}/` |
| Facade legacy | `company_brain_infrastructure/facade.py` → `knowledge_api` |
| API | `GET/PATCH /api/v1/tenants/{id}/company-brain` |
| Migración | `scripts/migrate_business_context_to_brain.py` |
| Tests | `tests/test_company_brain.py` |

---

## Configuración

```env
ACCIO_BRAIN_STORE=dual    # json | sql | dual
```

| Modo | Lectura | Escritura |
|------|---------|-----------|
| `json` | Solo `business_context.json` | Solo JSON |
| `sql` | Solo `company_profiles` | Solo SQL |
| `dual` | SQL primero, fallback JSON | Ambos |

Tras migrar: `ACCIO_BRAIN_STORE=sql` o `dual`.

---

## Migración producción

```bash
python3 scripts/migrate_business_context_to_brain.py
# por tenant:
python3 scripts/migrate_business_context_to_brain.py --tenant easytech
```

---

## Siguiente: M3 Brands (`apps/registry.json` → `brands`)
