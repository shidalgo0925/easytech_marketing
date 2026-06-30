# Marketing Intelligence Layer

**Estado:** Activo · **Versión:** v1 · **Fecha:** 2026-06-30

Capa que transforma EM+Acción de detector de reglas a sistema que **prioriza, explica y justifica** decisiones de marketing.

---

## Componentes

### OpportunityScorer (`marketing_intelligence_domain/opportunity_scorer.py`)

Calcula **score 0–100** por oportunidad usando:

| Factor | Peso |
|--------|------|
| Prioridad de regla | 20% |
| Antigüedad de la señal | 15% |
| Impacto comercial por tipo | 18% |
| Leads afectados | 15% |
| Campañas relacionadas | 10% |
| Actividad reciente | 12% |
| Alineación Company Brain | 10% |

Persiste en `opportunities.score`, `opportunities.reasoning_json`, actualiza `priority` y `confidence`.

La **prioridad final** combina regla y score (`resolve_opportunity_priority`): el scorer nunca degrada una regla marcada como `high`.

**Versión algoritmo:** `opportunity_scorer_v1`

### RecommendationComposer (`marketing_intelligence_domain/recommendation_composer.py`)

Transforma oportunidad + score en recomendación ejecutiva estructurada:

- título, descripción, objetivo, impacto esperado
- acción recomendada, prioridad
- razones, evidencias, siguientes pasos

El **Marketing Brain (M11)** solo enriquece esta estructura; no crea recomendaciones desde cero.

**Versión:** `recommendation_composer_v1`

### Explainability (`marketing_intelligence_domain/explainability.py`)

Objeto `explain` por recomendación:

- reglas disparadas
- datos utilizados
- score y factores
- contexto considerado
- fecha y versión del algoritmo
- estructura `composed`

Persistido en `recommendations.explain_json` y `recommendations.composed_json`.

**Versión:** `explainability_v1`

### Marketing Context Engine (extendido)

`MarketingContextBuilder.build_for_recommendation()` agrega:

- score de oportunidad y factores
- campañas relacionadas y publicaciones recientes
- KPIs operativos
- historial de aprobaciones
- recomendaciones similares pendientes

---

## Flujo de decisión

```
Reglas Opportunity Engine
        ↓
OpportunityScorer (score + reasoning)
        ↓
Persistencia opportunities
        ↓ (promote)
RecommendationComposer → explain
        ↓
Recommendation pending_approval
        ↓ (opcional)
Marketing Brain enrich (IA sobre estructura existente)
        ↓
Approval Queue (M10.5)
```

---

## API v2 (sin romper v1)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/tenants/{tenant}/recommendations/{id}/explain` | Explicación técnica + composed + IA |
| POST | `/api/v1/tenants/{tenant}/recommendations/{id}/recompose` | Recalcular recomendación desde oportunidad |
| GET | `/api/v1/tenants/{tenant}/recommendations/{id}/similar` | Comparar recomendaciones similares |
| POST | `/api/v1/tenants/{tenant}/opportunities/{id}/rescore` | Recalcular score |

---

## Consola

En `/accio/plan/{tenant}/` → **¿Por qué?** en cada recomendación:

- Score y prioridad
- Reglas disparadas
- Factores y razonamiento del motor
- Evidencias
- Narrativa IA (si existe enrich)

---

## Schema

**v13** — columnas `score`, `reasoning_json` en `opportunities`; `explain_json`, `composed_json` en `recommendations`.

---

## Tests

`tests/test_marketing_intelligence_layer.py`

---

## Siguiente bloque

**Campaign Engine** — generará campañas apoyadas en recomendaciones con explain y score verificables.
