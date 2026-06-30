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

- Publisher automático
- Encolado directo en `content_queue.json` (bloque siguiente)

---

## Tests

`tests/test_content_engine.py`
