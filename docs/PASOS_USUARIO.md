# Motor Marketing EasyTech - Estado

## URLs activas
- n8n: https://n8n.etsrv.site
- Landing guia: https://n8n.etsrv.site/guia/
- Odoo CRM: https://easydb.etsrv.site

## Automatizacion
- Cron: domingos 6:00 AM (scraper + Odoo sync)
- Manual: `/opt/easytech_marketing/scripts/run_pipeline.sh`

## n8n (opcional)
Importar `docs/n8n-workflow-semanal.json` en n8n si prefieres cron visual.

## DNS pendiente (opcional)
Para `guia.etsrv.site` dedicado:
- Cloudflare: A `guia` -> 95.111.244.137 (proxy on)
- Luego: `sudo certbot certonly --webroot -w /var/www/html -d guia.etsrv.site`

## Rotar API key Odoo
La key se compartio en chat. Revocar en Odoo y actualizar `/opt/easytech_marketing/.env`.
