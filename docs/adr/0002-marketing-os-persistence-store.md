# ADR-0002: Persistencia Marketing OS — store y migración

**Estado:** Aceptado (Sprint 1)  
**Fecha:** 2026-06-26  
**Contexto:** [MARKETING_OS_DOMAIN_PERSISTENCE.md](../MARKETING_OS_DOMAIN_PERSISTENCE.md) · [MARKETING_OS_CONSTITUTION.md](../MARKETING_OS_CONSTITUTION.md) (Principios 9, 12, 16)

---

## Contexto

El Marketing OS requiere persistencia multi-tenant con Corporate Memory append-only, conocimiento exportable y convivencia con datos legacy en JSON por filesystem. Elegir motor antes de Domain Model v1.0 bloqueaba el diseño lógico.

---

## Decisión

1. **Diseño lógico primero** — tablas y agregados en `MARKETING_OS_DOMAIN_PERSISTENCE.md` son independientes del motor.
2. **Fase A (actual → 6 meses):** legacy JSON + SQLite existente (`auth.db`, secretos) sin migración big-bang.
3. **Fase B (objetivo plataforma):** **SQLite único** `marketing_os.db` por instancia del motor, con `tenant_id` en todas las tablas core.
4. **Fase C (escala SaaS):** migración opcional a **PostgreSQL** con mismo esquema lógico; sin rediseño de dominio.
5. **Corporate Memory:** tabla `memory_events` append-only; prohibido `DELETE` (Principio 12).
6. **MarketingPlan v1.1:** permanece en JSON (`marketing_plans/*.json`) hasta subdominio Plan tenga migración explícita.
7. **Mapping legacy:** `app_id` → `brand_id` en capa persistencia; sin renombrar carpetas hasta sprint de migración.

---

## Consecuencias

### Positivas

- Alineado con stack actual (SQLite ya en producción)
- Esquema portable a Postgres
- Migración incremental por agregado

### Negativas

- SQLite limita concurrencia escritura masiva (aceptable en V1)
- Dual-write temporal JSON + DB durante migración

### Reglas ON DELETE

| Relación | Regla |
|----------|-------|
| tenant → * | RESTRICT (no borrar tenant con datos) |
| brand → campaign, publication | RESTRICT o soft-archive |
| campaign → publication | CASCADE soft (archive) |
| memory_events | **Nunca DELETE** |

---

## Alternativas consideradas

| Alternativa | Rechazada porque |
|-------------|------------------|
| Solo JSON indefinido | No escala Corporate Memory ni queries |
| Postgres inmediato | Overhead ops en ARROZCONPOLLO; SQLite suficiente V1 |
| DB por tenant | Complejidad backup/migración en N clientes |

---

## Referencias

- [ADR-0001](0001-marketing-os-domain-sprint0.md)
- [MARKETING_OS_DOMAIN_MODEL.md](../MARKETING_OS_DOMAIN_MODEL.md)
