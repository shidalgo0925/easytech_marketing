# Changelog — EasyMarketingOne / ARROZCONPOLLO

Formato basado en fechas. Solo cambios operativos relevantes en el VPS o repo.

---

## 2026-06-26 — Estabilización inicial ARROZCONPOLLO

### Añadido
- `docs/PROJECT_STATE.md` — fuente única de verdad del servidor y reglas de operación
- `scripts/doctor.sh` — diagnóstico automatizado (host, servicios, git, docker)
- `docs/CHANGELOG.md` — este archivo
- `docs/NEXT_STEPS.md` — plan operativo pendiente

### Corregido
- `scripts/accio_tick.sh` — ruta `POST /accio/easytech/tick` (antes `/accio/tick` → 404)
- `scripts/accio_cli.sh` — rutas tenant-scoped para `orders` y `tick`
- `Motor_Tecnico/accio_engine/app.py` — API key Bearer recupera permisos de automatización (cron/Accio Work); antes RBAC devolvía 403 en `tick`

### Actualizado
- `docs/INVENTARIO_DESPLIEGUE.md` — refleja motor Accio activo, servicios OAuth, endpoints multi-tenant

### Verificado
- `easytech-accio-engine` running en :8092
- Endpoints: `/accio/health`, `/accio/status`, `/accio/easytech/tasks`, `/accio/files/tree` → 200
- OAuth services LinkedIn/Meta/Google → 200
- `accio_tick.sh` → `{"ok": true, "message": "Sin ordenes pendientes"}`

---

## 2026-06-26 — GO #2 (push + n8n + legacy tick)

### Añadido
- Ruta legacy `POST /accio/tick` → delega a `/accio/easytech/tick`

### Corregido
- `docs/n8n-workflow-*.json` — IDs de workflow y nodos para import CLI n8n

### Desplegado
- Push commit `5661107` → `origin/main`
- Workflows n8n importados (inactivos): LinkedIn automático, pipeline semanal

### Pendiente (requiere dueño)
- Flyer `10_iius.png` — sin asset fuente en servidor
- Activar workflows n8n (opcional; cron VPS ya activo)

---

## Histórico (commits recientes en Git)

| Fecha | Commit | Resumen |
|-------|--------|---------|
| 2026-06-26 | `b7e34a9` | Multi-empresa, auth, CRUD configuración |
| 2026-06-26 | `a5bb44d` | Phase E Knowledge Engine integrado |
| 2026-06-26 | `ad9bb91` | Documentación EMAcción como motor comercial IA |
| 2026-06-26 | `6732a05` | Roadmap Phase E |
| 2026-06-26 | `3fba19a` | Contexto proyecto + README |
