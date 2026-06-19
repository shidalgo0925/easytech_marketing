# Integracion Odoo CRM - EasyTech Marketing

## Odoo (listo)
- URL: https://easydb.etsrv.site
- DB: Easydb
- Modulo: marketing_crm_integration
- Campos: x_url_web, x_sector
- Etapa: Nuevo - Marketing
- Fuentes UTM: scraper_panama, linkedin, guia_fe

## Servidor marketing (95.111.244.137)

```bash
cd /opt/easytech_marketing
cp secrets/api_key.env .env   # copiar desde maquina Odoo
chmod 600 .env
source venv/bin/activate
python3 Motor_Tecnico/odoo_sync.py
```

## Variables .env
```
ODOO_URL=https://easydb.etsrv.site
ODOO_DB=Easydb
ODOO_USER=shidalgo@easytech.services
ODOO_PASSWORD=<API_KEY>
```
