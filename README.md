# EasyMarketingOne

Motor de marketing autónomo de **EasyTech Services** — planifica, publica, captura leads y opera desde el VPS (ArrozConPollo).

Dashboard UI: **EM+Acción** · Repo: `github.com/shidalgo0925/easytech_marketing`

> Accio Work Desktop quedó sin créditos. **Este motor propio sigue vivo.**

## Contexto completo

Ver **[docs/CONTEXTO.md](docs/CONTEXTO.md)** — arquitectura, URLs, conectores, estrategia editorial 3:1, Meta, operación diaria.

## Estado actual (jun 2026)

| Componente | Estado |
|------------|--------|
| Accio Engine + EM+Acción dashboard | ✅ |
| LinkedIn auto | ✅ 3 posts publicados |
| Facebook Page (Meta OAuth) | ✅ conectado |
| Instagram / Google / TikTok | ⏳ OAuth o publisher pendiente |
| Cola editorial 3 valor + 1 venta | ✅ reestructurada |
| Odoo CRM + lead API | ✅ |
| Flyers | ✅ 11/12 (#10 IIUS falta) |

**Servidor:** `95.111.244.137` → `/opt/easytech_marketing`

## URLs

| Servicio | URL |
|----------|-----|
| Dashboard EM+Acción | https://n8n.etsrv.site/accio/dashboard/ |
| API | https://n8n.etsrv.site/accio/ |
| Meta OAuth | https://n8n.etsrv.site/meta/ |
| Privacidad | https://n8n.etsrv.site/accio/privacidad/ |
| Landing guía | https://n8n.etsrv.site/guia/ |
| Odoo CRM | https://easydb.etsrv.site |

## Instalación

Ver [docs/INSTALACION.md](docs/INSTALACION.md)

## Documentación

| Doc | Contenido |
|-----|-----------|
| [CONTEXTO.md](docs/CONTEXTO.md) | **Contexto técnico completo** |
| [ROADMAP.md](docs/ROADMAP.md) | Roadmap fases A–K |
| [EMACCION_ARCHITECTURE.md](docs/EMACCION_ARCHITECTURE.md) | Arquitectura objetivo |
| [EMACCION_GAP_ANALYSIS.md](docs/EMACCION_GAP_ANALYSIS.md) | Brecha hoy vs V1 comercial |
| [EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md](docs/EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md) | Fase E Knowledge Engine |
| [CONECTAR_REDES.md](docs/CONECTAR_REDES.md) | OAuth por canal |
| [ACCIO_API.md](docs/ACCIO_API.md) | API REST |
| [OPERAR_SIN_CURSOR.md](docs/OPERAR_SIN_CURSOR.md) | Operación diaria |
| [CALENDARIO_PUBLICACION.md](Marketing/CALENDARIO_PUBLICACION.md) | Cola editorial |
| [deploy/SECRETS.md](deploy/SECRETS.md) | Secretos (no Git) |

## Estructura

```
easytech_marketing/
├── Motor_Tecnico/       # accio_engine, OAuth, publishers, conectores
├── Marketing/           # content_queue, flyers, accio/
├── docs/                # CONTEXTO.md, ROADMAP, conectores…
├── deploy/              # systemd, cron
└── scripts/             # auto_publish
```

## Licencia

Privado — EasyTech Services © 2026
