# Contexto — EM+Acción / EasyMarketingOne

Documento de referencia para operadores, agentes y desarrollo.  
**Actualizado:** 2026-06-20 · **Repo:** `github.com/shidalgo0925/easytech_marketing`

---

## Qué es

**EasyMarketingOne** es el motor de marketing autónomo de **EasyTech Services** (Panamá), desplegado en el VPS *ArrozConPollo* (`/opt/easytech_marketing`).

La **UI del dashboard** se llama **EM+Acción**:

- Logo: engranaje cobre girando + **EM** fijo + **+Acción** (Fraunces itálico)
- App Meta Developers: **EMAccion** (ID `944229778615599`)
- Page Facebook: **Easy Technology Services** (ID `1156663574198754`)

Internamente sigue usando rutas/API `accio/` y variable `ACCIO_API_KEY` (sin renombrar infra).

---

## Para qué sirve

| Función | Descripción |
|---------|-------------|
| **Dashboard EM+Acción** | KPIs, cola de posts, leads Odoo, campañas, calendario, métricas, flyers, conectores |
| **Orquestador** | API REST que ejecuta pipeline, publicaciones y órdenes |
| **Conectores** | LinkedIn ✅ · Facebook ✅ · Instagram ⏳ · Google/TikTok OAuth listo · Ads stub |
| **Automatización** | Cron LinkedIn/Meta; scraper domingos; leads → Odoo |

---

## URLs principales

| Recurso | URL |
|---------|-----|
| Dashboard EM+Acción | https://n8n.etsrv.site/accio/dashboard/ |
| API motor | https://n8n.etsrv.site/accio/ |
| Meta OAuth | https://n8n.etsrv.site/meta/ |
| Google OAuth | https://n8n.etsrv.site/google/ |
| TikTok OAuth | https://n8n.etsrv.site/tiktok/ |
| Política privacidad | https://n8n.etsrv.site/accio/privacidad/ |
| Icono app 1024 | https://n8n.etsrv.site/accio/dashboard/em-accion-app-icon-1024.png |
| Landing guía leads | https://n8n.etsrv.site/guia/ |
| Odoo CRM | https://easydb.etsrv.site |
| Meta Developers | https://developers.facebook.com/apps/944229778615599/ |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  EM+Acción Dashboard (navegador)                        │
│  accio-design.css · dashboard.html · privacidad.html    │
└────────────────────┬────────────────────────────────────┘
                     │ ACCIO_API_KEY
┌────────────────────▼────────────────────────────────────┐
│  Accio Engine :8092  (easytech-accio-engine)            │
│  app.py · dashboard_data · executor · queue_store       │
└──┬──────────┬──────────┬──────────┬────────────────────┘
   │          │          │          │
LinkedIn   Meta OAuth  Google OAuth  TikTok OAuth
:8091      :8093       :8094         :8095
   │          │          │
publishers  meta_publisher.py  connectors/publishers/
   │          │
content_queue.json · Marketing/flyers/ · Odoo CRM
```

**nginx** (`n8n.etsrv.site`) hace proxy a cada servicio.

---

## Servicios systemd (VPS)

| Servicio | Puerto | Rol |
|----------|--------|-----|
| `easytech-accio-engine` | 8092 | Dashboard + API |
| `easytech-meta-oauth` | 8093 | OAuth Facebook/IG |
| `easytech-linkedin-oauth` | 8091 | OAuth LinkedIn |
| `easytech-google-oauth` | 8094 | OAuth Google Business / YouTube |
| `easytech-tiktok-oauth` | 8095 | OAuth TikTok |
| `easytech-lead-api` | 8080 | Leads → Odoo |

Reiniciar `easytech-accio-engine` tras cambios en `.env`.

---

## Design system (UI)

**Paleta:** Verde bosque profundo + acento cobre  
Archivo: `Motor_Tecnico/accio_engine/static/accio-design.css`

| Token | Hex | Uso |
|-------|-----|-----|
| `--accio-bg-base` | `#10211A` | Fondo |
| `--accio-bg-surface` | `#19332A` | Cards |
| `--accio-accent` | `#C8843C` | Marca, CTA |
| `--accio-text-primary` | `#EFF4F1` | Texto + datos en tablas/KPIs |

**Logo EM+Acción:** HTML/CSS animado (`.em-gear-ring`, `.em-monogram`, `.em-wordmark`).  
**Fuentes:** Fraunces (display), Inter (UI), IBM Plex Mono (datos).

---

## Estrategia editorial de contenido

**Regla:** **3 posts de valor + 1 de venta/consejo** por cada bloque de 4.  
**Todos los posts llevan imagen** (flyer PNG en `Marketing/flyers/`).

| Tipo | Qué publicamos |
|------|----------------|
| `valor` | Educativo: errores comunes, checklists, insights de sector — sin pitch duro |
| `venta` | Demo, producto, CTA claro (DEMO / EN1 / DIAGNÓSTICO) |

Archivos:

- Cola: `Marketing/content_queue.json` (campo `content_type`)
- Calendario: `Marketing/accio/calendar.json`
- Campañas: `Marketing/accio/campaigns.json`
- Referencia rápida: `Marketing/CALENDARIO_PUBLICACION.md`
- Catálogo flyers: `Marketing/flyers/manifest.json`

### LinkedIn — estado cola

| Estado | Posts |
|--------|-------|
| **Publicados** | #1 FE+Odoo · #2 Diagnóstico · #3 Odoo ERP |
| **Pendientes** | #4–#11 (cadencia 3:1, jun–jul 2026) |

Próximo pendiente: `linkedin_04_fe_errores` (2026-06-30, valor, flyer #3).

### Otros canales pendientes

Facebook 4 · Instagram 4 · Google Business 1 · YouTube 1 · TikTok 1 — ver calendario.

**Flyer faltante:** #10 IIUS (`manifest.json` → `status: missing`).

---

## Conectores

Registro: `Marketing/accio/connectors.json` · Guía: `docs/CONECTAR_REDES.md`

| Canal | Modo | Estado operativo |
|-------|------|------------------|
| LinkedIn | live | Activo |
| Facebook Page | live | Activo (OAuth OK) |
| Instagram Business | live | Falta `META_IG_USER_ID` / scopes IG |
| Google Business | live | Falta OAuth + location ID |
| YouTube | stub | OAuth compartido Google |
| TikTok | stub | OAuth listo; publisher pendiente |
| Meta Ads / Google Ads | stub | Estructura |

---

## Meta / Facebook — estado

### Completado

- App **EMAccion** + permisos de prueba
- OAuth Facebook → Page **Activo** en dashboard
- Política privacidad publicada
- Icono 1024×1024 en static
- Scopes Instagram inválidos removidos de OAuth default

### Pendiente

- Meta Básica: subir icono + URL privacidad + categoría **Negocios**
- Verificación empresa Easy Technology Services (en revisión)
- App Review / publicar app en producción
- Conectar Instagram (caso de uso + scopes)
- Rotar **App Secret** (expuesto en chat histórico)

---

## Datos y archivos clave

```
/opt/easytech_marketing/
├── .env                          # Secretos (NO git)
├── .env.example                  # Plantilla variables
├── Motor_Tecnico/
│   ├── accio_engine/             # Dashboard + API
│   │   └── static/
│   │       ├── dashboard.html
│   │       ├── accio-design.css
│   │       ├── privacidad.html
│   │       └── em-accion-app-icon-1024.png
│   ├── meta_oauth.py · meta_publisher.py
│   ├── google_oauth.py · tiktok_oauth.py
│   └── connectors/               # Registry + publishers
├── Marketing/
│   ├── content_queue.json
│   ├── flyers/ + manifest.json
│   └── accio/                    # calendar, campaigns, connectors
├── docs/CONTEXTO.md              # Este archivo
└── deploy/systemd/
```

---

## Variables `.env` (referencia, sin valores)

Ver `.env.example`. Grupos principales:

- `ACCIO_API_KEY`, `ACCIO_ENGINE_PORT`
- `LINKEDIN_*`
- `META_APP_ID`, `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`, `META_OAUTH_PORT`
- `GOOGLE_CLIENT_*`, `GOOGLE_OAUTH_REFRESH_TOKEN`, `GOOGLE_BUSINESS_LOCATION_ID`
- `TIKTOK_CLIENT_*`, `TIKTOK_ACCESS_TOKEN`

---

## Operación diaria

1. **Dashboard** → KPIs, conectores, cola, publicar siguiente
2. **Odoo** → leads y pipeline comercial
3. **Operador humano** → DMs LinkedIn, cierre comercial
4. **Cron** → LinkedIn Mar/Jue/Vie 13:00 PA · Meta Mié/Vie · scraper domingos

Docs: `docs/OPERAR_SIN_CURSOR.md`, `docs/ACCIO_API.md`, `docs/ROADMAP.md`

---

## Publicar manualmente

```bash
# LinkedIn — dry-run
python3 Motor_Tecnico/linkedin_publisher.py --dry-run

# Facebook — dry-run
python3 Motor_Tecnico/meta_publisher.py --platform=facebook --dry-run --force
```

O desde dashboard → **Publicar siguiente** / **Publicar Meta**.

---

## Fases del proyecto (resumen)

| Fase | Estado |
|------|--------|
| A — Git, deploy, docs | ✅ En producción |
| B — Cola editorial, leads | 🔄 Cola reestructurada 3:1 |
| C — Campañas, calendario UI, métricas | ✅ |
| D — Conectores multicanal | 🔄 FB live; Google/TikTok OAuth; IG pendiente |

Detalle: `docs/ROADMAP.md`

---

## Contacto y CTA

- CTA principal: **DIAGNÓSTICO**
- Guía: https://n8n.etsrv.site/guia/
- WhatsApp: +507 6688-4938
- Email: easytechservices25@gmail.com / info@easytech.services
