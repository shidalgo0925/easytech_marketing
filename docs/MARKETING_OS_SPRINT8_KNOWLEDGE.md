# M6 — ProductKnowledge (Sprint 8)

**Estado:** ✅ Cerrado (2026-06-26)

---

## Entregables

| Item | Ubicación |
|------|-----------|
| Schema v6 `knowledge_articles` | `platform_infrastructure/schema_v6_knowledge.py` |
| Domain slice | `knowledge_article_{domain,application,infrastructure,api}/` |
| Facade | `knowledge_api.list/load/save/delete` → SQL cuando `ACCIO_KNOWLEDGE_STORE=sql\|dual` |
| API | `GET /api/v1/tenants/{id}/knowledge/articles[/{slug}]` |
| Migración | `scripts/migrate_knowledge_to_sql.py` |
| Tests | `tests/test_knowledge_articles.py` |

---

## Config

```env
ACCIO_KNOWLEDGE_STORE=dual   # json | sql | dual
```

Legacy: `knowledge/manifest.json` + `knowledge/*.md` siguen sincronizados en modo dual.

---

## Siguiente: M7 Campaigns (`campaigns.json`)
