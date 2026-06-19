# Inventario de despliegue — ArrozConPollo

**Servidor:** `95.111.244.137` (`vmi3119011`)  
**Proyecto:** `/opt/easytech_marketing`  
**Fecha auditoría:** 2026-06-19  
**Auditor:** Cursor (este chat), verificado en vivo con `systemctl`, `docker`, `curl`.

---

## Veredicto ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Está desplegado el **motor Accio** (producto conectado a EN1)? | **NO** — no hay binario, repo, contenedor ni servicio llamado Accio. |
| ¿Hay un motor de marketing/prospección funcionando? | **SÍ, parcial** — stack **Python custom** (no Accio): scraper, Odoo sync, landing, LinkedIn. |
| ¿Hay integración API con **EN1 / EasyNodeOne**? | **NO** — EN1 solo aparece en textos de marketing y flyers. |
| ¿Accio completó su propio paso 1 (apt, docker, carpeta)? | **SÍ** — y Cursor amplió con scripts, systemd, nginx, Odoo, LinkedIn. |

---

## Lo que Accio indicó vs lo que existe

Accio solo entregó comandos de **preparación del SO**:

```bash
apt-get update && upgrade
apt-get install git python3-pip python3-venv docker.io docker-compose
mkdir /opt/easytech_marketing
```

**No entregó:** `git clone`, imagen Docker del motor, `.env` del motor Accio, conexión EN1, Econverso, ni paso 2 de despliegue.

---

## Servicios corriendo AHORA (evidencia)

| Servicio | Tipo | Puerto | Estado | Comando verificación |
|----------|------|--------|--------|----------------------|
| `easytech-lead-api` | systemd | 127.0.0.1:8080 | **active** | `curl http://127.0.0.1:8080/health` → 200 |
| `easytech-linkedin-oauth` | systemd | 127.0.0.1:8091 | **active** | `curl http://127.0.0.1:8091/linkedin/` → 200 |
| `easytech_marketing-n8n-1` | Docker | 127.0.0.1:5678 | **Up** | `curl http://127.0.0.1:5678/` → 200 |
| nginx | sistema | 80, 443 | **active** | `https://n8n.etsrv.site/guia/` → 200 |

**Cron:** domingos 6:00 → `/opt/easytech_marketing/scripts/run_pipeline.sh`

---

## URLs públicas

| URL | Función | Backend |
|-----|---------|---------|
| https://n8n.etsrv.site | Panel n8n | Docker n8n |
| https://n8n.etsrv.site/guia/ | Landing captura leads | `/var/www/guia/index.html` |
| https://n8n.etsrv.site/guia/api/lead | POST lead → Odoo | `lead_api.py:8080` |
| https://n8n.etsrv.site/linkedin/ | OAuth LinkedIn | `linkedin_oauth.py:8091` |
| https://easydb.etsrv.site | CRM Odoo | Externo (Easydb) |

---

## Código instalado (Motor_Tecnico)

| Archivo | Origen | Función | EN1 |
|---------|--------|---------|-----|
| `scraper_panama.py` | Cursor (basado en concepto Accio) | Busca empresas → CSV | No |
| `odoo_sync.py` | Cursor | CSV → `crm.lead` Odoo | No |
| `lead_api.py` | Cursor | Formulario guía → Odoo | No |
| `linkedin_publisher.py` | Cursor | Publica cola LinkedIn | No |
| `linkedin_oauth.py` | Cursor | OAuth + publicar | No |

**No existe en el servidor:** `acciocms`, motor Accio PHP/Laravel, webhook EN1, Econverso WhatsApp bot, repo git del motor Accio.

---

## Datos / evidencia operativa

| Artefacto | Estado |
|-----------|--------|
| `leads_prospeccion.csv` | 37 filas (+ header) de scraper |
| Odoo auth | OK (`uid=2` en prueba 2026-06-19) |
| `Marketing/publish_log.json` | 3 posts LinkedIn publicados (IDs reales) |
| `Marketing/content_queue.json` | Post #4 pendiente (2026-06-30) |
| `Marketing/flyers/` | 12 flyers (#10 IIUS falta) |
| n8n workflows importados | **No confirmado** — JSON en `docs/` pero no hay evidencia de workflows activos |
| Pipeline cron ejecutado | **No** — carpeta `logs/` vacía (primer domingo aún no pasó o no corrió) |

### Posts LinkedIn publicados (API)

| ID cola | LinkedIn URN |
|---------|--------------|
| linkedin_01_fe_odoo | urn:li:share:7473608703850762240 |
| linkedin_02_diagnostico | urn:li:share:7473609231162654720 |
| linkedin_03_implementamos_odoo | urn:li:share:7473610329587908609 |

---

## Variables de entorno (.env)

Presentes (valores ocultos):

- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN`

**Ausentes (esperadas si Accio+EN1 existiera):**

- `EN1_API_URL`, `EN1_API_KEY`, `ECONVERSO_*`, `ACCIO_*`

---

## Qué falta para que sea el “motor Accio + EN1” original

1. **Definir qué es Accio técnicamente** — repo, imagen Docker, o SaaS (Accio no dejó artefacto en VPS).
2. **Integración EN1** — API/webhook para demos, membresías o seguimiento (no implementada).
3. **Econverso / WhatsApp** — secuencia automática (solo propuesta Accio, no código).
4. **n8n workflows activos** — importar y activar JSON de `docs/`.
5. **Cron pipeline** — verificar primera ejecución domingo 6:00.
6. **Guía PDF** — landing existe; PDF completo pendiente.

---

## Comandos para re-verificar

```bash
systemctl status easytech-lead-api easytech-linkedin-oauth
docker ps
curl -s http://127.0.0.1:8080/health
curl -s -o /dev/null -w '%{http_code}\n' https://n8n.etsrv.site/guia/
ls -la /opt/easytech_marketing/Motor_Tecnico/
wc -l /opt/easytech_marketing/leads_prospeccion.csv
grep -r EN1 /opt/easytech_marketing --include='*.py'   # debe dar vacío
find /opt -iname '*accio*'                             # debe dar vacío
```

---

## Conclusión (actualizada — visión Accio)

El servidor **no tiene aún el cerebro Accio** (`accio_engine`), pero **sí tiene la capa de ejecución** que Accio debe orquestar:

- Prospección: scraper → CSV → Odoo (cron)
- Inbound: landing + LinkedIn → Odoo
- **Pendiente:** orquestador Accio + sync EN1

Ver plan maestro: `docs/ACCIO_MARKETING_ENGINE.md`
