# EasyMarketingOne

Motor de marketing autónomo de **EasyTech Services** — planifica, publica, captura leads y opera desde el VPS (ArrozConPollo).

> Accio Work Desktop quedó sin créditos. **Este motor propio sigue vivo.**

## Estado actual (Fase A)

| Componente | Estado |
|------------|--------|
| Accio Engine API | ✅ `Motor_Tecnico/accio_engine/` |
| Dashboard web | ✅ `/accio/dashboard/` |
| LinkedIn auto | ✅ publisher + cron |
| Odoo CRM | ✅ lead API + sync |
| Scraper Panamá | ✅ cron domingo |
| Flyers | ✅ `Marketing/flyers/` |

**Servidor producción:** `95.111.244.137` → `/opt/easytech_marketing`

## URLs

| Servicio | URL |
|----------|-----|
| Dashboard | https://n8n.etsrv.site/accio/dashboard/ |
| API | https://n8n.etsrv.site/accio/ |
| Landing guía | https://n8n.etsrv.site/guia/ |
| Odoo CRM | https://easydb.etsrv.site |

## Instalación

Ver [docs/INSTALACION.md](docs/INSTALACION.md)

## Documentación

| Doc | Contenido |
|-----|-----------|
| [ACCIO_MARKETING_ENGINE.md](docs/ACCIO_MARKETING_ENGINE.md) | Plan maestro 4 fases |
| [ACCIO_API.md](docs/ACCIO_API.md) | API REST |
| [OPERAR_SIN_CURSOR.md](docs/OPERAR_SIN_CURSOR.md) | Operación diaria |
| [INVENTARIO_DESPLIEGUE.md](docs/INVENTARIO_DESPLIEGUE.md) | Auditoría VPS |
| [deploy/SECRETS.md](deploy/SECRETS.md) | Secretos (no Git) |

## Estructura

```
EasyMarketingOne/
├── Motor_Tecnico/       # scraper, Odoo, LinkedIn, accio_engine
├── Marketing/           # cola, flyers, accio/
├── docs/
├── deploy/              # systemd, cron, secretos
├── scripts/
└── docker-compose.yml   # n8n
```

## Roadmap

- **Fase A** — Git + backup + docs ✅ (en curso)
- **Fase B** — Posts #5–#12, validar leads
- **Fase C** — Campañas, calendario, métricas
- **Fase D** — Facebook, Instagram, Google, Meta Ads…

## Licencia

Privado — EasyTech Services © 2026
