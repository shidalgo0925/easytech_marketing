# Inventario de despliegue — ArrozConPollo

**Servidor:** `95.111.244.137` (`vmi3119011`)  
**Proyecto:** `/opt/easytech_marketing`  
**Fecha auditoría:** 2026-06-26  
**Auditor:** Cursor — verificado con `doctor.sh`, `systemctl`, `curl`

---

## Veredicto ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Está desplegado el **motor Accio/EMAcción**? | **SÍ** — `easytech-accio-engine` (Python Flask, multi-tenant) |
| ¿Hay motor de marketing/prospección funcionando? | **SÍ** — accio_engine + scraper, Odoo sync, landing, publishers |
| ¿Hay integración API con **EN1 / EasyNodeOne**? | **NO** — EN1 solo en contenido/flyers de marketing |
| ¿Dashboard operativo? | **SÍ** — https://n8n.etsrv.site/accio/dashboard/easytech/ |
| ¿Git versionado? | **SÍ** — `main` en `github.com/shidalgo0925/easytech_marketing` |

---

## Servicios corriendo (evidencia 2026-06-26)

| Servicio | Tipo | Puerto | Estado |
|----------|------|--------|--------|
| `easytech-accio-engine` | systemd | 127.0.0.1:8092 | **active** |
| `easytech-lead-api` | systemd | 127.0.0.1:8080 | **active** |
| `easytech-linkedin-oauth` | systemd | 127.0.0.1:8091 | **active** |
| `easytech-meta-oauth` | systemd | 127.0.0.1:8093 | **active** |
| `easytech-google-oauth` | systemd | 127.0.0.1:8094 | **active** |
| `easytech-tiktok-oauth` | systemd | 127.0.0.1:8095 | **active** |
| `easytech_marketing-n8n-1` | Docker | 127.0.0.1:5678 | **Up** |
| nginx | sistema | 80, 443 | **active** |

**Cron:**
- Cada 15 min → `scripts/accio_tick.sh` → `POST /accio/easytech/tick`
- Domingos 6:00 → `scripts/run_pipeline.sh`
- Mar/Jue 15:00, Vie 20:00 → `scripts/linkedin_auto_publish.sh`

---

## URLs públicas

| URL | Función | Backend |
|-----|---------|---------|
| https://n8n.etsrv.site/accio/ | EMAcción / Accio Engine | `accio_engine:8092` |
| https://n8n.etsrv.site/accio/dashboard/easytech/ | Dashboard EasyTech | `accio_engine:8092` |
| https://n8n.etsrv.site/accio/login/ | Login plataforma | `accio_engine:8092` |
| https://n8n.etsrv.site | Panel n8n | Docker n8n |
| https://n8n.etsrv.site/guia/ | Landing captura leads | `/var/www/guia/index.html` |
| https://n8n.etsrv.site/guia/api/lead | POST lead → Odoo | `lead_api.py:8080` |
| https://n8n.etsrv.site/linkedin/ | OAuth LinkedIn | `linkedin_oauth.py:8091` |
| https://n8n.etsrv.site/meta/ | OAuth Meta (FB/IG) | `meta_oauth.py:8093` |
| https://n8n.etsrv.site/google/ | OAuth Google | `google_oauth.py:8094` |
| https://easydb.etsrv.site | CRM Odoo | Externo (Easydb) |

---

## Motor Accio (`Motor_Tecnico/accio_engine/`)

| Componente | Función |
|------------|---------|
| `app.py` | API REST + dashboard web + auth multi-tenant |
| `executor.py` | Ejecuta órdenes (pipeline, publish, tick) |
| `dashboard_data.py` | Datos para dashboard |
| `auth_service.py` | Usuarios + RBAC (SQLite `auth.db`) |
| `tenant_secrets.py` | Secretos por tenant |

**Tenants registrados:** `easytech`, `relatic` (`Marketing/tenants/registry.json`)

**Endpoints principales (tenant-scoped):**

| Método | Ruta |
|--------|------|
| GET | `/accio/{tenant}/status` |
| GET | `/accio/{tenant}/tasks` |
| GET | `/accio/{tenant}/content/queue` |
| POST | `/accio/{tenant}/tick` |
| POST | `/accio/{tenant}/run/pipeline` |
| POST | `/accio/{tenant}/run/publish-linkedin` |
| GET | `/accio/files/tree` |
| GET | `/accio/openapi.json` |

Rutas legacy sin tenant (default `easytech`): `/accio/status`, `/accio/content/queue`, `/accio/run/*`.

---

## Código auxiliar (Motor_Tecnico)

| Archivo | Función |
|---------|---------|
| `scraper_panama.py` | Prospección → CSV |
| `odoo_sync.py` | CSV → Odoo CRM |
| `lead_api.py` | Formulario guía → Odoo |
| `linkedin_publisher.py` | Publica cola LinkedIn |
| `linkedin_oauth.py` | OAuth + publish LinkedIn |
| `meta_publisher.py` | Publica Facebook/Instagram |
| `connectors/` | Publishers Google, TikTok, etc. |

---

## Conectores (tenant easytech)

| ID | OAuth | Publisher | Estado config |
|----|-------|-----------|---------------|
| linkedin | :8091 | `linkedin_publisher.py` | configured |
| facebook | :8093 | `meta_publisher.py` | ver dashboard |
| instagram | :8093 | `meta_publisher.py` | ver dashboard |
| google_business | :8094 | `connectors/publishers/google_business.py` | parcial |
| youtube | :8094 | stub | pendiente tokens |
| tiktok | :8095 | stub | pendiente tokens |

---

## Datos operativos

| Artefacto | Estado |
|-----------|--------|
| `leads_prospeccion.csv` | ~37 filas de scraper |
| `Marketing/content_queue.json` | 3 posts LinkedIn publicados |
| Post #4 (`linkedin_04_fe_errores`) | **pending** → 2026-06-30 |
| `Marketing/flyers/` | 12 flyers (#10 IIUS falta) |
| n8n workflows importados | **No confirmado** |
| `logs/accio_tick.log` | Activo (tick OK tras fix 26-jun) |

### Posts LinkedIn publicados

| ID cola | LinkedIn URN |
|---------|--------------|
| linkedin_01_fe_odoo | urn:li:share:7473608703850762240 |
| linkedin_02_diagnostico | urn:li:share:7473609231162654720 |
| linkedin_03_implementamos_odoo | urn:li:share:7473610329587908609 |

---

## Variables de entorno (.env)

Presentes (valores ocultos):

- `ACCIO_API_KEY`, `ACCIO_ENGINE_PORT`, `ACCIO_ADMIN_PASSWORD`
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
- `LINKEDIN_*`, `META_*`, `GOOGLE_*`, `TIKTOK_*`

Opcional: `ACCIO_DEFAULT_TENANT=easytech` (cron/scripts)

**Ausentes (no scope de este servidor):**

- `EN1_API_URL`, `EN1_API_KEY`, `ECONVERSO_*`

---

## Documentación viva

| Archivo | Rol |
|---------|-----|
| `docs/PROJECT_STATE.md` | Fuente única de verdad del servidor |
| `docs/INVENTARIO_DESPLIEGUE.md` | Este inventario |
| `docs/CHANGELOG.md` | Historial de cambios |
| `docs/NEXT_STEPS.md` | Próximos pasos |
| `scripts/doctor.sh` | Diagnóstico rápido |

---

## Comandos para re-verificar

```bash
/opt/easytech_marketing/scripts/doctor.sh
curl -s http://127.0.0.1:8092/accio/health
systemctl status easytech-accio-engine --no-pager
/opt/easytech_marketing/scripts/accio_tick.sh
/opt/easytech_marketing/scripts/accio_cli.sh status
```

---

## Conclusión

ARROZCONPOLLO es el **servidor oficial de marketing EasyTech** con motor Accio/EMAcción desplegado y operativo. Pendientes: flyer IIUS, workflows n8n activos, tokens Meta/Google completos, integración EN1 (fuera de scope).

Ver: `docs/ACCIO_MARKETING_ENGINE.md`, `docs/CONTEXTO.md`, `docs/NEXT_STEPS.md`
