# Próximos pasos — ARROZCONPOLLO

**Actualizado:** 2026-06-26  
**Estado:** post-estabilización inicial (GO ejecutado)

---

## Hecho en esta sesión

- [x] `PROJECT_STATE.md` creado
- [x] `doctor.sh` creado y probado
- [x] `INVENTARIO_DESPLIEGUE.md` actualizado
- [x] Cron tick corregido (`/accio/easytech/tick`)
- [x] RBAC API key corregido para automatización
- [x] `CHANGELOG.md` y `NEXT_STEPS.md` creados

---

## Prioridad alta

1. **Flyer #10 IIUS** — crear `Marketing/flyers/10_iius.png`, actualizar `manifest.json`
2. **Post LinkedIn #4** — programado 2026-06-30; verificar publicación automática o manual con aprobación
3. **Commitear y push** cambios de estabilización a `origin/main`
4. **Verificar cron pipeline** — próximo domingo 6:00 (`run_pipeline.sh`); revisar `logs/cron.log`

---

## Prioridad media

5. **n8n workflows** — importar y activar `docs/n8n-workflow-linkedin.json` y `docs/n8n-workflow-semanal.json`
6. **Tokens Meta** — completar `META_PAGE_ACCESS_TOKEN`, `META_IG_USER_ID` si publicación FB/IG es objetivo
7. **Google Business** — completar OAuth refresh token y `GOOGLE_BUSINESS_LOCATION_ID`
8. **Accio Work Desktop** — conectar MCP con URLs de `docs/ACCIO_WORK_ARROZCONPOLLO.md`
9. **Legacy route `/accio/tick`** — opcional: alias en app.py para compatibilidad con docs antiguos

---

## Prioridad baja / fuera de scope

10. Integración EN1 / Econverso (requiere definición de producto)
11. Swap en VPS (actualmente 0B)
12. Fase E matriz editorial 95/5 — ver `docs/ROADMAP.md`

---

## Cómo operar campañas (flujo mínimo)

1. Editar cola: `Marketing/tenants/easytech/content_queue.json` o vía dashboard
2. Ver estado: `scripts/accio_cli.sh status`
3. Publicar LinkedIn (con aprobación): `scripts/accio_cli.sh publish`
4. Tick manual: `scripts/accio_tick.sh`
5. Diagnóstico servidor: `scripts/doctor.sh`

---

## Antes de cada sesión de trabajo

```bash
/opt/easytech_marketing/scripts/doctor.sh
```

Leer `docs/PROJECT_STATE.md` → diagnosticar → plan → GO.
