# EasyMarketingOne — Roadmap

## Fase A — Seguridad (ahora)

- [x] Motor vivo en ArrozConPollo
- [x] Git init + .gitignore
- [x] deploy/systemd + crontab.example
- [x] docs/INSTALACION.md
- [ ] Push a GitHub `EasyMarketingOne`
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
2. Facebook / Instagram — live (OAuth pendiente)
3. Google Business, Meta Ads, Google Ads, YouTube, TikTok — stub (cola + dry-run)

Registro: `Marketing/accio/connectors.json`
