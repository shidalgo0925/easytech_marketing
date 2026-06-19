# Accio Marketing Engine — API

**Base URL (VPS):** `https://n8n.etsrv.site/accio/`  
**Local:** `http://127.0.0.1:8092/accio/`  
**Auth:** header `Authorization: Bearer <ACCIO_API_KEY>` (valor en `/opt/easytech_marketing/.env`)

---

## Dashboard web (Fase 1.5)

**URL:** https://n8n.etsrv.site/accio/dashboard/

Login con `ACCIO_API_KEY` (sessionStorage del navegador). Muestra:

- Cola posts pendientes
- Leads Odoo recientes
- Últimas órdenes Accio
- Botones: Pipeline · Publicar · Forzar post

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/accio/health` | Sin auth — ping |
| GET | `/accio/status` | Estado cola, CSV, órdenes |
| GET | `/accio/content/queue` | Lee `content_queue.json` |
| POST | `/accio/content/queue` | Agrega post(s) a cola LinkedIn |
| POST | `/accio/calendar` | Guarda calendario editorial |
| GET | `/accio/orders` | Lista órdenes Accio |
| POST | `/accio/orders` | Encola acción (`execute_now` opcional) |
| POST | `/accio/tick` | Ejecuta siguiente orden pendiente |
| POST | `/accio/run/pipeline` | Scraper + Odoo sync |
| POST | `/accio/run/publish-linkedin` | Publica siguiente post |

---

## Acciones (`POST /accio/orders`)

```json
{
  "action": "run_pipeline",
  "params": {},
  "execute_now": true,
  "source": "accio"
}
```

| action | params |
|--------|--------|
| `run_pipeline` | — |
| `publish_linkedin` | `force`, `dry_run` |
| `enqueue_post` | `post`: objeto post |
| `enqueue_posts` | `posts`: array |
| `set_calendar` | `calendar`: objeto |

---

## Agregar post LinkedIn

```json
POST /accio/content/queue
{
  "post": {
    "id": "linkedin_05_en1",
    "platform": "linkedin",
    "scheduled_at": "2026-07-03T13:00:00-05:00",
    "flyer": "flyers/05_en1_plataforma.png",
    "utm": "linkedin_post5",
    "text": "...",
    "first_comment": "https://n8n.etsrv.site/guia/"
  }
}
```

---

## Flujo Accio (operador autónomo)

```
Accio (estrategia)
    → POST /accio/content/queue  (genera calendario)
    → POST /accio/orders { action: run_pipeline }
    → cron /accio/tick cada 15 min (ejecuta órdenes)
    → POST /accio/run/publish-linkedin (o orden encolada)
```

---

## CLI en servidor

```bash
/opt/easytech_marketing/scripts/accio_cli.sh status
/opt/easytech_marketing/scripts/accio_cli.sh pipeline
/opt/easytech_marketing/scripts/accio_cli.sh publish
/opt/easytech_marketing/scripts/accio_cli.sh tick
```

---

## Servicio

```bash
systemctl status easytech-accio-engine
```

Logs órdenes: `Marketing/accio/orders.json`  
Estado: `Marketing/accio/state.json`
