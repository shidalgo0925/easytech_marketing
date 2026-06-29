# ADR-0003: Arquitectura en capas Marketing OS

**Estado:** Aceptado (Sprint 2)  
**Fecha:** 2026-06-26  
**Contexto:** [MARKETING_OS_ARCHITECTURE.md](../MARKETING_OS_ARCHITECTURE.md) · [MARKETING_OS_DOMAIN_MODEL.md](../MARKETING_OS_DOMAIN_MODEL.md)

---

## Contexto

El motor `accio_engine` tiene dos estilos coexistiendo:

1. **Slice vertical MarketingPlan** — domain → application → infrastructure → `/api/v1` (correcto)
2. **Legacy flat** — `app.py` + `*_store.py` + JSON directo (deuda técnica)

Sprint 1 cerró dominio y persistencia conceptual. Sin decisión de capas, cada pilar nuevo repetiría el patrón legacy.

---

## Decisión

1. **Patrón obligatorio** para todo agregado nuevo y migraciones:

   ```
   HTTP/UI → API → Application (use cases) → Domain Service → Repository Port → Adapter
   ```

2. **Referencia canónica:** módulos `marketing_plan_*` — copiar estructura, no contenido.

3. **Legacy `/accio/`** permanece hasta adapter equivalente en `/api/v1` + período de convivencia documentado.

4. **Composition root** por bounded context (`*_api/composition.py`), no wiring en `app.py`.

5. **Eventos de dominio** → `DomainEventPublisher` → `CorporateMemoryService.record` (adapter infra).

6. **Persistencia fase B:** repositorios SQLite implementan mismos ports que JSON adapters durante migración dual-write opcional.

7. **`app_id` en rutas HTTP** se mantiene; dominio interno usa `brand_id` en mapeo repositorio.

---

## Consecuencias

### Positivas

- Onboarding: un solo patrón
- Testeable (memory repos, collecting event publisher)
- Migración incremental sin big-bang

### Negativas

- Refactor gradual de `app.py` (no eliminar de golpe)
- Más carpetas por agregado

### No hacer

- Llamar Domain Service desde routes HTTP
- Nuevos `*_store.py` flat sin port
- IA/HTTP dentro de `marketing_plan_domain/` o equivalentes

---

## Referencias

- [ADR-0002](0002-marketing-os-persistence-store.md)
- [API_CONTRACT_V1.md](../API_CONTRACT_V1.md)
- [MARKETING_PLAN_APPLICATION_LAYER.md](../MARKETING_PLAN_APPLICATION_LAYER.md)
