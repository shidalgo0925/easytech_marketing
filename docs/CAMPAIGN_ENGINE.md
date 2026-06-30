# Campaign Engine

**Estado:** Activo · **Versión:** v1 · **Fase:** H (Plan Maestro v3.1)

Transforma **recomendaciones aprobadas** en **campañas de marketing estructuradas**, trazables y listas para generación de contenido posterior.

---

## Arquitectura

```
Recommendation (approved)
        ↓
CampaignPlanner (contexto + score + explain)
        ↓
CampaignBuilder (estructura)
        ↓
Campaign Explain (trazabilidad)
        ↓
Persistencia (campaigns + channels + kpis + history)
        ↓ (opcional)
Marketing Brain → AI Provider → Campaign Enrichment
```

### Capas

| Capa | Módulo |
|------|--------|
| Dominio | `campaign_domain/campaign_planner.py`, `campaign_builder.py`, `campaign_explainability.py`, `engine_service.py` |
| Aplicación | `campaign_application/engine_use_cases.py` |
| Infraestructura | `campaign_infrastructure/engine_sqlite_repository.py`, `engine_orchestrator.py`, `campaign_llm_client.py` |
| API | `campaign_api/engine_routes.py` |

La IA **no crea** campañas desde cero. Solo enriquece campos sobre estructura existente.

---

## Modelo de datos (schema v14)

### Tabla `campaigns` (extendida)

Campos clave del motor: `recommendation_id`, `opportunity_id`, `description`, `target_audience`, `value_proposition`, `call_to_action`, `priority`, `owner`, fechas, estimaciones, `explain_json`, `llm_enrichment_json`, `origin_score`.

### Tablas auxiliares

- `campaign_channels` — canales sugeridos
- `campaign_kpis` — KPIs iniciales
- `campaign_history` — auditoría de eventos

---

## Estados

`draft` → `pending_approval` → `approved` → `scheduled` → `running` → `completed` | `cancelled` | `archived`

**No publica automáticamente.** Publisher es integración futura.

---

## API REST (tenant-scoped)

Base: `/api/v1/tenants/{tenant_id}/campaigns`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/campaigns` | Listar (`?status=`, `?brand_id=`) |
| GET | `/campaigns/{id}` | Detalle |
| GET | `/campaigns/{id}/explain` | Explicación técnica |
| PATCH | `/campaigns/{id}` | Actualizar campos |
| POST | `/campaigns/from-recommendation/{rec_id}` | Crear desde recomendación aprobada |
| POST | `/campaigns/{id}/enrich` | Enriquecimiento IA |
| POST | `/campaigns/{id}/approve` | Aprobar campaña |
| POST | `/campaigns/{id}/archive` | Archivar |

La API M7 legacy (`/apps/{app_id}/campaigns`) se mantiene para compatibilidad.

---

## Campaign Explain

Responde **¿por qué esta campaña?** con:

- recomendación y oportunidad origen
- score y factores
- reglas disparadas
- contexto considerado (Company Brain, Knowledge Matrix, etc.)
- razonamiento del motor
- enriquecimiento IA (si disponible)

---

## Consola

En `/accio/plan/{tenant}/` — sección **Campañas**:

- Recomendaciones aprobadas con botón **Crear campaña**
- Listado de campañas con score, objetivo, audiencia, estado
- Panel **¿Por qué?** (modal compartido)

---

## Integración futura con Publisher

```
Campaign (approved)
        ↓
Content generation (futuro)
        ↓
Approval Queue
        ↓
Publisher
        ↓
Analytics → Learning
```

Relación preparada vía `campaign_id` y `recommendation_id`; sin conexión automática en este bloque.

---

## Degradación IA

Si `ACCIO_AI_BASE_URL` no está configurado:

- `campaign.llm_skipped = true`
- El flujo continúa con estructura del motor

---

## Tests

`tests/test_campaign_engine.py` — planner, builder, explain, API, schema v14.
