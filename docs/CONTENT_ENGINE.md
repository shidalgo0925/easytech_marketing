# Content Engine

**Estado:** Activo · **Versión:** v1 · **Fase:** I (Plan Maestro v3.1)

Transforma **campañas aprobadas** en **piezas de contenido estructuradas**, trazables y listas para la cola de aprobación editorial.

---

## Flujo

```
Campaign (approved)
        ↓
ContentPlanner
        ↓
ContentBuilder
        ↓
Content Explain
        ↓ (opcional)
Marketing Brain → AI Provider → Content Enrichment
        ↓
pending_approval → approved → (futuro) Publication / Publisher
```

---

## API

Base: `/api/v1/tenants/{tenant_id}/content`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/content` | Listar piezas |
| GET | `/content/{id}` | Detalle |
| GET | `/content/{id}/explain` | Explicación |
| PATCH | `/content/{id}` | Actualizar |
| POST | `/content/from-campaign/{campaign_id}` | Crear desde campaña |
| POST | `/content/{id}/enrich` | Enriquecimiento IA |
| POST | `/content/{id}/approve` | Aprobar contenido |

---

## Schema v15

- `content_pieces`
- `content_variants`
- `content_history`

---

## Consola

Sección **Contenido** en `/accio/plan/{tenant}/` con botón **Generar contenido** en campañas aprobadas.

---

## No incluido

- Publisher automático sin acción humana
- Otros canales (Meta, Instagram…) — ver VS2 limitaciones

**VS2 (cerrado):** aprobación → cola → LinkedIn vía `ContentPublisherBridge`. Ver [VS2_PRIMERA_CAMPANA_PUBLICADA.md](VS2_PRIMERA_CAMPANA_PUBLICADA.md).

---

## Tests

`tests/test_content_engine.py` · `tests/test_vs2_content_publish.py`
