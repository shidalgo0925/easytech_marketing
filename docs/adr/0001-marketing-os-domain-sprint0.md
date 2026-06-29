# ADR-0001: Sprint 0 — Dominio Marketing OS

**Estado:** Propuesto (Sprint 0 en curso)  
**Fecha:** 2026-06-26  
**Contexto:** [EMACCION_PRODUCT_VISION_v2.2.md](../EMACCION_PRODUCT_VISION_v2.2.md) · [MARKETING_OS_DOMAIN_SPRINT0.md](../MARKETING_OS_DOMAIN_SPRINT0.md)

---

## Contexto

EM+Acción evoluciona de aplicación de marketing a **Marketing OS** (plataforma). Sin dominio estable, el riesgo de rehacer modelos, APIs y BD es alto.

---

## Decisión

1. **Sprint 0 = arquitectura de dominio exclusivamente** — sin features de usuario, sin IA, sin UI nueva.
2. **Jerarquía SaaS:** Tenant → Empresa → Marca → Producto → Campaña → Contenido → Resultados → Corporate Memory.
3. **`app_id` actual = Marca** — no renombrar en código hasta sprint de migración explícito.
4. **`MarketingPlan` v1.1 permanece congelado** — subdominio en fase Planificar; no expandir entidad Plan con campos operativos.
5. **Corporate Memory** es agregado transversal a nivel Tenant/Empresa; compartido entre marcas.
6. **Recomendación** es entidad central del Roadmap Engine — siempre con responsable, prioridad, impacto, estado, dependencias.
7. **AI Provider** = capa infraestructura; contratos definidos en Sprint 0, integración post-dominio.
8. **Plan Maestro** no se modifica en Sprint 0; alineación en iteración posterior.

---

## Consecuencias

### Positivas

- Fundamento común para BD, APIs, automatizaciones y UI
- Onboarding de devs con vocabulario único
- Filtro anti-«pantalla suelta»

### Negativas / costos

- Pausa features visibles (CODITO, Roadmap proactivo) hasta cierre dominio
- Esfuerzo documental upfront

### Pendiente de definir en Sprint 0

- [ ] ER cardinalidad completa
- [ ] Matriz ownership
- [ ] Propuesta persistencia (JSON fase 1 vs SQLite/Postgres)
- [ ] Lista servicios de dominio
- [ ] APIs propuestas (recursos REST v2)

---

## Alternativas consideradas

| Alternativa | Rechazada porque |
|-------------|------------------|
| Continuar con módulos (chat, IA CODITO) | Acopla producto a features, no a plataforma |
| Expandir Plan Maestro primero | Mezcla fases técnicas con modelo de negocio |
| Renombrar `app` → `marca` en código ya | Rompe compatibilidad; mapping documental primero |

---

## Referencias

- Product Vision v2.2 (CONGELADO)
- MARKETING_PLAN_DOMAIN_v1.1 (CONGELADO)
