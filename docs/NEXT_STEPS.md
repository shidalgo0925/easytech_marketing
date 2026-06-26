# Próximos pasos — ARROZCONPOLLO

**Actualizado:** 2026-06-26 (GO #2)  
**Estado:** push Git OK · legacy tick · n8n importado (inactivo)

---

## Hecho en esta sesión

- [x] `PROJECT_STATE.md` creado
- [x] `doctor.sh` creado y probado
- [x] `INVENTARIO_DESPLIEGUE.md` actualizado
- [x] Cron tick corregido (`/accio/easytech/tick`)
- [x] RBAC API key corregido para automatización
- [x] `CHANGELOG.md` y `NEXT_STEPS.md` creados
- [x] **Push** `5661107` → `origin/main`
- [x] Ruta legacy `POST /accio/tick` (compatibilidad docs antiguos)
- [x] Workflows n8n importados (inactivos — ver nota abajo)

---

## Prioridad alta

1. **Flyer #10 IIUS** — requiere PNG del dueño; subir y ejecutar `scripts/import_flyer.sh 10_iius.png`
2. **Post LinkedIn #4** — programado 2026-06-30; cron `linkedin_auto_publish.sh` (Mar/Jue 15:00, Vie 20:00) publicará si `scheduled_at` ya pasó
3. ~~**Push Git**~~ — hecho
4. **Verificar cron pipeline** — próximo domingo 6:00; revisar `logs/cron.log`

---

## Prioridad media

5. **n8n workflows** — importados en n8n (inactivos). **Nota:** cron del VPS ya cubre LinkedIn y pipeline; activar en n8n solo si se quiere reemplazar cron. Panel: https://n8n.etsrv.site
6. **Tokens Meta** — completar `META_PAGE_ACCESS_TOKEN`, `META_IG_USER_ID`
7. **Google Business** — completar OAuth refresh token y `GOOGLE_BUSINESS_LOCATION_ID`
8. **Accio Work Desktop** — conectar MCP (`docs/ACCIO_WORK_ARROZCONPOLLO.md`)

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
