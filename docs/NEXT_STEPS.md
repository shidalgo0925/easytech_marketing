# Próximos pasos — ARROZCONPOLLO

**Actualizado:** 2026-06-27  
**Estado:** Tenant SaaS nativo corregido

---

## Hecho

- [x] Estabilización ARROZCONPOLLO (doctor, tick, n8n, sessions)
- [x] Arquitectura Tenant vs App (`docs/EMACCION_TENANT_VS_APP.md`)
- [x] Fase 1–2 Apps: registry, selector UI, colas por `app_id`
- [x] **Tenant nativo EMAcción** — subdomain, registration, UI Organización, CRUD plataforma

---

## Prioridad alta

1. **Flyer #10 IIUS** — PNG del dueño → `scripts/import_flyer.sh 10_iius.png`
2. **Post LinkedIn #4** — 2026-06-30 vía cron
3. **Verificar cron pipeline** — domingo 6:00 → `logs/cron.log`
4. **UI Apps en Configuración** — gestionar apps del tenant (además del selector header)

---

## Prioridad media

5. **n8n** — workflows importados inactivos; cron VPS es principal
6. **Tokens Meta / Google**
7. **Accio Work Desktop** — MCP
8. **CRM externo** — Odoo/EN1 como destino de leads (no como registro de tenants)

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
