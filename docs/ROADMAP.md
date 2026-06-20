# EasyMarketingOne — Roadmap

## Fase A — Seguridad (ahora)

- [x] Motor vivo en ArrozConPollo
- [x] Git init + .gitignore
- [x] deploy/systemd + crontab.example
- [x] docs/INSTALACION.md
- [x] Push a GitHub `shidalgo0925/easytech_marketing`
- [ ] Backup .env offline cifrado

## Fase B — Operación

- [x] Posts LinkedIn #5–#12 en cola
- [ ] Validar leads Odoo (origen guía vs scraper)
- [ ] Confirmar cron LinkedIn en logs
- [ ] Rotar secretos expuestos

## Fase C — Plataforma

- [x] Módulo campañas
- [x] Calendario editorial UI
- [x] Panel métricas (clicks, conversiones)
- [x] Biblioteca flyers en dashboard

## Fase D — Conectores

Estrategia: **estructura primero, APIs después** (`docs/ARQUITECTURA_CONECTORES.md`).

1. LinkedIn ✅ live
2. Facebook / Instagram — live (OAuth: https://n8n.etsrv.site/meta/)
3. Google Business — live (OAuth: https://n8n.etsrv.site/google/)
4. YouTube — OAuth compartido Google; publisher video pendiente
5. TikTok — OAuth: https://n8n.etsrv.site/tiktok/; publisher pendiente
6. Meta Ads, Google Ads — stub

Guía: `docs/CONECTAR_REDES.md`

Registro: `Marketing/accio/connectors.json`
