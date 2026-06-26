# Fase B V2 — Checklist de cierre

**Referencia:** [EMACCION_V2_PLAN_MAESTRO.md](../EMACCION_V2_PLAN_MAESTRO.md) §5

---

## Modelo tenant

- [x] `registry.json` v2 (timezone, created_at, domains)
- [x] `tenant.json` por tenant (branding)
- [x] Carpetas `Marketing/tenants/{id}/` aisladas
- [x] API `/accio/{tenant_id}/...`
- [x] Dashboard `/accio/dashboard/{tenant_id}/`
- [x] Branding CSS por tenant (colores inyectados)
- [x] API `GET/POST /accio/{tenant_id}/settings/tenant`
- [x] UI Configuración → Tenant / Branding
- [ ] Usuarios y roles por tenant (Fase C)
- [ ] Logo upload (URL por ahora)

## Aislamiento

- [x] Cola, KB, campañas separados (easytech vs relatic)
- [x] `tests/test_tenant_isolation.py`
- [ ] Deprecar rutas legacy `Marketing/accio/` (symlink o warning)
- [ ] CI ejecutando tests

## Pruebas

```bash
cd /opt/easytech_marketing
python3 -m unittest tests/test_tenant_isolation.py -v
```

**Estado:** 🔄 ~85% — falta usuarios/RBAC y deprecación legacy explícita.
