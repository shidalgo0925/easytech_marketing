# Vertical Slice 1 — EM+Acción Marketing Plan

**Estado:** Implementado  
**Fase:** B (validación end-to-end)

## Objetivo

Un solo flujo atravesando todas las capas:

```
Administrador → Crear Plan → Activar → Ver Plan → Context Builder → Planner IA (3 propuestas)
```

## Endpoints (API v1)

Base: `/api/v1/tenants/{tenant_id}/apps/{app_id}`

| Método | Ruta | Caso de uso |
|--------|------|-------------|
| POST | `/marketing-plans` | CreateMarketingPlan |
| POST | `/marketing-plans/{id}/activate` | ActivateMarketingPlan |
| GET | `/marketing-plans/{id}` | GetMarketingPlan |
| GET | `/marketing-plans/active` | GetActiveMarketingPlan |

Extensiones del slice (no en contrato completo):

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/marketing-context` | Context Builder V1 |
| POST | `/planner/proposals` | 3 propuestas (LLM o fallback) |

## Capas

```
Dashboard (tab Plan) → /api/v1 → Application Layer → Domain Service → JsonMarketingPlanRepository
                                                      ↓
                                              Marketing/tenants/{tenant}/apps/{app}/marketing_plans/
```

- **Composition root:** `Motor_Tecnico/accio_engine/marketing_plan_api/composition.py`
- **Context Builder:** `Motor_Tecnico/accio_engine/marketing_context_builder.py`
- **Planner:** `Motor_Tecnico/accio_engine/marketing_planner.py`

## UI mínima

Dashboard → pestaña **Plan**:

- Ver plan activo
- Crear borrador
- Lista de planes creados en sesión (localStorage)
- Activar borrador
- Generar 3 propuestas IA

## Fuera de alcance (Fase C+)

- OpenAPI / Swagger
- Listado paginado REST
- Campaigns, Calendar, Assets, publicaciones
- Context Builder completo (campañas, métricas, historial)

## Tests

```bash
python -m unittest tests/test_vertical_slice_1.py -v
```

## Próximo paso

Tras validar el slice en producción/staging: expandir recursos (Campaign, Calendar) repitiendo el mismo patrón vertical.
