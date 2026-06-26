# Próximos pasos — ARROZCONPOLLO

**Actualizado:** 2026-06-27  
**Estado:** Fase 3 EN1 sync read-only · push pendiente

---

## Hecho

- [x] Estabilización ARROZCONPOLLO (doctor, tick, n8n, sessions)
- [x] `docs/EMACCION_TENANT_VS_APP.md` — arquitectura SaaS
- [x] Fase 1 App: `marketing_app.py`, registry, API `/accio/{tenant}/apps`
- [x] 22 posts easytech con `app_id: default`
- [x] **Fase 2 Apps** — selector UI dashboard + colas/publishers por `app_id`
- [x] **Fase 3 EN1** — sync read-only organizations ↔ `tenant_id`

---

## Prioridad alta

1. **Flyer #10 IIUS** — PNG del dueño → `scripts/import_flyer.sh 10_iius.png`
2. **Post LinkedIn #4** — 2026-06-30 vía cron
3. **Verificar cron pipeline** — domingo 6:00 → `logs/cron.log`
4. **Configurar EN1 API** — `EN1_API_URL` + key en CRM tenant relatic → sync live

---

## Prioridad media

5. **n8n** — workflows importados inactivos; cron VPS es principal
6. **Tokens Meta / Google**
7. **Accio Work Desktop** — MCP
8. **UI mapping EN1** — pantalla dashboard para vincular tenant ↔ org EN1
9. **Leads EN1** — write path (requiere GO + API EN1)

---

## Prioridad baja

9. Integración EN1 leads / Econverso
10. Swap VPS
11. Fase E editorial 95/5

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
