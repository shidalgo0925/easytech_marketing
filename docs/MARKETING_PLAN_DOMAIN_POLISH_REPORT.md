# Reporte de conformidad — Pulido post-auditoría (Pieza 3)

**Fecha:** 2026-06-27  
**Alcance:** 5 hallazgos de [`MARKETING_PLAN_DOMAIN_IMPLEMENTATION_AUDIT.md`](MARKETING_PLAN_DOMAIN_IMPLEMENTATION_AUDIT.md)

| Item | Estado |
|------|--------|
| ✔ Dependencia corregida | **OK** — `service.py` importa `AcceptAllTenantAppValidator` desde `defaults.py`; ya no importa `memory.py`. |
| ✔ Tests agregados | **OK** — 8 tests nuevos (R3, R9 create/update, budget, currency, complete borrador, update finalizado, tenant). **22 tests** total, todos pasan. |
| ✔ Errores unificados | **OK** — R2 usa `ACTIVE_PLAN_RESOLUTION_REQUIRED`; eliminados códigos muertos; `CURRENCY_INVALID` activo en validación de moneda. |
| ✔ R9 corregido | **OK** — `CreatePlanCommand.extra_fields` + `reject_forbidden_fields` simétrico a `update_plan`. |
| ✔ Stubs movidos | **OK** — `InMemoryMarketingPlanRepository`, `FixedClock`, `FixedIdGenerator` en `marketing_plan_infrastructure/`. |

**Verificación:** `python3 -m unittest tests.test_marketing_plan_domain_service -v` → OK

**No modificado:** dominio congelado, schema, documentos de diseño, API, persistencia.

**Listo para:** Pieza 4 — Infrastructure Adapters (primer adaptador de repositorio).
