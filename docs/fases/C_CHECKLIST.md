# Fase C V2 — Checklist de cierre

**Referencia:** [EMACCION_V2_PLAN_MAESTRO.md](../EMACCION_V2_PLAN_MAESTRO.md) §6

---

## Backend (`settings_center.py` + `rbac.py`)

- [x] `GET /accio/{tenant_id}/settings/center` — vista unificada
- [x] `POST /settings/empresa` — contexto de negocio (KB)
- [x] `POST /settings/productos` — `products.json` con seed desde business context
- [x] `POST /settings/publicacion` — canales + reglas editoriales
- [x] `POST /settings/landings` — dominio, UTM, rutas
- [x] `POST /settings/variables` — JSON plano + secretos cifrados
- [x] `POST /settings/ia` — `ai.json`
- [x] `POST /settings/usuarios` — `users.json` + contraseñas hasheadas
- [x] `GET /settings/logs` — tail de logs del motor
- [x] `POST /settings/backup` — ejecutar `backup_secrets.sh`
- [x] `POST /settings/logo` — upload a `tenants/{id}/assets/`
- [x] `GET /accio/{tenant_id}/assets/<file>` — servir logo del tenant
- [x] RBAC enforced en API (`rbac.py` + `require_api_key`)
- [x] Login email/contraseña por tenant (`POST /accio/auth/login`)
- [x] Rutas previas: conectores, CRM, platform, tenant branding

## Dashboard — Configuration Center

- [x] Sub-navegación lateral (13 secciones)
- [x] Login dual: API Key / Usuario
- [x] Badge de rol en header; botones según permisos
- [x] Upload de logo en Tenant / Branding
- [x] Usuarios con campo contraseña (admin)

## Tests

- [x] `tests/test_settings_center.py`
- [x] `tests/test_rbac.py`

## Pendiente menor

- [ ] Guía operativa “no editar JSON manual” en `docs/`
- [ ] OAuth por usuario (hoy email+password local)

## Pruebas manuales

```bash
cd /opt/easytech_marketing
python3 -m unittest tests/test_tenant_isolation.py tests/test_settings_center.py tests/test_rbac.py -v

curl -s -H "X-Accio-Key: $ACCIO_API_KEY" \
  http://127.0.0.1:8092/accio/easytech/settings/center | python3 -m json.tool | head
```

**Estado:** ✅ ~95% — listo para cierre formal; RBAC y auth multi-usuario operativos.
